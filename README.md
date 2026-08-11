# Tyche Pay — Agente de IA Corporativo (Challenge Alura Agentes)

Agente de inteligência artificial corporativo, construído sobre uma arquitetura **RAG (Retrieval-Augmented Generation)**, capaz de responder perguntas de colaboradores com base em documentos internos da **Tyche Pay** — uma fintech fictícia criada para este desafio.

O agente é acessível por uma interface de chat web simples, cita as fontes usadas em cada resposta e recusa-se a inventar informações que não estejam nos documentos.

---

## Sobre o projeto

Este projeto foi desenvolvido como parte do desafio **Alura Agentes**, seguindo as seis etapas propostas:

1. **Coleta e organização de documentos** — mapeamento de fontes, categorização e definição de responsáveis (ver planilha `Tyche_Pay_Mapeamento_de_Documentos.xlsx`).
2. **Processamento e extração de conteúdo** — extração de texto, limpeza e divisão em chunks (`extractors.py`, `cleaning.py`, `chunking.py`, `metadata.py`, `main.py`).
3. **Indexação vetorial** — geração de embeddings e armazenamento em banco vetorial (`embeddings.py`, `vector_store.py`, `indexer.py`).
4. **Camada de recuperação (RAG)** — busca semântica, filtro por metadados e reranqueamento (`retrieval.py`, `reranker.py`).
5. **Geração e validação de respostas** — prompt estruturado, citação de fontes e fallback contra alucinação (`generator.py`, `llm.py`).
6. **Implantação, interface e manutenção** — chat web, histórico de conversas, feedback e processos de manutenção contínua (`app.py`, `static/`, `feedback.py`, `conversation.py`, [`MANUTENCAO.md`](MANUTENCAO.md)).

---

## Empresa fictícia: Tyche Pay

Fintech de pagamentos digitais fictícia, criada para este desafio. Os documentos internos cobrem categorias como Financeiro, Legal e Compliance, RH, Operacional, Dados e Sistemas, Comunicação Interna, Estratégico e Qualidade — todos listados e categorizados na planilha de mapeamento (Etapa 1).

---

## Arquitetura do pipeline

```
Documentos (Docs/)
      │
      ▼
Etapa 2 — Extração, limpeza e chunking (main.py)
      │
      ▼
saida/chunks.json
      │
      ▼
Etapa 3 — Embeddings (Cohere) + indexação (indexer.py)
      │
      ▼
chroma_db/ (banco vetorial)
      │
      ▼
Etapa 4 — Busca vetorial + rerank + filtro de relevância (retrieval.py)
      │
      ▼
Etapa 5 — Prompt + LLM (Groq) + validação anti-alucinação (generator.py)
      │
      ▼
Etapa 6 — Interface web (app.py + static/)
```

---

## Tecnologias utilizadas

| Camada                       | Tecnologia                                                         |
| ---------------------------- | ------------------------------------------------------------------ |
| Extração de PDF            | PyMuPDF (fitz), pypdf, pdf2image + pytesseract (OCR)               |
| Extração de Word/Excel/CSV | python-docx, pandas, openpyxl                                      |
| Embeddings e Reranking       | Cohere (`embed-multilingual-v3.0`, `rerank-multilingual-v3.0`) |
| Banco vetorial               | ChromaDB (persistente, local)                                      |
| LLM (geração de resposta)  | Groq (`openai/gpt-oss-120b`)                                     |
| Backend / API                | FastAPI + Uvicorn                                                  |
| Frontend                     | HTML, CSS e JavaScript puros (sem framework)                       |

---

## Estrutura do projeto

```
Challenge-AgenteIA-da-alura/
├── Docs/                          # Documentos internos da Tyche Pay (fonte de verdade)
├── saida/
│   └── chunks.json                # Saída da Etapa 2 (versionado)
├── chroma_db/                     # Banco vetorial (gerado, gitignored)
├── conversas/                     # Conversas salvas (geradas, gitignored)
├── feedback/                      # Feedback dos colaboradores (gerado)
├── static/                        # Frontend do chat
│   ├── index.html
│   ├── style.css
│   └── main.js
├── extractors.py                  # Etapa 2
├── cleaning.py                    # Etapa 2
├── chunking.py                    # Etapa 2
├── metadata.py                    # Etapa 2
├── main.py                        # Etapa 2 (orquestrador)
├── embeddings.py                  # Etapa 3
├── vector_store.py                # Etapa 3
├── indexer.py                     # Etapa 3 (orquestrador)
├── reranker.py                    # Etapa 4
├── retrieval.py                   # Etapa 4 (orquestrador)
├── llm.py                         # Etapa 5
├── generator.py                   # Etapa 5 (orquestrador)
├── app.py                         # Etapa 6 (backend web)
├── feedback.py                    # Etapa 6
├── conversation.py                # Etapa 6
├── requirements.txt
├── Tyche_Pay_Mapeamento_de_Documentos.xlsx   # Etapa 1
├── MANUTENCAO.md                  # Etapa 6 (manutenção contínua)
└── README.md
```

---

## Como rodar localmente

### Pré-requisitos de sistema

- Python 3.11+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) instalado (necessário para `pytesseract`, usado em PDFs escaneados)
- [Poppler](https://poppler.freedesktop.org/) instalado (necessário para `pdf2image`)

### 1. Clonar o repositório e criar o ambiente virtual

```bash
git clone <url-do-repositorio>
cd Challenge-AgenteIA-da-alura

python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```
COHERE_API_KEY=sua_chave_aqui
GROQ_API_KEY=sua_chave_aqui
```

### 4. Processar os documentos e gerar o índice vetorial

```bash
python main.py       # Etapa 2 — gera saida/chunks.json
python indexer.py    # Etapa 3 — gera chroma_db/
```

> Sempre que um documento em `Docs/` for adicionado, alterado ou removido, repita esses dois passos. Veja o processo completo em [MANUTENCAO.md](MANUTENCAO.md).

### 5. Rodar a interface web

```bash
uvicorn app:app --reload
```

Acesse **http://localhost:8000** no navegador.

---

## Funcionalidades da interface

- Chat web simples, com indicação clara de que se trata de um agente de IA.
- Exibição das fontes (documento + categoria) usadas em cada resposta.
- Botões de feedback (👍/👎) por resposta.
- Histórico de conversas com sidebar — permite criar novas conversas e reabrir conversas anteriores.
- Fallback explícito quando a pergunta não tem resposta na base de documentos, evitando respostas inventadas.

> **Limitação conhecida:** como o projeto não implementa autenticação de usuários, o histórico de conversas é global (visível a qualquer pessoa que acesse a interface), não individual por colaborador.

---

## Manutenção contínua

O processo de atualização de documentos, curadoria de conteúdo, monitoramento de qualidade e ciclo de melhoria está documentado em [MANUTENCAO.md](MANUTENCAO.md).

---

## Requisitos do desafio

- [X] Múltiplos formatos de documento suportados (PDF nativo/escaneado, com extensibilidade para Word, Excel, CSV)
- [X] Cobertura de diferentes domínios organizacionais (RH, Financeiro, Legal, Operacional, Dados e Sistemas, Comunicação Interna, Estratégico, Qualidade)
- [X] Repositório público no GitHub
- [ ] Deploy na Oracle Cloud Infrastructure (OCI)
- [ ] Imagem/vídeo do agente em execução na nuvem (neste README)
