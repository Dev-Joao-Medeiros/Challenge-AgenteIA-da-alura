import os
import time
from dotenv import load_dotenv
import cohere

load_dotenv()

MODELO_EMBEDDING = "embed-multilingual-v3.0"
LIMITE_LOTE_COHERE = 96

_cliente_cohere: cohere.Client | None = None

def configurar_cliente_embeddings()  ->  cohere.Client:
    global _cliente_cohere

    if _cliente_cohere is not None:
        return _cliente_cohere

    api_key = os.getenv("COHERE_API_KEY")

    if not api_key:
        raise ValueError(
            "Erro: A variável de ambiente COHERE_API_KEY não foi encontrada. "
            "Verifique o seu arquivo .env."
        )

    _cliente_cohere = cohere.Client(api_key=api_key)
    return _cliente_cohere

def gerar_embedding(texto: str) -> list[float]:
    if not texto or not texto.strip():
        raise ValueError("O texto fornecido para embedding não pode ser vazio.")

    co = configurar_cliente_embeddings()

    try:
        resposta = co.embed(
            texts = [texto],
            model=MODELO_EMBEDDING,
            input_type="search_document",
            embedding_types=["float"]
        )

        return resposta.embeddings.float[0]

    except Exception as e:
        print(f"Erro ao gerar embedding: {e}")
        raise e

def gerar_embeddings_em_lote(textos: list[str]) -> list[list[float]]:
    

    co = configurar_cliente_embeddings()
    todos_embedding = []

    for i in range(0, len(textos), LIMITE_LOTE_COHERE):
        lote_atual = textos[i : i + LIMITE_LOTE_COHERE]
        print(f"Processamento lote {i // LIMITE_LOTE_COHERE + 1} ... ({len(lote_atual)} textos)")

        try:
            resposta = co.embed(
                texts = lote_atual,
                model= MODELO_EMBEDDING,
                input_type = "search_document",
                embedding_types = ["float"]
            )
            todos_embedding.extend(resposta.embeddings.float)

        except Exception as e:
            print(f"Erro ao processar lote a partir do índice {i}: {e}")
            raise e

        if i + LIMITE_LOTE_COHERE < len(textos):
            print("Aguardando um momento para o próximo lote...")
            time.sleep(2)

    return todos_embedding
