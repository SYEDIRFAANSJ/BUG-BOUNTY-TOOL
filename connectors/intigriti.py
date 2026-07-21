import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from connectors.base import PlatformConnector
from connectors.rate_limiter import TokenBucketRateLimiter
from shared.config import settings

class IntigritiConnector(PlatformConnector):
    def __init__(self, rate_limiter: TokenBucketRateLimiter):
        super().__init__(rate_limiter)
        self.headers = {
            "Authorization": f"Bearer {settings.INTIGRITI_PAT}"
        }
        self.base_url = "https://api.intigriti.com/external/researcher"

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=30))
    def fetch_all_programs(self) -> list[dict]:
        # Note: Intigriti researcher API shape may change as it was in beta.
        programs = []
        offset = 0
        limit = 100
        
        while True:
            self.rate_limiter.acquire()
            url = f"{self.base_url}/v1/programs?offset={offset}&limit={limit}"
            self.logger.info("Fetching Intigriti programs", url=url)
            
            response = httpx.get(url, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            batch = data.get("records", [])
            if not batch:
                break
                
            programs.extend(batch)
            offset += limit
            
        return programs

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=30))
    def fetch_program_scope(self, external_id: str) -> list[dict]:
        self.rate_limiter.acquire()
        url = f"{self.base_url}/v1/programs/{external_id}"
        self.logger.info("Fetching Intigriti program scope", external_id=external_id)
        
        response = httpx.get(url, headers=self.headers, timeout=30.0)
        if response.status_code == 404:
            self.logger.warning("Intigriti program not found", external_id=external_id)
            return []
            
        response.raise_for_status()
        data = response.json()
        
        # Domains/scope are often included in the program detail for Intigriti
        return data.get("domains", [])
