import re
import unicodedata

def remover_espacos_e_quebras_excessivas(texto: str) -> str:
    if not texto:
        return ""

    texto = re.sub(r'\n\s*\n', '\n\n', texto)
    texto = re.sub(r'[ \t]+', ' ', texto)

    texto = '\n'.join(linha.strip() for linha in texto.split('\n'))

    return texto.strip()

def remover_cabecalhos_rodapes_repetidos(texto: str) -> str:
    if not texto:
        return ""
    
    # Padrão genérico para travas de confidencialidade/marcas d'água comuns
    padroes_corporativos = [
        r'(?i)^confidencial\s*(?:-\s*página\s*\d+)?$',
        r'(?i)^uso\s+interno\s*$',
        r'(?i)^todos\s+os\s+direitos\s+reservados\s*$'
    ]
    
    linhas = texto.split('\n')
    linhas_limpas = []
    
    for linha in linhas:
        linha_strip = linha.strip()
        if any(re.match(padrao, linha_strip) for padrao in padroes_corporativos):
            continue
        linhas_limpas.append(linha)
        
    return '\n'.join(linhas_limpas)

def remover_numeracao_de_pagina(texto: str) -> str:
    if not texto:
        return ""

    padroes = [
        r'(?i)pág(?:ina)?\s*\d+\s*(?:de\s*\d+)?',  # Página 1, pág 2, Página 3 de 10
        r'-\s*\d+\s*-',                             # - 1 -, - 2 -
        r'\[\s*\d+\s*\]',                           #, [2]
        r'^\s*\d+\s*$'                              # Número isolado na linha
    ]

    linhas = texto.split('\n')
    linhas_limpas = []

    for linha in linhas:
        linha_processada = linha
        for padrao in padroes:
            if padrao == r'^\s*\d+\s*$':
                if re.match(padrao, linha_processada):
                    linha_processada = ""
            else:
                linha_processada = re.sub(padrao, "", linha_processada)
        
        linhas_limpas.append(linha_processada)
        
    return '\n'.join(linhas_limpas)

def juntar_linhas_soltas_em_paragrafos(texto: str) -> str:
    """
    Junta quebras de linha 'soltas' (dentro de um mesmo parágrafo) num único
    parágrafo corrido, preservando apenas as quebras que de fato separam
    parágrafos (linha em branco entre elas).

    Isso corrige o padrão comum de PDFs extraídos pelo pypdf, em que cada
    'linha visual' do documento original vira uma linha separada no texto,
    mesmo quando pertence à mesma frase (ex: "pela\\nCEO\\nHelena\\nRamos").
    """
    if not texto:
        return ""

    # Um parágrafo termina onde há uma linha em branco (\n\n).
    paragrafos = re.split(r'\n\s*\n', texto)

    paragrafos_unidos = []
    for paragrafo in paragrafos:
        linhas = [linha.strip() for linha in paragrafo.split('\n')]
        linhas = [linha for linha in linhas if linha]  # remove linhas vazias
        paragrafos_unidos.append(' '.join(linhas))

    return '\n\n'.join(paragrafos_unidos)

def normalizar_caracteres_especiais(texto: str) -> str:
    if not texto:
        return ""

    texto = texto.replace('\u200b', '')
    texto_normalizado = unicodedata.normalize('NFKC', texto)
    return texto_normalizado

def limpar_texto(texto: str) -> str:
    if not texto:
        return ""
        
    texto = normalizar_caracteres_especiais(texto)
    
    texto = remover_numeracao_de_pagina(texto)
    texto = remover_cabecalhos_rodapes_repetidos(texto)

    texto = juntar_linhas_soltas_em_paragrafos(texto)   

    texto = remover_espacos_e_quebras_excessivas(texto)
    
    return texto