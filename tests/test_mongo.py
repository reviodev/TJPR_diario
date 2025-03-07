from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def test_connection():
    # Conecte ao MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    
    # Obtenha informações do servidor
    try:
        server_info = await client.server_info()
        print("Conexão com MongoDB bem-sucedida!")
        print(f"Versão: {server_info['version']}")
        
        # Listar bancos de dados
        dbs = await client.list_database_names()
        print(f"Bancos de dados: {dbs}")
        
        return True
    except Exception as e:
        print(f"Erro ao conectar com MongoDB: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())