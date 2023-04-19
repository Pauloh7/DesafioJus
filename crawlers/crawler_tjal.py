from datetime import datetime
import logging
import re
import requests
from bs4 import BeautifulSoup as bs
from tenacity import (
    retry,
    wait_fixed,
    stop_after_attempt,
)

logger = logging.getLogger()


class CrawlerTjal:
    """
    Robo que extrai dados do site TJAL(Tribunal de Justiça do Estado de Alagoas)

    Attributes:
        browser (str): This is where we store arg,


    """

    def __init__(self):
        self.timeout = 1000
        self.urlconsulta = "https://www2.tjal.jus.br/cpopg/show.do?processo.numero="

    def remove_blank_space(self, txt):
        """"""
        array = txt.split()
        return " ".join(array).strip()

    def remove_special_characters(self, texto):
        """"""
        texto_corrigido = texto
        texto_corrigido = re.sub(
            r"[\\\/,;<>\.\?\/\!\*\-\+\_\=\@\#%:\(\)" "]+", "", texto_corrigido
        )
        texto_corrigido = re.sub(r"\(\)", "", texto_corrigido)
        texto_corrigido = re.sub(r"\s{2,}", " ", texto_corrigido)
        texto_corrigido = re.sub(r"^\s+", "", texto_corrigido)
        texto_corrigido = re.sub(r"\s+$", "", texto_corrigido)
        return texto_corrigido

    def extract_partes(self, pagina):
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
            if len(td) == 2 and not "ADVOGAD" in self.remove_special_characters(
                td[0].text
            ):
                tipo_parte = self.remove_special_characters(td[0].text)
                nome_parte = self.remove_special_characters(td[1].next)
                if len(td[1].find_all("span")) >= 1:
                    for advs in td[1].find_all("span"):
                        lista_advogados.append(
                            "Advogado(a): "
                            + self.remove_special_characters(advs.next_sibling)
                        )
            else:
                lista_advogados.append(
                    "Advogado(a): " + self.remove_special_characters(td[1].text)
                )

            partes_list.append([tipo_parte, nome_parte, lista_advogados])
        return partes_list

    def extract_movimentos(self, pagina):
        julgamento_movimento = False
        movimentos = []
        movimentacao = pagina.find(
            "h2", text=re.compile(".*Movimentações.*", re.IGNORECASE)
        )
        if movimentacao:
            movimentacao = movimentacao.find_parent("div")
            if movimentacao:
                movimentacao = movimentacao.find_next_sibling("table")
                if (
                    self.remove_blank_space(movimentacao.text)
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
                                self.remove_blank_space(
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
                                tipo_movimento = self.remove_special_characters(
                                    movimento.find("a").text
                                )
                            else:
                                tipo_movimento = self.remove_special_characters(
                                    movimento.next
                                )
                            texto_movimento = self.remove_special_characters(
                                linha.find("span").text
                            )
                            if texto_movimento:
                                movimento_completo = (
                                    tipo_movimento + " " + texto_movimento
                                )
                            else:
                                movimento_completo = tipo_movimento
                            movimentos.append([data, movimento_completo])
                    except Exception as e:
                        print(e)
                        movimentos = None

        return movimentos

    @retry(wait=wait_fixed(1), stop=stop_after_attempt(5))
    def extract_processo_info_primeira_instancia(self, npu: str) -> str:
        """ """

        session = requests.Session()
        data = session.get(
            f"{self.urlconsulta}{npu}", verify=False, timeout=self.timeout
        )
        pagina = bs(data.content, features="html.parser")
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

            print(juiz)
        except Exception as exe:
            print(exe)


if __name__ == "__main__":
    robo = CrawlerTjal()
    # 07108025520188020001
    # 07114332320238020001
    robo.extract_processo_info_primeira_instancia("07108025520188020001")
