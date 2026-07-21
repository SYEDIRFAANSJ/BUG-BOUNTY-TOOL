import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from connectors.base import PlatformConnector
from connectors.rate_limiter import TokenBucketRateLimiter
from shared.config import settings

class HackerOneConnector(PlatformConnector):
    def __init__(self, rate_limiter: TokenBucketRateLimiter):
        super().__init__(rate_limiter)
        self.auth = (settings.H1_API_USERNAME, settings.H1_API_TOKEN)
        self.base_url = "https://api.hackerone.com/v1"

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=30))
    def fetch_all_programs(self) -> list[dict]:
        programs = []
        url = f"{self.base_url}/hackers/programs?page[size]=100"
        
        while url:
            self.rate_limiter.acquire()
            self.logger.info("Fetching HackerOne programs", url=url)
            response = httpx.get(url, auth=self.auth, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            programs.extend(data.get("data", []))
            
            links = data.get("links", {})
            url = links.get("next")
            
        return programs

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=30))
    def fetch_program_scope(self, external_id: str) -> list[dict]:
        self.rate_limiter.acquire()
        url = f"{self.base_url}/hackers/programs/{external_id}/structured_scopes"
        self.logger.info("Fetching HackerOne program scope", external_id=external_id)
        
        response = httpx.get(url, auth=self.auth, timeout=30.0)
        if response.status_code == 404:
            self.logger.warning("HackerOne program not found", external_id=external_id)
            return []
            
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
