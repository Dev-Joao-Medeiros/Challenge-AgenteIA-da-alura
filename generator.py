import re
import logging
from collections import OrderedDict

from llm import gerar_resposta_llm
from retrieval import recuperar_contexto

logger = logging.getLogger(__name__)

MENSAGEM_FALLBACK = (
    "Não encontrei essa informação nos documentos disponíveis. "
    "Para dúvidas desse tipo, entre em contato com a área responsável "
    "(RH, Financeiro, Jurídico, conforme o assunto)."
)

PADROES_SOCIAIS = [
    r"^oi\b", r"^ol[áa]\b", r"^bom dia\b", r"^boa tarde\b", r"^boa noite\b",
    r"^tudo bem", r"^como vai", r"^obrigad[oa]", r"^valeu\b", r"^tchau\b",
    r"^at[ée] mais\b", r"^até logo\b",
]

def parece_social(pergunta: str) -> bool:
    pergunta_normalizada = pergunta.strip().lower()

    if len(pergunta_normalizada.split()) > 6:
        return False

    return any(re.match(padrao, pergunta_normalizada) for padrao in PADROES_SOCIAIS)

def montar_prompt(pergunta: str, contexto: str) -> dict:
    system_prompt = (
        "Você é um assistente corporativo prestativo, empático e focado em ajudar os colaboradores.\n\n"
        "1. COMPORTAMENTO E INTERAÇÃO SOCIAL:\n"
        "- Seja natural, amigável e dinâmico. Evite responder frases idênticas aos exemplos.\n"
        "- Se o usuário enviar saudações, perguntas sobre seu bem-estar ou agradecimentos, interaja de forma calorosa, humana e profissional, convidando-o a tirar dúvidas.\n"
        "- Você tem permissão para usar conhecimento geral APENAS para manter essa conversa social fluida e cortês.\n\n"
        "2. RESPOSTAS CORPORATIVAS (REGRAS ESTRITAS):\n"
        "- Para qualquer dúvida factual, técnica ou sobre processos da empresa, baseie-se APENAS no contexto fornecido.\n"
        "- Sempre referencie a fonte da informação usando a tag [Fonte: nome_do_arquivo], conforme fornecida no contexto.\n"
        f"- Nunca invente dados corporativos. Se a dúvida técnica não estiver no contexto, responda exatamente com a seguinte frase: '{MENSAGEM_FALLBACK}'\n\n"
        "3. LINGUAGEM:\n"
        "- Responda no mesmo tom do usuário, mantendo a postura de um colega de trabalho prestativo."
    )

    user_prompt = (
        f"### CONTEXTO ###\n{contexto}\n\n"
        f"### PERGUNTA ###\n{pergunta}"
    )

    return {
        "system": system_prompt,
        "user": user_prompt
    }

def formatar_resposta_final(resposta_llm: str, chunks_usados: list[dict]) -> dict:
    resposta_limpa = re.sub(r"\[Fonte:.*?\]", "", resposta_llm).strip()

    fontes_unicas = OrderedDict()

    for chunk in chunks_usados:
        nome_arquivo = chunk.get("metadados", {}).get("arquivo_origem", "Documento Oculto")
        category_doc = chunk.get("metadados", {}).get("categoria", "Geral")

        if nome_arquivo not in fontes_unicas:
            fontes_unicas[nome_arquivo] = {
                "arquivo": nome_arquivo,
                "categoria": category_doc
            }

    return {
        "resposta": resposta_limpa,
        "fontes": list(fontes_unicas.values())
    }

def extrair_fontes_citadas(resposta_llm: str, chunks_relevantes: list[dict]) -> list[dict]:
    chunks_citados = [
        chunk for chunk in chunks_relevantes
        if chunk.get("metadados", {}).get("arquivo_origem", "") in resposta_llm
    ]
    return chunks_citados

def responder_pergunta(pergunta: str, categoria: str | None = None) -> dict:
    logger.info(f"Iniciando processo de resposta para a pergunta: '{pergunta}'")

    if parece_social(pergunta):
        logger.info("Pergunta identificada como social -- pulando busca de contexto.")
        prompt_social =montar_prompt(pergunta, contexto="(nenhum documento consultado -- interação social)")
        prompt_final_string = f"{prompt_social['system']}\n\n{prompt_social['user']}"
        resposta_llm = gerar_resposta_llm(prompt_final_string)
        return {"resposta": resposta_llm.strip(), "fontes": []}


    contexto_str, chunks_relevantes = recuperar_contexto(pergunta, categoria)

    if not contexto_str or not chunks_relevantes:
        logger.warning("Nenhum contexto recuperado. Retornando mensagem de fallback imediatamente.")
        return{
            "resposta": MENSAGEM_FALLBACK,
            "fontes": []
        }

    payload_prompt = montar_prompt(pergunta, contexto_str)

    prompt_final_string = f"{payload_prompt['system']}\n\n{payload_prompt['user']}"

    logger.info("Enviando prompt ao LLM Groq...")
    resposta_llm = gerar_resposta_llm(prompt_final_string)

    palavras_chaves_insuficiencia = ["não encontrei", "não consta", "desculpe", "informação não disponível"]
    if any(keyword in resposta_llm.lower() for keyword in palavras_chaves_insuficiencia):
        logger.info("LLM identificou insuficiência de dados no contexto. Aplicando fallback de consistência.")
        return {
            "resposta": MENSAGEM_FALLBACK,
            "fontes": []
        }
    chunks_para_fontes = extrair_fontes_citadas(resposta_llm, chunks_relevantes)

    logger.info("Formatando resposta final e consolidando fontes.")
    resultado_estruturado = formatar_resposta_final(resposta_llm, chunks_para_fontes)

    return resultado_estruturado

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    pergunta_teste = "como funciona o reembolso de despesas?"

    try:
        resultado = responder_pergunta(pergunta_teste)
        print("\n=== RESPOSTA FINAL ===\n")
        print(resultado)
    except Exception as err:
        logger.error(f"Erro na execução do orquestrador principal: {err}")