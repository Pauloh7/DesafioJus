import logging
import re
from datetime import datetime
import requests

from util import remove_blank_space, remove_special_characters, extract_tribunal
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
        self.urlconsulta_AL_primeiro_grau = "https://www2.tjal.jus.br/cpopg/show.do?processo.numero="
        self.urlconsulta_AL_segundo_grau_1 = "https://www2.tjal.jus.br/cposg5/search.do?conversationId=&paginaConsulta=0&cbPesquisa=NUMPROC&numeroDigitoAnoUnificado=&foroNumeroUnificado=&dePesquisaNuUnificado=&dePesquisaNuUnificado=UNIFICADO&dePesquisa="
        self.urlconsulta_AL_segundo_grau_2 = "https://www2.tjal.jus.br/cposg5/show.do?processo.codigo="
        self.urlconsulta_CE_primeiro_grau = "https://esaj.tjce.jus.br/cpopg/show.do?processo.codigo=01Z081I9T0000&processo.foro=1&processo.numero="
        self.urlconsulta_CE_segundo_grau_1 ="https://esaj.tjce.jus.br/cposg5/search.do;jsessionid=0430EE14DC7E5B016D9DD345C461DD55.cposg3?conversationId=&paginaConsulta=0&cbPesquisa=NUMPROC&numeroDigitoAnoUnificado=&foroNumeroUnificado=&dePesquisaNuUnificado=&dePesquisaNuUnificado=UNIFICADO&dePesquisa="
        self.urlconsulta_CE_segundo_grau_2 = "https://esaj.tjce.jus.br/cposg5/show.do?processo.codigo="

    def get_codigo_segunda_instancia(self, pagina_segundo_grau: bs) -> str:
        codigo_processo = pagina_segundo_grau.find(
            "input", id="processoSelecionado"
        ).get("value")

        return codigo_processo

    @retry(wait=wait_fixed(1), stop=stop_after_attempt(5))
    def send_request_primeiro_grau(self, npu: str, tribunal: str) -> bs:
        session = requests.Session()
        if tribunal == "02":
            grau = 1
            pagina_primeiro_grau = session.get(
                f"{self.urlconsulta_AL_primeiro_grau}{npu}", verify=False, timeout=self.timeout
            )
            soup_pagina_primeiro_grau = bs(
                pagina_primeiro_grau.content, features="html.parser"
            )

            if soup_pagina_primeiro_grau("td", id="mensagemRetorno"):
                soup_pagina_primeiro_grau = None

            primeiro_grau_processo_info = self.extract_processo_info(
                soup_pagina_primeiro_grau, npu, grau
            )

        # elif tribunal == "06":
        #     data = session.get(
        #     f"{self.urlconsulta}{npu}", verify=False, timeout=self.timeout
        # )

        return primeiro_grau_processo_info

    @retry(wait=wait_fixed(1), stop=stop_after_attempt(5))
    def send_request_segundo_grau(self, npu: str, tribunal: str) -> bs:
        grau = "2"
        session = requests.Session()
        if tribunal == "02":
            pagina_segundo_grau = session.get(
                f"{self.urlconsulta_AL_segundo_grau_1}{npu}",
                verify=False,
                timeout=self.timeout,
            )
            soup_pagina_segundo_grau = bs(
                pagina_segundo_grau.content, features="html.parser"
            )
            if soup_pagina_segundo_grau.find("td", id="mensagemRetorno"):
                soup_pagina_segundo_grau = None
            elif soup_pagina_segundo_grau.find("input", id="processoSelecionado"):
                codigo = self.get_codigo_segunda_instancia(soup_pagina_segundo_grau)
                pagina_segundo_grau = session.get(
                    f"{self.urlconsulta_AL_segundo_grau_2}{codigo}",
                    verify=False,
                    timeout=self.timeout,
                )
                soup_pagina_segundo_grau = bs(
                    pagina_segundo_grau.content, features="html.parser"
                )

        segundo_grau_processo_info = self.extract_processo_info(
            soup_pagina_segundo_grau, npu, grau
        )
        return segundo_grau_processo_info

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

    def extract_processo_info(self, pagina: bs, npu: str, grau: str) -> dict:
        # todo scraping segundo grau
        """ """
        try:
            if grau == 1:
                classe = pagina.find("span", {"id": "classeProcesso"}).get_text(
                    strip=True
                )
                assunto = pagina.find("span", {"id": "assuntoProcesso"}).get_text(
                    strip=True
                )
            else:
                classe = pagina.find("div", {"id": "classeProcesso"}).get_text(
                    strip=True
                )
                assunto = pagina.find("div", {"id": "assuntoProcesso"}).get_text(
                    strip=True
                )
            area = pagina.find("div", {"id": "areaProcesso"}).get_text(strip=True)
            if pagina.find("div", {"id": "dataHoraDistribuicaoProcesso"}) is not None:
                data_distribuicao = pagina.find(
                    "div", {"id": "dataHoraDistribuicaoProcesso"}
                ).get_text(strip=True)
            else:    
                data_distribuicao=''
            if pagina.find("span", {"id": "juizProcesso"}) is not None:
                juiz = pagina.find("span", {"id": "juizProcesso"}).get_text(strip=True)
            else:
                juiz=''
            valor_da_acao = (
                pagina.find("div", {"id": "valorAcaoProcesso"})
                .get_text(strip=True)
                .replace(" ", "")
            )
            partes_list = self.extract_partes(pagina)
            movimentos = self.extract_movimentos(pagina)

            return {
                "npu": npu if npu else "",
                "classe": classe if classe else "",
                "area": area if area else "",
                "assunto": assunto if assunto else "",
                "data_distribuicao": data_distribuicao if data_distribuicao else "",
                "juiz": juiz if juiz else "",
                "valor_da_acao": valor_da_acao if valor_da_acao else "",
                "partes": partes_list,
                "movimentos": movimentos,
                "grau": grau if grau else "",
            }
        except Exception as exc:
            logger.exception(exc)
            raise


if __name__ == "__main__":
    robo = Crawler()
    # AL-code 07108025520188020001
    # AL-nocode 08033402420198020000
    #TJCE - 00703379120088060001
    # 0805757-08.2023.8.02.0000
    # 07114332320238020001
    # tribunal = extract_tribunal("07108025520188020001")
    # primeiro_grau_info = robo.send_request_primeiro_grau(
    #     "07108025520188020001", tribunal
    # )
    # print(primeiro_grau_info)
    # segundo_grau_info = robo.send_request_segundo_grau("07108025520188020001", tribunal)
    # print(segundo_grau_info)

    tribunal = extract_tribunal("00703379120088060001")
    primeiro_grau_info = robo.send_request_primeiro_grau(
         "00703379120088060001", tribunal
    )
    print(primeiro_grau_info)
    segundo_grau_info = robo.send_request_segundo_grau("00703379120088060001", tribunal)
    print(segundo_grau_info)
    print("terminado")
