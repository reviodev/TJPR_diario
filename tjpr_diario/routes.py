from fastapi import APIRouter
from database import collection
from scraper import DJEDiarioScraper

router = APIRouter()

@router.get("/diarios")
def get_diarios():
    return list(collection.find({}, {"_id": 0}))

@router.get("/diarios/{data}")
def get_diario_por_data(data: str):
    return collection.find_one({"data_diario": data}, {"_id": 0})

@router.post("/scrap")
def executar_scraping():
    scraper = DJEDiarioScraper()
    scraper.run()
    return {"message": "Scraping concluído!"}
