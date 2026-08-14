import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.retrieval.generator import responder_pergunta
from src.app.feedback import registrar_feedback

from src.app.conversation import criar_conversa, adicionar_mensagem, listar_conversas, carregar_conversa

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Tyche Pay - Agente de IA Corporativo")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

class PerguntaRequest(BaseModel):
    pergunta: str
    categoria: str | None = None
    id_conversa: str | None = None

class NovaConversaRequest(BaseModel):
    primeira_pergunta: str
class FeedbackRequest(BaseModel):
    pergunta: str
    resposta: str
    avaliacao: str
    fontes: list[dict]

@app.get("/")
def servir_pagina_inicial():
    caminho_html = STATIC_DIR / "index.html"
    if not caminho_html.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Página index.html não encontrada na pasta static."
        )
    return FileResponse(caminho_html)

@app.post("/api/perguntar")
def perguntar(request: PerguntaRequest):
    logger.info(f"Pergunta recebida: '{request.pergunta}' | Categoria: {request.categoria} | Conversa: {request.id_conversa}")

    try:
        resultado = responder_pergunta(request.pergunta, request.categoria)
        if request.id_conversa:
            try:
                adicionar_mensagem(request.id_conversa, "usuario", request.pergunta)
                adicionar_mensagem(
                    request.id_conversa,
                    "agente",
                    resultado.get("resposta", ""),
                    resultado.get("fontes", []),
                )
                logger.info(f"Mensagens adicionadas à conversa {request.id_conversa}")
            except Exception as history_err:
                logger.error(f"Erro ao salvar mensagens no histórico da conversa: {str(history_err)}")
        return resultado
    
    except Exception as e:
        logger.error(f"Erro no pipeline RAG: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de IA temporariamente indisponível. Tente novamente mais tarde."
        )

@app.post("/api/conversas")
def criar_nova_conversa(request: NovaConversaRequest):
    logger.info(f"Criando nova conversa a partir da pergunta: '{request.primeira_pergunta}'")
    try:
        id_gerado = criar_conversa(request.primeira_pergunta)
        return {"id": id_gerado}
    except Exception as e:
        logger.error(f"Erro ao criar nova conversa: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao criar sessão de conversa."
        )

@app.get("/api/conversas")
def obter_lista_conversas():
    logger.info("Listando todas as conversas ativas")
    try:
        return listar_conversas()
    except Exception as e:
        logger.error(f"Erro ao listar conversas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao recuperar lista de conversas."
        )

@app.get("/api/conversas/{id_conversa}")
def obter_conversa(id_conversa: str):
    logger.info(f"Carregando detalhes da conversa: {id_conversa}")
    try:
        conversa = carregar_conversa(id_conversa)
        if conversa is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversa com ID {id_conversa} não encontrada."
            )
        return conversa
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao carregar conversa {id_conversa}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao carregar dados da conversa."
        )

@app.post("/api/feedback")
def feedback(request: FeedbackRequest):
    logger.info(f"Feedback recebido para a pergunta: '{request.pergunta}'")

    try:
        registrar_feedback(
            request.pergunta, 
            request.resposta, 
            request.avaliacao, 
            request.fontes
        )

        return {"status": "ok"}
    except Exception as e:
        logger.warning(f"Falha não crítica ao registrar feedback: {str(e)}")

        return {"status": "erro_interno_silencioso"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)