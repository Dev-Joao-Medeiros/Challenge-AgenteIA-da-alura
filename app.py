import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from generator import responder_pergunta
from feedback import registrar_feedback

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Tyche Pay - Agente de IA Corporativo")

STATIC_DIR = Path("static")
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

class PerguntaRequest(BaseModel):
    pergunta: str
    categoria: str | None = None

class feedbackRequest(BaseModel):
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
    logger.info(f"Pergunta recebida: '{request.pergunta}' | Categoria: {request.categoria}")

    try:
        resultado = responder_pergunta(request.pergunta, request.categoria)
        return resultado
    except Exception as e:
        logger.error(f"Erro no pipeline RAG: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de IA temporariamente indisponível. Tente novamente mais tarde."
        )

@app.post("/api/feedback")
def feedback(request: feedbackRequest):
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