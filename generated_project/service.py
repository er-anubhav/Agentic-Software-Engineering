from repository import URLRepository, UsageStatsRepository

class URLShortenerService:
    def __init__(self, url_repository: URLRepository, usage_stats_repository: UsageStatsRepository):
        self.url_repository = url_repository
        self.usage_stats_repository = usage_stats_repository

    def create_short_url(self, long_url: str) -> dict:
        short_code = self.generate_unique_short_code()
        self.url_repository.save(short_code, long_url)
        self.usage_stats_repository.initialize(short_code)
        return {'shortCode': short_code}

    def retrieve_long_url(self, short_code: str) -> dict:
        long_url = self.url_repository.get(long_url)
        if long_url is None:
            raise HTTPException(status_code=404, detail='Short code not found')
        self.usage_stats_repository.increment(short_code)
        return {'longUrl': long_url}

    def generate_unique_short_code(self) -> str:
        # Implement logic to generate a unique short code
        pass