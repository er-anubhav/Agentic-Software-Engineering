from fastapi import FastAPI
from service import URLShortenerService
from repository import URLRepository, UsageStatsRepository

app = FastAPI()

url_repository = URLRepository()
usage_stats_repository = UsageStatsRepository()

url_shortener_service = URLShortenerService(url_repository, usage_stats_repository)

@app.post('/shorten')
def create_short_url(request: CreateShortURLRequest):
    return url_shortener_service.create_short_url(request.longUrl)

@app.get('/{shortCode}')
def retrieve_long_url(shortCode: str):
    return url_shortener_service.retrieve_long_url(shortCode)