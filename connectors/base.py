from abc import ABC, abstractmethod
from shared.logging import get_logger
from connectors.rate_limiter import TokenBucketRateLimiter

class PlatformConnector(ABC):
    def __init__(self, rate_limiter: TokenBucketRateLimiter):
        self.rate_limiter = rate_limiter
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def fetch_all_programs(self) -> list[dict]: ...
    
    @abstractmethod  
    def fetch_program_scope(self, external_id: str) -> list[dict]: ...
