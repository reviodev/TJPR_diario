from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os

async def test_connection():
   
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    
  
    try:
        server_info = await client.server_info()
        print("Conexão com MongoDB bem-sucedida!")
        print(f"Versão: {server_info['version']}")
        
     
        dbs = await client.list_database_names()
        print(f"Bancos de dados: {dbs}")
        
        return client
    except Exception as e:
        print(f"Erro ao conectar com MongoDB: {e}")
        return None

async def test_scraper_data(client):
    """Verifica os dados do scraper no MongoDB"""
    if not client:
        print("❌ Cliente MongoDB não disponível")
        return
    
    
    db = client.diarios_db
    
    print("\n🔍 Verificando dados do scraper no MongoDB...\n")

    collections = await db.list_collection_names()
    print(f"Coleções disponíveis: {collections}")
    
    if not collections:
        print("❌ Nenhuma coleção encontrada")
        return
    
   
    for coll_name in collections:
        collection = db[coll_name]
        count = await collection.count_documents({})
        print(f"\nColeção '{coll_name}': {count} documentos")
        
        if count > 0:
         
            cursor = collection.find().sort("data_download", -1).limit(1)
            doc = await cursor.to_list(length=1)
            
            if doc:
                latest = doc[0]
                print("\n📄 Documento mais recente:")
                print(f"  ID: {latest['_id']}")
                
               
                expected_fields = ['nome_arquivo', 'caminho_arquivo', 'data_diario', 'data_download', 'status_leitura']
                for field in expected_fields:
                    value = latest.get(field, "❌ Não encontrado")
                    print(f"  {field}: {value}")
                
               
                caminho = latest.get('caminho_arquivo')
                if caminho and os.path.exists(caminho):
                    size_mb = os.path.getsize(caminho) / (1024 * 1024)
                    print(f"  ✅ Arquivo encontrado: {size_mb:.2f} MB")
                elif caminho:
                    print(f"  ❌ Arquivo não encontrado: {caminho}")
                else:
                    print("  ❓ Caminho do arquivo não especificado")

if __name__ == "__main__":
    async def run_tests():
        client = await test_connection()
        if client:
            await test_scraper_data(client)
            
    asyncio.run(run_tests())