from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI()

# In-memory storage for URL mappings and usage statistics
url_mappings = {}
usage_stats = {}

class CreateShortURLRequest(BaseModel):
    longUrl: str

@app.post('/shorten')
def create_short_url(request: CreateShortURLRequest):
    short_code = str(uuid.uuid4())[:8]
    url_mappings[short_code] = request.longUrl
    usage_stats[short_code] = 0
    return {'shortCode': short_code}

@app.get('/{shortCode}')
def retrieve_long_url(shortCode: str):
    if shortCode in url_mappings:
        usage_stats[shortCode] += 1
        return {'longUrl': url_mappings[shortCode]}
    else:
        raise HTTPException(status_code=404, detail='Short code not found')