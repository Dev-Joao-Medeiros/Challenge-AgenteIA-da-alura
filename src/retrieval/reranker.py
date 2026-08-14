import os
import logging
import cohere
from cohere.core.api_error import ApiError

logger = logging.getLogger(__name__)

MODELO_RERANKER = "rerank-multilingual-v3.0"

_client_cohere_rerank: cohere.Client | None = None

def _obter_client() -> cohere.Client:
    global _client_cohere_rerank

    if _client_cohere_rerank is None:
        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            logger.error("A variável de ambiente COHERE_API_KEY não foi encontrada.")
            raise ValueError("COHERE_API_KEY não configurada.")

        _client_cohere_rerank = cohere.Client(api_key=api_key)

    return _client_cohere_rerank

def reranquear(pergunta: str, candidatos: list[dict], top_n: int = 5) -> list[dict]:
    if not candidatos:
        logger.info("Nenhum candidato fornecido para rerank. Retornando lista vazia.")
        return []

    try:
        co = _obter_client()

        textos_documentos = [candidato["texto"] for candidato in candidatos]

        limite_top_n = min(top_n, len(candidatos))

        resposta = co.rerank(
            model=MODELO_RERANKER,
            query=pergunta,
            documents=textos_documentos,
            top_n=limite_top_n
        )

        resultados_reordenados = []

        for resultado in resposta.results:
            indice_original = resultado.index
            candidato_original = candidatos[indice_original]

            novo_candidato = {
                "id": candidato_original.get("id"),
                "texto": candidato_original.get("texto"),
                "metadados": candidato_original.get("metadados"),
                "relevance_score": resultado.relevance_score
            }

            resultados_reordenados.append(novo_candidato)

        return resultados_reordenados

    except ApiError as ce:
        logger.error(f"Erro de API na Cohere durante o Rerank: {ce}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Erro inesperado no módulo de Rerank: {e}", exc_info=True)
        raise
