import logging
from embeddings import gerar_embedding_pergunta
from vector_store import obter_colecao, buscar
from reranker import reranquear

logger = logging.getLogger(__name__)

TOP_K_BUSCA_INICIAL = 20 
TOP_N_FINAL = 5 

LIMITE_MAX_CARACTERES_CONTEXTO = 12000
LIMITE_MINIMO_RELEVANCIA = 0.05

def filtrar_por_relevancia(chunks_rerankeados: list[dict], limite_minimo: float) -> list[dict]:
    chunks_relevantes = [
        chunk for chunk in chunks_rerankeados
        if chunk.get("relevance_score", 0.0) >= limite_minimo
    ]

    descartados = len(chunks_rerankeados) - len(chunks_relevantes)
    if descartados > 0:
        logger.info(
            f"{descartados} chunk(s) descartado(s) por relevância abaixo de {limite_minimo}."
        )

    return chunks_relevantes

def montar_filtro_metadados(categoria: str | None = None) -> dict | None:
    if not categoria:
        return None

    return {"categoria": {"$eq": categoria}}

def montar_contexto(chunks_selecionados: list[dict]) -> str:
    if not chunks_selecionados:
        logger.warning("Nenhum chunk selecionado para montar o contexto.")
        return "Nenhum documento relevante ou contexto encontrado no banco de conhecimento."

    blocos_texto = []
    tamanho_acumulado = 0

    for chunk in chunks_selecionados:
        metadados = chunk.get("metadados", {})

        fonte = metadados.get("arquivo_origem", "Fonte desconhecida")
        cat = metadados.get("categoria", "Não categorizado")
        resp = metadados.get("responsavel", "Não informado")
        data = metadados.get("data_atualizacao", "Data indisponível")

        cabecalho = f"[Fonte: {fonte} | Categoria: {cat} | Responsável: {resp} | Atualizado em: {data}]"
        texto_chunk = chunk.get("texto", "").strip()

        bloco_formatado = f"{cabecalho}\n{texto_chunk}\n"

        if tamanho_acumulado + len(bloco_formatado) > LIMITE_MAX_CARACTERES_CONTEXTO:
            logger.warning(
                f"Limite de caracteres do contexto atingido ({LIMITE_MAX_CARACTERES_CONTEXTO}). "
                f"Truncando a inclusão de chunks adicionais."
            )
            break

        blocos_texto.append(bloco_formatado)
        tamanho_acumulado += len(bloco_formatado)

    return "\n---\n\n".join(blocos_texto)

def recuperar_contexto(
    pergunta: str,
    categoria: str | None = None,
    top_k_inicial: int = TOP_K_BUSCA_INICIAL,
    top_n_final: int = TOP_N_FINAL,
) -> tuple[str, list[dict]]:
    logger.info(f"Iniciando recuperação de contexto para a pergunta: '{pergunta}'")

    embedding_pergunta = gerar_embedding_pergunta(pergunta)

    filtros = montar_filtro_metadados(categoria)
    if filtros:
        logger.info(f"Aplicando filtro de metadados por categoria: {categoria}")

    colecao = obter_colecao()
    candidatos_vetoriais = buscar(
        colecao=colecao,
        embedding_consulta=embedding_pergunta,
        top_k=top_k_inicial,
        filtros=filtros
    )

    total_encontrado = len(candidatos_vetoriais)
    logger.info(f"Busca vetorial ampla retornou {total_encontrado} candidatos iniciais.")

    if total_encontrado == 0: 
        logger.warning("A busca vetorial retornou zero candidatos. Abortando etapa de rerank.")
        return montar_contexto([]), []

    logger.info(f"Executando Cohere Rerank para extrair os top {top_n_final} melhores...")

    chunks_rerankeados = reranquear(
        pergunta=pergunta,
        candidatos=candidatos_vetoriais,
        top_n=top_n_final
    )

    chunks_relevantes = filtrar_por_relevancia(chunks_rerankeados, LIMITE_MINIMO_RELEVANCIA)

    logger.info(f"Rerank concluído. {len(chunks_relevantes)} de {len(chunks_rerankeados)} chunks passaram no corte de relevância.")
    for i, chunk in enumerate(chunks_rerankeados, start=1):
        score = chunk.get("relevance_score", 0.0)
        fonte = chunk.get("metadados", {}).get("arquivo_origem", "Desconhecido")
        logger.debug(f" Pos {i}: Score={score:.4f} | Origem={fonte}")

    contexto_final = montar_contexto(chunks_relevantes)
    return contexto_final, chunks_relevantes

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

    pergunta_teste = "qual o contato do RH?"
    contexto, chunks = recuperar_contexto(pergunta_teste)
    print("\n=== CONTEXTO FINAL PRODUZIDO ===\n")
    print(contexto)
    