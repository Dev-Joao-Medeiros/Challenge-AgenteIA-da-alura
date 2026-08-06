def chunk_por_tamanho_fixo(
    texto: str,
    tamanho_chunk: int = 800,
    sobreposicao: int = 100,
) -> list[str]:

    if not texto:
        return []

    if sobreposicao >= tamanho_chunk:
        raise ValueError("A sobreposição deve ser menor que o tamanho do chunk.")

    chunks = []
    inicio = 0
    tamanho_texto = len(texto)

    while inicio < tamanho_texto:
        fim = inicio + tamanho_chunk
        chunk = texto[inicio:fim]
        chunks.append(chunk)
        inicio += tamanho_chunk - sobreposicao

    return chunks   

def chunk_por_estrutura(texto: str, tipo_documento: str, **kwargs) -> list[str]:
    if not texto:
        return []

    tipo = tipo_documento.lower().strip(".")

    if tipo in ["docx", "md", "txt"]:
        return [p.strip() for p in texto.split("\n\n") if p.strip()]

    if tipo in ["xlsx", "csv"]:
        linhas = [l.strip() for l in texto.split("\n") if l.strip()]
        if not linhas:
            return []

        repetir_cabecalho = kwargs.get("repetir_cabecalho_tabela", False)

        if repetir_cabecalho and len(linhas) > 1:
            cabecalho = linhas[0]
            chunks_tabela = []
            for linha_dados in linhas[1:]:
                chunks_tabela.append(f"{cabecalho}\n{linha_dados}")
            return chunks_tabela
        
        return [texto.strip()]

    return [texto]

def chunk_texto(
    texto: str,
    estrategia: str = "tamanho_fixo",
    **kwargs,
) -> list[str]:
    if estrategia == "tamanho_fixo":
        tamanho = kwargs.get("tamanho_chunk", 800)
        sobreposicao = kwargs.get("sobreposicao", 100)
        return chunk_por_tamanho_fixo(
            texto, tamanho_chunk=tamanho, sobreposicao=sobreposicao
        )

    if estrategia == "estrutura":
        tipo_documento = kwargs.pop("tipo_documento", None)
        if not tipo_documento:
            raise ValueError(
                "O parâmetro 'tipo_documento' é obrigatório para a estratégia 'estrutura'."
            )
        return chunk_por_estrutura(texto, tipo_documento=tipo_documento, **kwargs)

    raise ValueError(f"Estratégia de chunking desconhecida: {estrategia}")