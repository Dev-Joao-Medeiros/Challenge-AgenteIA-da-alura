import os
import pandas as pd
from typing import Dict, Any, Optional


def _valor_ou_padrao(linha: pd.Series, coluna: str, padrao: Any) -> Any:
    """
    Busca um valor numa linha do DataFrame, tratando tanto coluna ausente
    quanto célula vazia (NaN) -- os dois casos que o pandas trata de forma
    diferente de um dict comum.
    """
    valor = linha.get(coluna, padrao)
    if pd.isna(valor):
        return padrao
    return valor


def carregar_metadados_catalogo(caminho_planilha: str) -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(caminho_planilha):
        raise FileNotFoundError(f"Planilha não encontrada em: {caminho_planilha}")

    df = pd.read_excel(caminho_planilha)

    catalogo = {}

    for _, linha in df.iterrows():
        nome_arquivo = str(_valor_ou_padrao(linha, 'Nome do Arquivo (exato)', '')).strip()

        if nome_arquivo:
            catalogo[nome_arquivo] = {
                "categoria": _valor_ou_padrao(linha, "Categoria (oficial do desafio)", "Não Informado"),
                "responsavel": _valor_ou_padrao(linha, "Responsável Sugerido (Owner)", "Não Informado"),
                "versao": _valor_ou_padrao(linha, "Versão", "1.0"),
                "classificacao_acesso": _valor_ou_padrao(linha, "Classificação de Acesso", "Restrito"),
                "data_atualizacao": str(_valor_ou_padrao(linha, "Data da Última Atualização", "")),
            }

    return catalogo


def montar_metadados_chunk(
    metadados_basicos: dict,
    indice_chunk: int,
    metadados_catalogo: dict,
) -> dict:
    caminho_completo = metadados_basicos.get("arquivo_origem", "")
    nome_arquivo = os.path.basename(caminho_completo)

    info_catalogo = metadados_catalogo.get(nome_arquivo, {})
    if not info_catalogo:
        print(f"Aviso: {nome_arquivo} não encontrado no catálogo. Usando valores padrão.")

    # TODO (pendente, não resolvido aqui): nenhum extrator hoje devolve uma
    # chave "localizacao" nos metadados básicos (PDF devolve "paginas",
    # XLSX devolve "abas", etc.). Por isso este campo sempre cai no padrão
    # "Desconhecida" por enquanto. Resolver exige decidir, por extrator,
    # como expor a posição de cada chunk (nº de página, nome da aba...) e
    # repassar isso adiante -- fica como próximo passo de arquitetura.
    metadados_finais = {
        "arquivo_origem": caminho_completo,
        "localizacao": metadados_basicos.get("localizacao", "Desconhecida"),
        "indice_chunk": indice_chunk,
        "categoria": info_catalogo.get("categoria", "Geral"),
        "responsavel": info_catalogo.get("responsavel", "Suporte"),
        "versao": info_catalogo.get("versao", "N/A"),
        "classificacao_acesso": info_catalogo.get("classificacao_acesso", "Público"),
        "data_atualizacao": info_catalogo.get("data_atualizacao", "N/A"),
    }

    return metadados_finais