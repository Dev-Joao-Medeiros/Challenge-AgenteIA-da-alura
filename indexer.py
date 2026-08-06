import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

from embeddings import gerar_embeddings_em_lote
from vector_store import obter_colecao, adicionar_chunks

def carregar_chunks(caminho_chunks_json: str) -> list[dict]:
    caminho = Path(caminho_chunks_json)

    if not caminho.exists():
        logging.error(f"Arquivo de chunks não encontrado: {caminho_chunks_json}")
        raise FileNotFoundError(f"O arquivo essencial '{caminho_chunks_json}' não foi localizado.")
    
    logging.info(f"Carregando chunks de: {caminho.resolve()}")
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)

def filtrar_chunks_validos(chunks: list[dict]) -> list[dict]:
    chunks_validos = []

    for i, chunk in enumerate(chunks):
        texto = chunk.get("texto", "")
        metadados = chunk.get("metadados", {})

        origem = metadados.get("caminho_completo") or metadados.get("arquivo_origem") or "origem desconhecida"

        if texto and texto.strip():
            chunks_validos.append(chunk)
        else:
            logging.warning(
                f"Chunk descartado por estar vazio. Origem: {origem} | Índice original: {i}"
            )
    return chunks_validos

def gerar_id_chunk(metadados: dict, indice_chunk: int) -> str:
    identificador_arquivo = metadados.get("caminho_completo") or metadados.get("arquivo_origem")

    if not identificador_arquivo:
        raise ValueError("Metadados do chunk não possuem informações de 'caminho_completo' ou 'arquivo_origem'.")

    return f"{identificador_arquivo}::chunk_{indice_chunk}"

def montar_registros_para_indexacao(
        chunks_validos: list[dict],
        embeddings: list[list[float]]
) -> list[dict]:
    if len(chunks_validos) != len(embeddings):
        logging.error(f"Inconsistência crítica: {len(chunks_validos)} chunks para {len(embeddings)} embeddings.")
        raise ValueError("A quantidade de chunks válidos não corresponde à quantidade de embeddings gerados.")

    registros = []

    for chunk, embedding in zip(chunks_validos, embeddings):
        indice_real = chunk["metadados"].get("indice_chunk", 0)
        id_unico = gerar_id_chunk(chunk["metadados"], indice_real)

        registros.append({
            "id": id_unico,
            "texto": chunk["texto"],
            "embedding": embedding,
            "metadados": chunk["metadados"]
    })

    return registros

def indexar_chunks(caminho_chunks_json: str) -> None:
    try:
        chunks_brutos = carregar_chunks(caminho_chunks_json)
        total_bruto = len(chunks_brutos)

        chunks_validos = filtrar_chunks_validos(chunks_brutos)
        total_descartados = total_bruto - len(chunks_validos)

        if not chunks_validos:
            logging.warning("Nenhum chunk válido restou após a filtragem. Processo interrompido.")
            return

        logging.info(f"Gerando embeddings para {len(chunks_validos)} chunks...")
        textos_para_vetorizar = [c["texto"] for c in chunks_validos]
        embeddings_gerados = gerar_embeddings_em_lote(textos_para_vetorizar)

        registros_finais = montar_registros_para_indexacao(chunks_validos, embeddings_gerados)

        logging.info("Conectando ao ChromaDB e persistindo os dados...")
        colecao = obter_colecao()
        adicionar_chunks(colecao, registros_finais)

        logging.info("=== RESUMO DA INDEXAÇÃO VETORIAL ===")
        logging.info(f"Total de chunks analisados: {total_bruto}")
        logging.info(f"Total de chunks indexados com sucesso: {len(registros_finais)}")
        logging.info(f"Total de chunks descartados (vazios): {total_descartados}")
        logging.info("====================================")

    except FileNotFoundError as fnf:
        logging.error(f"Erro de arquivo: {str(fnf)}")
    except ValueError as ve:
        logging.error(f"Erro de consistência nos dados: {str(ve)}")
    except Exception as e:
        logging.critical(f"Falha crítica inesperada durante a indexação: {str(e)}", exc_info=True)

if __name__ == "__main__":
    caminho_padrao = "saida/chunks.json"
    indexar_chunks(caminho_padrao)