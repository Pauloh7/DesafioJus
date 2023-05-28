import logging
import re
from datetime import datetime
import requests
from util import remove_blank_space, remove_special_characters
from bs4 import BeautifulSoup as bs
from tenacity import (
    retry,
    wait_fixed,
    stop_after_attempt,
)

logger = logging.getLogger()


class Crawler:
    """
    Robo que extrai dados do site TJAL(Tribunal de Justiça do Estado de Alagoas)

    Attributes:
        timeout (int): Padrao de timeout para tentativas de conexao
        urlconsutla (str): Url de consulta de processos de alagoas primeira instancia

    """

    def __init__(self):
        self.timeout = 1000
        self.urlconsulta_AL = "https://www2.tjal.jus.br/cpopg/show.do?processo.numero="
        self.urlconsulta_AL_segunda_instancia = "https://www2.tjal.jus.br/cposg5/search.do?conversationId=&paginaConsulta=0&cbPesquisa=NUMPROC&numeroDigitoAnoUnificado=&foroNumeroUnificado=&dePesquisaNuUnificado=&dePesquisaNuUnificado=UNIFICADO&dePesquisa={npu}&tipoNuProcesso=SAJ"

    def send_request(self, npu: str, tribunal: str) -> bs:
        session = requests.Session()
        if tribunal == "02":
            data = session.get(
            f"{self.urlconsulta}{npu}", verify=False, timeout=self.timeout
        )
        elif tribunal == "06":
            data = session.get(
            f"{self.urlconsulta}{npu}", verify=False, timeout=self.timeout
        )
        
        pagina = bs(data.content, features="html.parser")
        return pagina

    def extract_partes(self, pagina: bs) -> list[str, str, list]:
        """"""
        tipo_parte = "NAO_INFORMADO"
        nome_parte = "NAO_INFORMADO"
        if pagina.find("table", {"id": "tableTodasPartes"}):
            span_list = [
                tr.find_all("td")
                for tr in pagina.find("table", {"id": "tableTodasPartes"}).find_all(
                    "tr"
                )
            ]
        else:
            span_list = [
                tr.find_all("td")
                for tr in pagina.find(
                    "table", {"id": "tablePartesPrincipais"}
                ).find_all("tr")
            ]
        partes_list = []
        for td in span_list:
            lista_advogados = []
            if len(td) == 0:
                continue
            if len(td) == 2 and not "ADVOGAD" in remove_special_characters(td[0].text):
                tipo_parte = remove_special_characters(td[0].text)
                nome_parte = remove_special_characters(td[1].next)
                if len(td[1].find_all("span")) >= 1:
                    for advs in td[1].find_all("span"):
                        lista_advogados.append(
                            "Advogado(a): "
                            + remove_special_characters(advs.next_sibling)
                        )
            else:
                lista_advogados.append(
                    "Advogado(a): " + remove_special_characters(td[1].text)
                )

            partes_list.append([tipo_parte, nome_parte, lista_advogados])
        return partes_list

    def extract_movimentos(self, pagina: bs) -> list[str, str]:
        """"""
        movimentos = []
        movimentacao = pagina.find(
            "h2", string=re.compile(".*Movimentações.*", re.IGNORECASE)
        )
        if movimentacao:
            movimentacao = movimentacao.find_parent("div")
            if movimentacao:
                movimentacao = movimentacao.find_next_sibling("table")
                if (
                    remove_blank_space(movimentacao.text)
                    == "Não há Movimentações para este processo."
                ):
                    movimentacao = None
                    return movimentacao
                else:
                    try:
                        lista_movimentos = pagina.find(
                            "tbody", {"id": "tabelaTodasMovimentacoes"}
                        ).find_all("tr", {"class": "containerMovimentacao"})
                        for linha in lista_movimentos:
                            data = datetime.strptime(
                                remove_blank_space(
                                    linha.find(
                                        "td", attrs={"class": "dataMovimentacao"}
                                    ).text
                                ),
                                "%d/%m/%Y",
                            )
                            movimento = linha.find(
                                "td", {"class": "descricaoMovimentacao"}
                            )

                            if movimento.find("a"):
                                tipo_movimento = remove_special_characters(
                                    movimento.find("a").text
                                )
                            else:
                                tipo_movimento = remove_special_characters(
                                    movimento.next
                                )
                            texto_movimento = remove_special_characters(
                                linha.find("span").text
                            )
                            if texto_movimento:
                                movimento_completo = (
                                    tipo_movimento + " " + texto_movimento
                                )
                            else:
                                movimento_completo = tipo_movimento
                            movimentos.append([data, movimento_completo])
                    except Exception as exc:
                        logger.exception(exc)
                        movimentos = None
                        raise

        return movimentos

    @retry(wait=wait_fixed(1), stop=stop_after_attempt(5))
    def extract_processo_info(self, npu: str, tribunal: str) -> dict:
        """ """
        pagina = self.send_request(npu, tribunal)
        try:
            classe = pagina.find("span", {"id": "classeProcesso"}).get_text(strip=True)
            area = pagina.find("div", {"id": "areaProcesso"}).get_text(strip=True)
            assunto = pagina.find("span", {"id": "assuntoProcesso"}).get_text(
                strip=True
            )
            data_distribuicao = pagina.find(
                "div", {"id": "dataHoraDistribuicaoProcesso"}
            ).get_text(strip=True)
            juiz = pagina.find("span", {"id": "juizProcesso"}).get_text(strip=True)
            valor_da_acao = (
                pagina.find("div", {"id": "valorAcaoProcesso"})
                .get_text(strip=True)
                .replace(" ", "")
            )
            partes_list = self.extract_partes(pagina)
            movimentos = self.extract_movimentos(pagina)

            return {
                "classe": classe if classe else "",
                "area": area if area else "",
                "assunto": assunto if assunto else "",
                "data_distribuicao": data_distribuicao if data_distribuicao else "",
                "juiz": juiz if juiz else "",
                "valor_da_acao": valor_da_acao if valor_da_acao else "",
                "partes": partes_list,
                "movimentos": movimentos,
            }
        except Exception as exc:
            logger.exception(exc)
            raise


if __name__ == "__main__":
    robo = CrawlerTjal()
    # 07108025520188020001
    # 07114332320238020001
    robo.extract_processo_info("07108025520188020001")
