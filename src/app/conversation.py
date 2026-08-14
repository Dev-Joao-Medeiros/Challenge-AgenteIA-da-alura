import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)
DIRETORIO_CONVERSAS = Path("conversas")

def _caminho_conversa(id_conversa:str) -> Path:
    return DIRETORIO_CONVERSAS / f"{id_conversa}.json"

def criar_conversa(primeira_pergunta: str) -> str:
    id_conversa = str(uuid.uuid4())
    titulo = primeira_pergunta[:40] + "..." if len(primeira_pergunta) > 40 else primeira_pergunta
    agora = datetime.now().isoformat()

    conversa = {
        "id": id_conversa,
        "titulo": titulo,
        "criado_em": agora,
        "atualizado_em": agora,
        "mensagens": []
    }

    DIRETORIO_CONVERSAS.mkdir(parents=True, exist_ok=True)
    caminho = _caminho_conversa(id_conversa)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(conversa, f, indent=4, ensure_ascii=False)
    return id_conversa

def adicionar_mensagem(
    id_conversa: str,
    papel: str,
    texto: str,
    fontes: list[dict] | None = None,
) -> None:
    conversa = carregar_conversa(id_conversa)

    if not conversa:
        logger.error(f"Tentativa de adicionar mensagem em conversa inexistente: {id_conversa}")
        raise FileNotFoundError(f"Conversa {id_conversa} não encontrada.")

    nova_mensagem = {
        "papel": papel,
        "texto": texto
    }

    if papel == "agente" and fontes is not None:
        nova_mensagem["fontes"] = fontes

    conversa["mensagens"].append(nova_mensagem)
    conversa["atualizado_em"] = datetime.now().isoformat()

    caminho = _caminho_conversa(id_conversa)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(conversa, f, indent=4, ensure_ascii=False)

def listar_conversas() -> list[dict]:
    if not DIRETORIO_CONVERSAS.exists():
        return []

    resumos = []

    for caminho_arquivo in DIRETORIO_CONVERSAS.glob("*.json"):
        try:
            with open(caminho_arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)

                resumo = {
                    "id": dados["id"],
                    "titulo": dados["titulo"],
                    "atualizado_em": dados["atualizado_em"]
                }
                resumos.append(resumo)

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Erro ao ler metadados do arquivo {caminho_arquivo}: {e}")
            continue

    return sorted(resumos, key=lambda c: c["atualizado_em"], reverse=True)

def carregar_conversa(id_conversa: str) -> dict | None:
    caminho = _caminho_conversa(id_conversa)

    if not caminho.exists():
        return None

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Arquivo de conversa corrompido ou JSON inválido ({id_conversa}): {e}")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado ao abrir a conversa ({id_conversa}): {e}")
        return None

