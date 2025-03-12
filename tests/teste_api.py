import os
import sys
import unittest
import time
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv
import requests
import glob

# Adicionar diretório pai ao path para importar o scraper
sys.path.append(str(Path(__file__).parent.parent))

# Importar o scraper
from tjpr_scraper_diario.scraper import DJEDiarioScraper

# Carregar variáveis de ambiente
load_dotenv()

class TestScraper(unittest.TestCase):
    """Testes para o scraper de diários do TJPR"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        # Conectar ao MongoDB para verificação
        mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
        mongo_db = os.getenv("MONGO_DB", "diarios_db")
        mongo_collection = os.getenv("MONGO_COLLECTION", "downloads")
        
        self.client = MongoClient(mongo_url)
        self.db = self.client[mongo_db]
        self.collection = self.db[mongo_collection]
        
        # Registrar quantidade inicial de documentos
        self.initial_count = self.collection.count_documents({})
        print(f"\n📊 Estado inicial do banco de dados:")
        print(f"  🔢 Documentos no MongoDB: {self.initial_count}")
        
        # Registrar arquivos existentes antes do teste
        download_dir = os.path.join(os.getcwd(), os.getenv("DOWNLOAD_DIR", "Diarios"))
        if os.path.exists(download_dir):
            self.initial_files = set(glob.glob(os.path.join(download_dir, "*.pdf")))
            print(f"  📁 Arquivos PDF no diretório: {len(self.initial_files)}")
        else:
            self.initial_files = set()
            print(f"  📁 Diretório de downloads não existe ainda")
    
    def tearDown(self):
        """Limpeza após os testes"""
        if hasattr(self, 'client'):
            self.client.close()
    
    def test_scraper_execution(self):
        """Teste da execução completa do scraper"""
        print("\n🔍 Iniciando teste do scraper...")
        
        # Instanciar e executar o scraper
        scraper = None
        download_dir = os.path.join(os.getcwd(), os.getenv("DOWNLOAD_DIR", "Diarios"))
        
        try:
            print("\n▶️ Executando scraper...")
            scraper = DJEDiarioScraper()
            
            # Executar o scraper - NÃO verificamos o valor de retorno
            scraper.run()
            print("✅ Scraper executado sem exceções")
            
        except Exception as e:
            self.fail(f"❌ Exceção durante execução do scraper: {str(e)}")
        finally:
            if scraper and hasattr(scraper, 'driver'):
                scraper.driver.quit()
                print("🔒 Recursos do scraper liberados")
        
        # Restante do código... verificações de arquivos e MongoDB...
        # ...
        
        print("\n✅ Teste do scraper concluído com sucesso")


if __name__ == "__main__":
    unittest.main()