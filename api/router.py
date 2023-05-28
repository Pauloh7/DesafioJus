from fastapi import FastAPI, HTTPException
import schema
from crawler_jus.crawler import Crawler

app = FastAPI()


@app.post("/search_cpf/")
async def search_cpf(cliente: schema.ClienteInput) -> dict:
    """Parte da api que recebe o post com dados do cliente e executa chamada para extração dos benefícios
    Args:
        cliente (schema.ClienteInput): Json com dados do cliente
    Returns:
        resultado_dict (dict): Dicionário com número do benefício
    Raises:
        HTTPException: Erro de processamento na requisição
    """

    try:
        crawler = Crawler()
        cliente.npu
        
        if numero_beneficio := crawler.extract_processo_info(
        ):
            return {"numero_do_beneficio": numero_beneficio}

        return {"detalhes": "Não foram encontrados benefícios para o CPF informado."}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao processar a requisição.")