from pydantic import BaseModel


class ClienteInput(BaseModel):
    """Schema do Json de input da api"""

    cpf: str
    login: str
    senha: str