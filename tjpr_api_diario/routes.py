from fastapi import APIRouter, HTTPException, BackgroundTasks
from bson import ObjectId
import json
import sys
import os
from pathlib import Path

# Adicionar o diretório do scraper ao path para importação
scraper_dir = Path(__file__).parent.parent.parent / "tjpr_scraper_diario"
sys.path.append(str(scraper_dir))

# Importar o scraper e a conexão com o banco de dados
from scraper import DJEDiarioScraper
from database import collection  # Importar a collection do módulo de database

router = APIRouter()

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

@router.get("/diarios")
def get_diarios():
    """Retorna todos os diários cadastrados"""
    diarios = list(collection.find())
    # Converter para JSON compatível
    return json.loads(JSONEncoder().encode(diarios))

@router.get("/diarios/{data}")
def get_diario_por_data(data: str):
    """Busca diários por data específica"""
    diario = collection.find_one({"data_diario": data})
    if not diario:
        raise HTTPException(status_code=404, detail=f"Nenhum diário encontrado para a data {data}")
    return json.loads(JSONEncoder().encode(diario))

@router.post("/scrap")
def executar_scraping(background_tasks: BackgroundTasks):
    """Executa o scraper do TJPR para baixar diários"""
    try:
        # Executar em background para não bloquear a API
        background_tasks.add_task(run_scraper_background)
        return {"message": "Scraping iniciado em segundo plano!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar scraping: {str(e)}")

def run_scraper_background():
    """Função para executar o scraper em segundo plano"""
    scraper = DJEDiarioScraper()
    try:
        scraper.run()
    finally:
        if hasattr(scraper, 'driver'):
            scraper.driver.quit()