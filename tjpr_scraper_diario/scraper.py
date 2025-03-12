import os
import time
import datetime
import requests
import glob
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient

class DJEDiarioScraper:
    def __init__(self):
        self.download_dir = os.path.join(os.getcwd(), "Diarios")  # Alterado para "arquivos"
        self._setup_download_directory()
        self.driver = self._setup_driver()
        self.original_window = None
        self.wait = WebDriverWait(self.driver, 10)
        self.api_url = "http://127.0.0.1:8000"
        self.setup_mongodb()

    def setup_mongodb(self):
        """Configura conexão com MongoDB"""
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client["diarios_db"]
        self.collection = self.db["downloads"]

    def _setup_download_directory(self):
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

    def _setup_driver(self):
        chrome_options = Options()
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "directory_upgrade": True,
            "safebrowsing.enabled": False,
            "plugins.always_open_pdf_externally": True 
        })
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)
    
    def _close_privacy_banner(self):
        try:
            politica_privacidade = self.wait.until(
                EC.element_to_be_clickable((By.ID, 'politica-privacidade-tjpr'))
            )
            politica_privacidade.click()
        except TimeoutException:
            print("Banner de política de privacidade não encontrado ou não clicável.")

    def _click_search_box(self):
        try:
            search_box = self.wait.until(
                EC.element_to_be_clickable((By.ID, 'search_diario'))
            )
            search_box.click()
        except TimeoutException:
            print("Caixa de pesquisa não encontrada ou não clicável.")

    def _switch_to_new_window(self):
        # Aguardar nova janela abrir
        self.wait.until(lambda d: len(d.window_handles) > 1)
        
        # Mudar para a nova janela
        for window_handle in self.driver.window_handles:
            if window_handle != self.original_window:
                self.driver.switch_to.window(window_handle)
                break

    def _fill_search_form(self):
        try:
            # Preencher data inicial
            data_inicial = self.wait.until(
                EC.presence_of_element_located((By.ID, 'dataPublicacaoInicio'))
            )
            data_inicial.clear()
            data_inicial.send_keys(datetime.datetime.now().strftime("%d/%m/%Y"))

            # Preencher data final
            data_final = self.wait.until(
                EC.presence_of_element_located((By.ID, 'dataPublicacaoFinal'))
            )
            data_final.clear()
            data_final.send_keys(datetime.datetime.now().strftime("%d/%m/%Y"))
            
        except TimeoutException:
            print("Erro ao preencher o formulário de pesquisa.")
            
    def _search(self):
        try:
            pesquisa = self.wait.until(
                EC.element_to_be_clickable((By.ID, 'pesquisar'))
            )
            pesquisa.click()
        except TimeoutException:
            print("Botão de pesquisa não encontrado ou não clicável.")
            
    def _download_diario(self):
        try:
            download = self.wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'linkDownload'))
            )
            download.click()
            print("Download iniciado...")
        except TimeoutException:
            print("Link de download não encontrado ou não clicável.")
            
    def _check_download_complete(self, timeout=60):
        """Verifica se o download foi concluído"""
        print("⏳ Aguardando download concluir...")
        inicio = time.time()
        while time.time() - inicio < timeout:
            # Verificar se existe algum arquivo .part (download em andamento)
            part_files = glob.glob(os.path.join(self.download_dir, "*.part"))
            crdownload_files = glob.glob(os.path.join(self.download_dir, "*.crdownload"))
            
            if not part_files and not crdownload_files:
                # Obter o arquivo PDF mais recente na pasta
                pdf_files = glob.glob(os.path.join(self.download_dir, "*.pdf"))
                if pdf_files:
                    # Ordenar por data de modificação (mais recente primeiro)
                    pdf_files.sort(key=os.path.getmtime, reverse=True)
                    return pdf_files[0]
            
            time.sleep(1)
        
        return None  # Timeout - download não concluído

    def _get_file_info(self, filepath):
        """Obtém informações do arquivo baixado"""
        if not filepath or not os.path.exists(filepath):
            return None
        
        info = {
            "nome_arquivo": os.path.basename(filepath),
            "caminho_arquivo": filepath,
            "data_diario": datetime.datetime.now().strftime("%d/%m/%Y"),
            "data_download": datetime.datetime.now(),
            "status_leitura": False,
            "tamanho": os.path.getsize(filepath)
        }
        return info

    def _registrar_download_mongodb(self, file_info):
        """Registra o download diretamente no MongoDB"""
        try:
            resultado = self.collection.insert_one(file_info)
            print(f"✅ Download registrado no MongoDB: {file_info['nome_arquivo']}")
            return str(resultado.inserted_id)
        except Exception as e:
            print(f"❌ Erro ao salvar no MongoDB: {str(e)}")
            return None

    def _registrar_download_api(self, file_info):
        """Registra o download via API"""
        try:
            # Converter formato de data para o que a API espera (DD-MM-YYYY)
            # Substituir barras por hífens na data
            data_diario = file_info["data_diario"].replace("/", "-")
            
            # Criar payload no formato que a API espera
            payload = {
                "data_diario": data_diario,
                "tribunal": "TJPR",
                "cadernos": [
                    {
                        "caderno": file_info["nome_arquivo"],
                        "status_leitura": file_info["status_leitura"],
                        "caminho_arquivo": file_info["caminho_arquivo"]
                    }
                ]
            }
            
            response = requests.post(f"{self.api_url}/salvar/", json=payload)
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
            # Acessar o site
            self.driver.get("https://www.tjpr.jus.br/")
            time.sleep(5)
            
            # Salvar janela original
            self.original_window = self.driver.current_window_handle
            
            # Executar passos do scraping
            self._close_privacy_banner()
            self._click_search_box()
            self._switch_to_new_window()
            self._fill_search_form()
            self._search()     
            self._download_diario()
            
            # Aguardar tempo adicional para processamento
            time.sleep(5)
            
            # NOVO: Verificar conclusão do download e registrar
            downloaded_file = self._check_download_complete()
            
            if downloaded_file:
                print(f"✅ Download concluído: {downloaded_file}")
                # Obter informações do arquivo
                file_info = self._get_file_info(downloaded_file)
                
                # Registrar via MongoDB diretamente
                self._registrar_download_mongodb(file_info)
                
                # Tentar registrar via API também
                self._registrar_download_api(file_info)
            else:
                print("❌ Download não foi concluído")

        except Exception as e:
            print(f"Erro durante a execução: {str(e)}")
            self.close()

    def close(self):
        if self.driver:
            self.driver.quit()
        if hasattr(self, 'client'):
            self.client.close()

if __name__ == "__main__":
    scraper = DJEDiarioScraper()
    try:
        scraper.run()
    finally:
        scraper.close()