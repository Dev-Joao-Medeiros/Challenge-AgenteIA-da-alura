import json
from pathlib import Path

from extractor import extrair, EXTRATORES_POR_EXTENSAO
from cleaning import limpar_texto
from chunking import chunk_texto
from metadata import carregar_metadados_catalogo, montar_metadados_chunk


def processar_documento(
    caminho_arquivo: Path,
    metadados_catalogo: dict,
    estrategia_chunking: str = "tamanho_fixo",
    **kwargs_chunking,
) -> list[dict]:
    """
    Processa um único documento do início ao fim do pipeline.
    Devolve a lista de chunks prontos: [{"texto": str, "metadados": dict}, ...]
    """

    # 1. Extração: delega pro extractors.py, que já sabe escolher a função
    #    certa com base na extensão do arquivo.
    texto_bruto, metadados_basicos = extrair(caminho_arquivo)

    # O extractors.py não sabe (e não precisa saber) o caminho completo do
    # arquivo -- ele só lida com o conteúdo. Quem injeta essa informação
    # nos metadados é o orquestrador, aqui, porque é quem tem essa info.
    metadados_basicos["arquivo_origem"] = str(caminho_arquivo)

    # 2. Limpeza: função agnóstica de formato, só trabalha em cima da string.
    texto_limpo = limpar_texto(texto_bruto)

    # Se depois da limpeza não sobrou nada de útil (documento vazio,
    # ou só tinha ruído), não faz sentido seguir pro chunking.
    if not texto_limpo:
        print(f"Aviso: '{caminho_arquivo.name}' não gerou texto após a limpeza. Pulando.")
        return []

    # 3. Chunking: divide o texto limpo em pedaços, segundo a estratégia
    #    escolhida (por padrão, tamanho fixo).
    chunks_texto = chunk_texto(texto_limpo, estrategia=estrategia_chunking, **kwargs_chunking)

    # 4. Metadados: para cada chunk gerado, monta o dicionário final de
    #    metadados combinando o que veio da extração com o que está
    #    cadastrado na planilha (catálogo da Etapa 1).
    chunks_processados = []
    for indice, chunk in enumerate(chunks_texto):
        metadados_finais = montar_metadados_chunk(
            metadados_basicos=metadados_basicos,
            indice_chunk=indice,
            metadados_catalogo=metadados_catalogo,
        )
        chunks_processados.append({
            "texto": chunk,
            "metadados": metadados_finais,
        })

    return chunks_processados


def processar_diretorio(caminho_documentos: Path, caminho_planilha: str) -> list[dict]:
    """
    Varre o diretório de documentos e processa todos os arquivos de
    formato suportado, devolvendo a lista completa de chunks de todos
    os documentos combinados.
    """

    # O catálogo (planilha da Etapa 1) só precisa ser carregado uma vez,
    # não a cada arquivo -- por isso fica fora do loop.
    metadados_catalogo = carregar_metadados_catalogo(caminho_planilha)
    
    # Extensões que o extractors.py sabe processar hoje (pdf, docx, xlsx, csv).
    # Consultar isso aqui evita hardcodar a lista de novo -- se você
    # adicionar um novo formato no extractors.py, o main.py acompanha
    # automaticamente, sem precisar editar nada aqui.
    extensoes_suportadas = set(EXTRATORES_POR_EXTENSAO.keys())

    todos_os_chunks = []

    # rglob("*") varre recursivamente todas as subpastas (rh/, financeiro/,
    # legal/ etc.) dentro de /documentos.
    for caminho_arquivo in caminho_documentos.rglob("*"):

        # Pula diretórios -- só nos interessam arquivos.
        if not caminho_arquivo.is_file():
            continue

        # Pula arquivos de formato ainda não suportado (ex: .pptx, .json),
        # em vez de deixar o pipeline inteiro quebrar no meio da execução.
        if caminho_arquivo.suffix.lower() not in extensoes_suportadas:
            print(f"Aviso: formato '{caminho_arquivo.suffix}' ainda não suportado. Pulando '{caminho_arquivo.name}'.")
            continue

        # try/except por arquivo: se UM documento falhar na extração
        # (ex: PDF corrompido), o processamento dos outros continua.
        try:
            chunks_do_documento = processar_documento(caminho_arquivo, metadados_catalogo)
            todos_os_chunks.extend(chunks_do_documento)
            print(f"OK: '{caminho_arquivo.name}' processado -> {len(chunks_do_documento)} chunks.")
        except Exception as erro:
            print(f"Erro ao processar '{caminho_arquivo.name}': {erro}")
            continue

    return todos_os_chunks


def salvar_resultado(chunks: list[dict], caminho_saida: str) -> None:
    """
    Salva a lista final de chunks processados em um único arquivo JSON,
    pronto para ser consumido pela Etapa 3 (geração de embeddings).
    """

    # Garante que a pasta de saída existe antes de tentar escrever o arquivo.
    Path(caminho_saida).parent.mkdir(parents=True, exist_ok=True)

    with open(caminho_saida, "w", encoding="utf-8") as arquivo_saida:
        # ensure_ascii=False preserva acentuação legível no JSON,
        # em vez de converter tudo pra sequências de escape (\u00e7 etc.)
        json.dump(chunks, arquivo_saida, ensure_ascii=False, indent=2)

    print(f"\n{len(chunks)} chunks salvos em '{caminho_saida}'.")


if __name__ == "__main__":
    caminho_documentos = Path("Docs")
    caminho_planilha = "Tyche_Pay_Mapeamento_de_Documentos.xlsx"
    caminho_saida = "saida/chunks.json"

    chunks_finais = processar_diretorio(caminho_documentos, caminho_planilha)
    salvar_resultado(chunks_finais, caminho_saida)