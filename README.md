# Tyche Pay — Agente de IA Corporativo (Challenge Alura Agentes)

Agente de inteligência artificial corporativo, construído sobre uma arquitetura **RAG (Retrieval-Augmented Generation)**, capaz de responder perguntas de colaboradores com base em documentos internos da **Tyche Pay** — uma fintech fictícia criada para este desafio.

O agente é acessível por uma interface de chat web simples, cita as fontes usadas em cada resposta e recusa-se a inventar informações que não estejam nos documentos.

---

## Sobre o projeto

Este projeto foi desenvolvido como parte do desafio **Alura Agentes** e segue a arquitetura de um pipeline RAG para documentos internos corporativos.

Os principais passos do fluxo atual são:

1. **Coleta e organização de documentos** — arquivos corporativos em `Docs/` com categorização por área.
2. **Processamento e extração de conteúdo** — extração, limpeza e chunking em `src/ingestion/`.
3. **Indexação vetorial** — geração de embeddings e armazenamento em `src/indexing/` e `chroma_db/`.
4. **Camada de recuperação (RAG)** — busca semântica, reranking e montagem do contexto em `src/retrieval/`.
5. **Geração e validação de respostas** — prompt estruturado e LLM em `src/generation/llm/`.
6. **Interface e manutenção** — API e chat web em `src/app/`, além da documentação em `Manutencao.md`.

---

## Empresa fictícia: Tyche Pay

Fintech de pagamentos digitais fictícia, criada para este desafio. Os documentos internos cobrem categorias como Financeiro, Legal e Compliance, RH, Operacional, Dados e Sistemas, Comunicação Interna, Estratégico e Qualidade — todos listados e categorizados na planilha de mapeamento (Etapa 1).

---

## Arquitetura do pipeline

```text
Documentos em Docs/
        │
        ▼
src/ingestion/
  - extractor.py
  - cleaning.py
  - chunking.py
  - metadata.py
  - main.py
        │
        ▼
saida/chunks.json
        │
        ▼
src/indexing/
  - embeddings.py
  - vector_store.py
  - indexer.py
        │
        ▼
chroma_db/
        │
        ▼
src/retrieval/
  - retrieval.py
  - reranker.py
  - generator.py
        │
        ▼
src/generation/llm/llm.py
        │
        ▼
src/app/app.py
        │
        ▼
Interface web + histórico + feedback
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

```text
Challenge-AgenteIA-da-alura/
├── Docs/
│   ├── comunicacao-interna/
│   ├── dados-e-sistemas/
│   ├── Estrategico/
│   ├── financeiro/
│   ├── Legal-e-compliance/
│   ├── Operational/
│   ├── Qualidade/
│   └── RH/
├── src/
│   ├── app/
│   │   ├── app.py
│   │   ├── conversation.py
│   │   ├── feedback.py
│   │   └── static/
│   │       ├── index.html
│   │       ├── style.css
│   │       └── main.js
│   ├── generation/
│   │   └── llm/
│   │       └── llm.py
│   ├── ingestion/
│   │   ├── cleaning.py
│   │   ├── chunking.py
│   │   ├── extractor.py
│   │   ├── main.py
│   │   └── metadata.py
│   ├── indexing/
│   │   ├── embeddings.py
│   │   ├── indexer.py
│   │   └── vector_store.py
│   └── retrieval/
│       ├── generator.py
│       ├── reranker.py
│       └── retrieval.py
├── tests/
│   └── smoke/
│       └── teste_busca.py
├── chroma_db/
├── conversas/
├── feedback/
├── saida/
├── .env.example
├── .gitignore
├── Dockerfile
├── Manutencao.md
├── README.md
├── requirements.txt
├── Tyche_Pay_Mapeamento_de_Documentos.xlsx
└── .env
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

Copie o arquivo de exemplo:

```bash
copy .env.example .env
```

No Linux/macOS:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com as chaves reais:

```env
GROQ_API_KEY=sua_chave_groq
COHERE_API_KEY=sua_chave_cohere
```

### 4. Processar os documentos

```bash
python src/ingestion/main.py
```

Isso gera os chunks em `saida/chunks.json`.

### 5. Indexar os chunks no banco vetorial

```bash
python src/indexing/indexer.py
```

### 6. Rodar a interface web

```bash
uvicorn src.app.app:app --reload
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

O processo de atualização de documentos, curadoria de conteúdo, monitoramento de qualidade e ciclo de melhoria está documentado em [Manutencao.md](Manutencao.md).

---

## Requisitos do desafio

- [X] Múltiplos formatos de documento suportados (PDF nativo/escaneado, com extensibilidade para Word, Excel, CSV)
- [X] Cobertura de diferentes domínios organizacionais (RH, Financeiro, Legal, Operacional, Dados e Sistemas, Comunicação Interna, Estratégico, Qualidade)
- [X] Repositório público no GitHub
- [X] Deploy na Oracle Cloud Infrastructure (OCI)
- [X] Imagem/vídeo do agente em execução na nuvem (neste README)
