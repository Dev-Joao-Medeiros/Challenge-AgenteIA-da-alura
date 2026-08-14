import json 
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

CAMINHO_ARQUIVO_FEEDBACK = "feedback/feedback.jsonl"


def registrar_feedback(
        pergunta: str,
        resposta: str,
        avaliacao: str,
        fontes: list[dict]
) -> None:
    avaliacao_limpa = avaliacao.strip().lower()
    if avaliacao_limpa not in ["positivo", "negativo"]:
        logger.warning(f"Avaliação inválida recebida: '{avaliacao}'. Registro abortado.")
        return

    registro = {
        "timestamp": datetime.now().isoformat(),
        "pergunta": pergunta,
        "resposta": resposta,
        "avaliacao": avaliacao_limpa,
        "fontes": fontes
    }

    try:
        caminho = Path(CAMINHO_ARQUIVO_FEEDBACK)
        caminho.parent.mkdir(parents=True, exist_ok=True)

        with open(caminho, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")

        logger.info("Feedback registrado com sucesso.")

    except Exception as e:
        logger.error(f"Erro ao salvar feedback em disco: {e}")

def calcular_metricas_basicas() -> dict:
    metricas = {
        "total_feedbacks": 0,
        "positivos": 0,
        "negativos": 0,
        "taxa_negativo_percentual": 0.0
    }

    caminho = Path(CAMINHO_ARQUIVO_FEEDBACK)
    if not caminho.exists():
        logger.info("Arquivo de feedback ainda não existe. Retornando métricas zeradas.")
        return metricas

    try: 
        with open(caminho, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue

                registro = json.loads(linha)
                metricas["total_feedbacks"] += 1

                if registro.get("avaliacao") == "positivo":
                    metricas["positivos"] += 1
                elif registro.get("avaliacao") == "negativo":
                    metricas["negativos"] += 1

        total = metricas["total_feedbacks"]
        if total > 0:
            taxa = (metricas["negativos"] / total) * 100
            metricas["taxa_negativo_percentual"] = round(taxa, 2)

        return metricas

    except Exception as e:
        logger.error(f"Erro ao calcular métricas de feedback: {e}")
        return metricas