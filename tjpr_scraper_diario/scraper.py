import os
import time
import datetime
import requests
import glob
import sys
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class DJEDiarioScraper:
    
    def __init__(self):
        self.download_dir = os.path.join(os.getcwd(), os.getenv("DOWNLOAD_DIR", "Diarios"))
        self._setup_download_directory()
        self.driver = self._setup_driver()
        self.wait = WebDriverWait(self.driver, int(os.getenv("WAIT_TIMEOUT", "10")))
        self.api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
        self.usar_dia_anterior = os.getenv("DIA_ANTERIOR", "false").lower() == "true"
        self.setup_mongodb()

    def setup_mongodb(self):
        try:
            mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
            mongo_db = os.getenv("MONGO_DB", "diarios_db")
            mongo_collection = os.getenv("MONGO_COLLECTION", "downloads")
            
            self.client = MongoClient(mongo_url)
            self.db = self.client[mongo_db]
            self.collection = self.db[mongo_collection]
            print(f"✅ Conexão com MongoDB estabelecida: {mongo_url}")
        except Exception as e:
            print(f"❌ Erro ao conectar ao MongoDB: {str(e)}")

    def _setup_download_directory(self):
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            print(f"📁 Diretório de downloads criado: {self.download_dir}")
        else:
            print(f"📁 Usando diretório de downloads: {self.download_dir}")

    def _setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--disable-application-cache")
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "directory_upgrade": True,
            "safebrowsing.enabled": False,
            "plugins.always_open_pdf_externally": True,
            "browser.download.manager.showWhenStarting": False,
            "browser.helperApps.neverAsk.saveToDisk": "application/pdf,application/octet-stream"
        })
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)
    
    def _get_data_busca(self):
        if self.usar_dia_anterior:
            data = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%d/%m/%Y")
            print(f"🗓️ Usando data do dia anterior: {data}")
        else:
            data = datetime.datetime.now().strftime("%d/%m/%Y")
            print(f"🗓️ Usando data atual: {data}")
        return data
    
    def _fill_search_form(self):
        try:
            data_busca = self._get_data_busca()
            
            try:
                data_campo = self.wait.until(
                    EC.presence_of_element_located((By.ID, 'dataVeiculacao'))
                )
                data_campo.clear()
                data_campo.send_keys(data_busca)
                print(f"✅ Campo de data preenchido: {data_busca}")
                return True
            except TimeoutException:
               
                campos_texto = self.driver.find_elements(By.XPATH, "//input[@type='text']")
                if campos_texto:
                    campo_data = campos_texto[1] if len(campos_texto) > 1 else campos_texto[0]
                    campo_data.clear()
                    campo_data.send_keys(data_busca)
                    print(f"✅ Campo de texto alternativo preenchido: {data_busca}")
                    return True
                else:
                    print("⚠️ Nenhum campo de texto encontrado para preencher a data")
                    raise Exception("Campo de data não encontrado")
                
        except Exception as e:
            print(f"❌ Erro ao preencher o formulário: {str(e)}")
            return False
            
    def _search(self):
        try:
         
            try:
                pesquisa = self.wait.until(
                    EC.element_to_be_clickable((By.ID, 'searchButton'))
                )
                pesquisa.click()
                print("✅ Botão de pesquisa clicado")
                return True
            except TimeoutException:
                # Fallback para outros tipos de botões
                try:
                    pesquisa = self.driver.find_element(By.XPATH, 
                        "//input[@type='submit'] | //button[contains(text(), 'Pesquisar')]")
                    pesquisa.click()
                    print("✅ Botão de pesquisa alternativo clicado")
                    return True
                except:
                    print("⚠️ Botão de pesquisa não encontrado")
                    return False
        except Exception as e:
            print(f"❌ Erro ao clicar no botão de pesquisa: {str(e)}")
            return False
            
    def _download_diario(self):
        try:
            time.sleep(3)
            print("🔍 Analisando página de resultados...")
            
        
            try:
                baixar_link = self.driver.find_element(By.XPATH, "//a[@class='link' and text()='Baixar']")
                print("🎯 Link 'Baixar' encontrado")
                baixar_link.click()
                print("✅ Download iniciado via link 'Baixar'")
                return True
            except Exception as e:
                print("⚠️ Link 'Baixar' não encontrado, tentando alternativa")
     
            try:
                download = self.driver.find_element(By.XPATH, 
                    "//a[contains(text(), 'Baixar') or contains(text(), 'Download') or contains(@title, 'Baixar')]")
                download.click()
                print("✅ Download iniciado via link alternativo")
                return True
            except:
                print("⚠️ Nenhum link de download encontrado")
                return False
            
        except Exception as e:
            print(f"❌ Erro ao tentar download: {str(e)}")
            return False
            
    def _check_download_complete(self, timeout=60):
        print(f"⏳ Aguardando download concluir (timeout: {timeout}s)...")
        inicio = time.time()
        
        while time.time() - inicio < timeout:
            # Verificar arquivos temporários
            part_files = glob.glob(os.path.join(self.download_dir, "*.part"))
            crdownload_files = glob.glob(os.path.join(self.download_dir, "*.crdownload"))
            
            if not part_files and not crdownload_files:
                # Verificar apenas arquivos PDF
                pdf_files = glob.glob(os.path.join(self.download_dir, "*.pdf"))
                if pdf_files:
                    # Ordenar por data de modificação (mais recente primeiro)
                    pdf_files.sort(key=os.path.getmtime, reverse=True)
                    return pdf_files[0]
            
            time.sleep(1)
        
        print("❌ Timeout - download não foi concluído")
        return None

    def _get_file_info(self, filepath):
        if not filepath or not os.path.exists(filepath):
            print(f"❌ Arquivo não encontrado: {filepath}")
            return None
        
        data_busca = self._get_data_busca()
        
        info = {
            "nome_arquivo": os.path.basename(filepath),
            "caminho_arquivo": filepath,
            "data_diario": data_busca,
            "data_download": datetime.datetime.now(),
            "status_leitura": False,
            "tamanho": os.path.getsize(filepath)
        }
        return info

    def _registrar_download_mongodb(self, file_info):
        try:
            resultado = self.collection.insert_one(file_info)
            print(f"✅ Download registrado no MongoDB: {file_info['nome_arquivo']}")
            return str(resultado.inserted_id)
        except Exception as e:
            print(f"❌ Erro ao salvar no MongoDB: {str(e)}")
            return None

    def _registrar_download_api(self, file_info):
        try:
            data_diario = file_info["data_diario"].replace("/", "-")
            
            payload = {
                "data_diario": data_diario,
                "tribunal": os.getenv("TRIBUNAL", "TJPR"),
                "cadernos": [
                    {
                        "caderno": file_info["nome_arquivo"],
                        "status_leitura": file_info["status_leitura"],
                        "caminho_arquivo": file_info["caminho_arquivo"]
                    }
                ]
            }
            
            endpoint = os.getenv("API_ENDPOINT", "salvar")
            url = f"{self.api_url}/{endpoint}/"
            
            print(f"📤 Enviando dados para API: {url}")
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                print(f"✅ Download registrado via API: {file_info['nome_arquivo']}")
                return response.json()
            else:
                print(f"❌ Erro ao registrar via API: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Erro na comunicação com API: {str(e)}")
            return None

    def run(self):
        try:
            print(f"🔄 Iniciando scraper de diários TJPR...")
            
            site_url = "https://portal.tjpr.jus.br/e-dj/publico/diario/pesquisar/filtro.do"
            self.driver.get(site_url)
            print(f"🌐 Acessando página de pesquisa: {site_url}")
            time.sleep(5)
            
            if not self._fill_search_form():
                print("❌ Falha ao preencher formulário de pesquisa")
                return False
            
            if not self._search():
                print("❌ Falha ao executar pesquisa")
                return False
            
            time.sleep(5)
            
            if not self._download_diario():
                print("❌ Não foi possível iniciar o download")
                return False
            
            downloaded_file = self._check_download_complete(int(os.getenv("DOWNLOAD_TIMEOUT", "60")))
            
            if downloaded_file:
                print(f"✅ Download concluído: {downloaded_file}")
                file_info = self._get_file_info(downloaded_file)
                self._registrar_download_mongodb(file_info)
                self._registrar_download_api(file_info)
                return True
            else:
                print("❌ Download não foi concluído")
                return False

        except Exception as e:
            print(f"❌ Erro durante a execução: {str(e)}")
            traceback.print_exc()
            return False

    def close(self):
        if hasattr(self, 'driver'):
            self.driver.quit()
            print("🔒 Driver do navegador fechado")
        if hasattr(self, 'client'):
            self.client.close()
            print("🔒 Conexão com MongoDB fechada")
        print("👋 Scraper finalizado")

if __name__ == "__main__":
    scraper = DJEDiarioScraper()
    try:
        resultado = scraper.run()
        if resultado:
            print("✅ Scraper concluído com sucesso!")
            sys.exit(0)
        else:
            print("❌ Scraper falhou na execução!")
            sys.exit(1)
    finally:
        scraper.close()