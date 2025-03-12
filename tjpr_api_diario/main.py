from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
import os
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

app = FastAPI(
    title="API Diários TJPR",
    description="API para gerenciamento de diários oficiais do TJPR",
    version="1.0.0"
)

# Configuração do MongoDB via variáveis de ambiente
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB", "diarios_db")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "downloads")

try:
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    print(f"✅ Conexão com MongoDB estabelecida: {MONGO_URL}")
except Exception as e:
    print(f"❌ Erro ao conectar ao MongoDB: {str(e)}")
    # Aqui você poderia implementar um fallback

# Modelo de dados
class Caderno(BaseModel):
    caderno: str
    status_leitura: bool
    caminho_arquivo: str

class DownloadData(BaseModel):
    data_diario: str  # Formato "11-03-2025"
    tribunal: str = "TJPR"
    cadernos: List[Caderno]

# Rota para salvar dados
@app.post("/salvar/")
async def salvar_dados(dados: DownloadData):
    try:
        # Converter os dados para um formato adequado para o MongoDB
        documento = dados.dict()
        resultado = collection.insert_one(documento)
        return {"mensagem": "Dados salvos", "id": str(resultado.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar dados: {str(e)}")

# Rota para recuperar todos os dados
@app.get("/downloads/")
async def listar_downloads():
    try:
        dados = list(collection.find({}, {"_id": 0}))  # Ocultando o _id
        return {"downloads": dados}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar downloads: {str(e)}")