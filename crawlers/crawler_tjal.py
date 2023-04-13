import logging
import requests
from bs4 import BeautifulSoup as bs
from tenacity import (
    retry,
    wait_fixed,
    stop_after_attempt,
)
logger = logging.getLogger()

class CrawlerTjal:
    '''
    Robo que extrai dados do site TJAL(Tribunal de Justiça do Estado de Alagoas)
    
    Attributes:
        browser (str): This is where we store arg,
    '''

    def __init__(self):
        self.browser = None
        self.timeout = 1000
        self.urlconsulta = (
            "https://www2.tjal.jus.br/cpopg/show.do?processo.numero="
        )
        self.headers = None
   #@retry(wait=wait_fixed(1), stop=stop_after_attempt(5))
    def extract_processo_info_primeira_instancia(self, npu: str) -> str:
        '''
        '''

        session = requests.Session()
        data = session.get(f"{self.urlconsulta}{npu}", verify=False, timeout=self.timeout)
        pagina = bs(data.content, features="html.parser")
        classe = pagina.find("span", {"id": "classeProcesso"}).get_text(strip=True)
        area = pagina.find("div", {"id": "areaProcesso"}).get_text(strip=True)
        print (pagina)


if __name__ == '__main__':
    robo = CrawlerTjal()
    robo.extract_processo_info_primeira_instancia( "07108025520188020001")
