import chromadb
from pathlib import Path

CAMINHO_BANCO_VETORIAL = "chroma_db"
NOME_COLECAO = "tyche_pay_documentos"

def obter_colecao():
    Path(CAMINHO_BANCO_VETORIAL).mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=CAMINHO_BANCO_VETORIAL)

    colecao = client.get_or_create_collection(name=NOME_COLECAO, embedding_function=None)

    return colecao

def adicionar_chunks(colecao, chunks: list[dict]) -> None:
    if not chunks:
        return

    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for chunk in chunks:
        ids.append(chunk["id"])
        embeddings.append(chunk["embedding"])
        documents.append(chunk["texto"])

        metadados_limpos = {}

        for chave, valor in chunk.get("metadados", {}).items():
            if isinstance(valor, (str, int, float, bool)):
                metadados_limpos[chave] = valor
            else:
                metadados_limpos[chave] = str(valor)

        metadatas.append(metadados_limpos)

    colecao.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )


def buscar(colecao, embedding_consulta: list[float], top_k: int = 5, filtros:  dict | None = None) -> list[dict]:
    resultados = colecao.query(
        query_embeddings=[embedding_consulta],
        n_results=top_k,
        where=filtros
    )

    lista_formatada = []

    if resultados and resultados["ids"] and len(resultados["ids"][0]) > 0:
        ids = resultados["ids"][0]
        documents = resultados["documents"][0]
        metadatas = resultados["metadatas"][0]
        distances = resultados["distances"][0] if "distances" in resultados and resultados["distances"] else [0.0] * len(ids)

        for i in range(len(ids)):
            lista_formatada.append({
                "id": ids[i],
                "texto": documents[i],
                "metadados": metadatas[i],
                "distancia": distances[i]
            })

    return lista_formatada