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

def montar_prompt(pergunta: str, contexto: str) -> dict:
    system_prompt = (
        "Você é um assistente corporativo focado em responder dúvidas dos colaboradores.\n"
        "Diretrizes estritas:\n"
        "1. Responda a pergunta baseando-se APENAS no contexto fornecido abaixo.\n"
        "2. NÃO utilize qualquer conhecimento externo ou geral prévio ao seu treinamento.\n"
        "3. Se a informação não estiver clara ou explícita no contexto, não tente adivinhar. "
        f"Responda exatamente com a seguinte frase: '{MENSAGEM_FALLBACK}'\n"
        "4. Sempre indique de qual documento o fato foi extraído, referenciando a tag [Fonte: nome_do_arquivo] fornecida."
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
        "resposta": resposta_llm.strip(),
        "fontes": list(fontes_unicas.values())
    }

def responder_pergunta(pergunta: str, categoria: str | None = None) -> dict:
    logger.info(f"Iniciando processo de resposta para a pergunta: '{pergunta}'")

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

    logger.info("Formatando resposta final e consolidando fontes.")
    resultado_estruturado = formatar_resposta_final(resposta_llm, chunks_relevantes)

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