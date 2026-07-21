import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from connectors.base import PlatformConnector
from connectors.rate_limiter import TokenBucketRateLimiter
from shared.config import settings

class BugcrowdConnector(PlatformConnector):
    def __init__(self, rate_limiter: TokenBucketRateLimiter):
        super().__init__(rate_limiter)
        self.headers = {
            "Authorization": f"Token {settings.BUGCROWD_API_TOKEN}",
            "Accept": "application/vnd.bugcrowd+json"
        }
        self.base_url = "https://api.bugcrowd.com"

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=30))
    def fetch_all_programs(self) -> list[dict]:
        programs = []
        offset = 0
        limit = 100
        
        while True:
            self.rate_limiter.acquire()
            url = f"{self.base_url}/programs?page[limit]={limit}&page[offset]={offset}"
            self.logger.info("Fetching Bugcrowd programs", url=url)
            
            response = httpx.get(url, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            batch = data.get("data", [])
            if not batch:
                break
                
            programs.extend(batch)
            offset += limit
            
        return programs

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=30))
    def fetch_program_scope(self, external_id: str) -> list[dict]:
        self.rate_limiter.acquire()
        url = f"{self.base_url}/programs/{external_id}?include=current_brief.target_groups.targets"
        self.logger.info("Fetching Bugcrowd program scope", external_id=external_id)
        
        response = httpx.get(url, headers=self.headers, timeout=30.0)
        if response.status_code == 404:
            self.logger.warning("Bugcrowd program not found", external_id=external_id)
            return []
            
        response.raise_for_status()
        
        data = response.json()
        included = data.get("included", [])
        
        # Bugcrowd's JSON API requires mapping included relations
        return {"data": data.get("data", {}), "included": included}
