import os
import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from database import collection  

class DJEDiarioScraper:
    def __init__(self):
        self.download_dir = os.path.join(os.getcwd(), "arquivos")
        self._setup_download_directory()
        self.driver = self._setup_driver()
        self.wait = WebDriverWait(self.driver, 10)

    def _setup_download_directory(self):
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

    def _setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True 
        })
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

    def _close_privacy_banner(self):
        try:
            banner = self.wait.until(
                EC.element_to_be_clickable((By.ID, 'politica-privacidade-tjpr'))
            )
            banner.click()
        except TimeoutException:
            print("ℹ️ Nenhum banner encontrado.")

    def _fill_search_form(self):
        try:
            data_hoje = datetime.datetime.now().strftime("%d/%m/%Y")
            data_inicial = self.wait.until(EC.presence_of_element_located((By.ID, 'dataPublicacaoInicio')))
            data_final = self.wait.until(EC.presence_of_element_located((By.ID, 'dataPublicacaoFinal')))
            data_inicial.clear()
            data_inicial.send_keys(data_hoje)
            data_final.clear()
            data_final.send_keys(data_hoje)
            return True
        except TimeoutException:
            return False

    def _search(self):
        try:
            pesquisa = self.wait.until(EC.element_to_be_clickable((By.ID, 'pesquisar')))
            pesquisa.click()
            return True
        except TimeoutException:
            return False

    def _download_diario(self):
        try:
            download = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'linkDownload')))
            download.click()
            return True
        except TimeoutException:
            return False

    def _save_to_mongo(self, caminho_arquivo):
        registro = {
            "data_diario": datetime.datetime.now().strftime('%d-%m-%Y'),
            "caminho_arquivo": caminho_arquivo,
            "status_leitura": False
        }
        collection.insert_one(registro)
        print(f"✅ Diário registrado no MongoDB: {registro}")

    def run(self):
        self.driver.get("https://www.tjpr.jus.br/")
        time.sleep(5)

        self._close_privacy_banner()
        if self._fill_search_form() and self._search():
            if self._download_diario():
                caminho_arquivo = os.path.join(self.download_dir, "diario.pdf")
                time.sleep(5)  
                if os.path.exists(caminho_arquivo):
                    self._save_to_mongo(caminho_arquivo)
                else:
                    print("❌ O arquivo não foi encontrado.")
        self.driver.quit()

if __name__ == "__main__":
    scraper = DJEDiarioScraper()
    scraper.run()
