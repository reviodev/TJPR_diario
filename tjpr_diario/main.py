from fastapi import FastAPI
from routes import router

app = FastAPI(title="DJE Scraper API", version="1.0")

app.include_router(router)

@app.get("/")
def home():
    return {"message": "API de Scraping de Diários!"}
