import asyncio
import json
from api import schema
from fastapi import FastAPI, HTTPException
from crawler_jus.crawler import Crawler
from crawler_jus.util import extract_tribunal, valida_npu, remove_special_characters


app = FastAPI()


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
        crawler = Crawler()
        npu = cliente.npu
        npu = remove_special_characters(npu)
        tribunal = extract_tribunal(npu)
        if tribunal == "02" or tribunal == "06":
            if not valida_npu(npu):
                raise HTTPException(
                    status_code=400, detail="Número do processo inválido"
                )

            task1 = asyncio.create_task(
                crawler.send_request_primeiro_grau(npu, tribunal)
            )
            task2 = asyncio.create_task(
                crawler.send_request_segundo_grau(npu, tribunal)
            )

            await asyncio.gather(task1, task2)

            result1 = task1.result()
            result2 = task2.result()

            result1 = result1.__dict__
            result2 = result2.__dict__
            results = []

            if result1:
                results.append(result1)

            if result2:
                results.append(result2)

            if len(results) == 0:
                raise HTTPException(
                    status_code=404, detail="Nenhum processo encontrado"
                )

            return results
        raise HTTPException(
            status_code=404,
            detail="O número de processo apresentado não possui tribunal valido",
        )

    except Exception as exc:
        # print(exc)
        raise HTTPException(status_code=500, detail="Erro ao processar a requisição.")
