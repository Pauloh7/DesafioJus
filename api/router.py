import asyncio
import json
from api import schema
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from crawler_jus.crawler import Crawler
from crawler_jus.util import extract_tribunal, valida_npu, remove_special_characters


@asynccontextmanager
async def lifespan(app: FastAPI):
    crawler = Crawler()
    app.state.crawler = crawler

    yield

    await crawler.aclose()


app = FastAPI(lifespan=lifespan)

@app.post("/search_npu/")
async def search_npu(cliente: schema.ClienteInput) -> list[dict]:
    """Parte da api que recebe o post com dados do processo e executa chamada para extração dos dados
    Args:
        cliente (schema.ClienteInput): Json com numero do processo
    Returns:
        processo_info (dict): Dicionário com dados do processo
    Raises:
        HTTPException: Erro de processamento na requisição
    """

    try:
        crawler: Crawler = app.state.crawler
        npu = remove_special_characters(cliente.npu)
        tribunal = extract_tribunal(npu)
        if tribunal not in ("02", "06"):
            raise HTTPException(
                status_code=404,
                detail="O número de processo apresentado não possui tribunal valido",
            )

        if not valida_npu(npu):
            raise HTTPException(
                status_code=400,
                detail="Número do processo inválido",
            )

        result1, result2 = await asyncio.gather(
            crawler.send_request_primeiro_grau(npu, tribunal),
            crawler.send_request_segundo_grau(npu, tribunal),
        )

        results = []

        if result1:
            results.append(result1.__dict__)

        if result2:
            results.append(result2.__dict__)

        if not results:
            raise HTTPException(
                status_code=404, detail="Nenhum processo encontrado"
            )

        return results

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Erro ao processar a requisição.")
