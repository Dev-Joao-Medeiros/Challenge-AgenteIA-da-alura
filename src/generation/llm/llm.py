import os
import logging
from groq import Groq

logger = logging.getLogger(__name__)

MODELO_LLM = "openai/gpt-oss-20b"

_cliente_groq: Groq | None = None


def _obter_cliente() -> Groq:

    global _cliente_groq

    if _cliente_groq is not None:
        return _cliente_groq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("A variável de ambiente GROQ_API_KEY não foi encontrada.")
        raise ValueError("A chave de API do Groq (GROQ_API_KEY) deve estar configurada nas variáveis de ambiente.")

    _cliente_groq = Groq(api_key=api_key)
    return _cliente_groq

def gerar_resposta_llm(prompt: str, temperatura: float=0.2) -> str:

    try:
        cliente = _obter_cliente()

        resposta = cliente.chat.completions.create(
            model=MODELO_LLM,
            messages =[
                {"role": "user", "content": prompt}
            ],
            temperature=temperatura
        )

        conteudo = resposta.choices[0].message.content
        if conteudo is None:
            raise ValueError("O LLM retornou uma resposta vazia.")
            
        return conteudo

    except Exception as e:
        logger.error(f"Erro ao gerar resposta com o LLM Groq: {str(e)}", exc_info=True)
        raise e