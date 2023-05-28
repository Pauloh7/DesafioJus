from fastapi import FastAPI, HTTPException
import schema
from crawler_jus.crawler import Crawler

app = FastAPI()


@app.post("/search_cpf/")
async def search_cpf(cliente: schema.ClienteInput) -> dict:
    """Parte da api que recebe o post com dados do processo e executa chamada para extração dos dados
    Args:
        cliente (schema.ClienteInput): Json com numero do processo
    Returns:
        processo_info (dict): Dicionário com dados do processo
    Raises:
        HTTPException: Erro de processamento na requisição
    """

    try:
        crawler = Crawler()
        npu = cliente.npu
        npu_split = npu.split(".")
        tribunal = npu_split[3]
        if tribunal == "02" or tribunal == "06"
            if processo_info := crawler.extract_processo_info(npu, tribunal):
                return processo_info
            return {"detalhes": "Não foram encontrados processos."}
        return {"detalhes": "O número de processo apresentado não possui tribunal valido."}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao processar a requisição.")
