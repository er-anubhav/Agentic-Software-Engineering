# URL Shortener Service
## Overview
This is a production-ready FastAPI project for creating and managing short URLs. It includes a microservices architecture with separate components for URL shortening, persistence, and analytics.
## Architecture
The system consists of the following components:
1. **URL Shortener Service**: Handles the creation and retrieval of short URLs, as well as redirection.
2. **Persistence Layer**: Stores mappings between short codes and long URLs.
3. **Analytics Service**: Tracks usage statistics for short URLs.
The communication between these components is facilitated via HTTP/REST APIs.
## API Endpoints
- **Create Short URL**: `POST /shorten`
  - Request Body: `{ "longUrl": "https://example.com" }`
  - Response: `{ "shortCode": "abc123" }`
- **Retrieve Long URL**: `GET /{shortCode}`
  - Response: `{ "longUrl": "https://example.com" }`
## Installation
To run this project, follow these steps:
1. Install the required dependencies:
   bash
   pip install -r requirements.txt
   
2. Create and apply database migrations (if using a different database):
   bash
   alembic upgrade head
   
3. Start the FastAPI server:
   bash
   uvicorn main:app --reload
   
## Usage
- To create a short URL, send a POST request to `/shorten` with the long URL in the request body.
- To retrieve the original long URL from a short code, access the endpoint `/shortCode` where `shortCode` is the generated short code.