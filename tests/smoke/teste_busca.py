from src.indexing.embeddings import gerar_embedding
from src.indexing.vector_store import obter_colecao, buscar

pergunta = "Qual o cronograma do primeiro dia de trabalho?"
embedding_pergunta = gerar_embedding(pergunta)

colecao = obter_colecao()
resultados = buscar(colecao, embedding_pergunta, top_k=3)

for r in resultados:
    print(r["metadados"].get("arquivo_origem"), "-", r["distancia"])
    print(r["texto"][:150], "...\n")