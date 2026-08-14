# Tyche Pay — Agente de IA Corporativo (Challenge Alura Agentes)

<img width="1408" height="768" alt="Gemini_Generated_Image_" src="https://github.com/user-attachments/assets/3642e1f4-e4a9-43e6-9407-ba26215b7c07" />

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
├── docs_ref/
│   ├── DEPLOY_OCI.md
│   ├── DEPLOY_OCI_AVANCADO_referencia.md
│   └── Manutencao.md
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
├── chroma_db/            (gerado localmente, não versionado)
├── conversas/             (gerado em runtime, não versionado)
├── feedback/              (gerado em runtime, não versionado)
├── saida/                 (gerado localmente, não versionado)
├── .env.example
├── .gitignore
├── Dockerfile
├── Manutencao.md
├── README.md
├── requirements.txt
└── Tyche_Pay_Mapeamento_de_Documentos.xlsx
```

> O arquivo `.env` (com as chaves reais de API) não é versionado — veja `.env.example` para o formato esperado, e a seção [Como rodar localmente](#como-rodar-localmente) para instruções de configuração.

---

## Como rodar localmente

### Pré-requisitos de sistema

- Python 3.11+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) instalado (necessário para `pytesseract`, usado em PDFs escaneados)
- [Poppler](https://poppler.freedesktop.org/) instalado (necessário para `pdf2image`)

### 1. Clonar o repositório e criar o ambiente virtual

```bash
git clone https://github.com/Dev-Joao-Medeiros/Challenge-AgenteIA-da-alura.git
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

## Projeto rodando na OCI:

- Acesse [Tyche Pay](http://147.15.86.59:8000/) para acessar o Agente de IA da Tyche Pay que está hospedado na OCI (Oracle Cloud Infrastructure)

<div style="display: flex; gap: 10px;">
  <img src="https://github.com/user-attachments/assets/e6b18884-67fb-46bc-ac32-e97319825c3e" width="45%" alt="tela-inicial" />
  <img src="https://github.com/user-attachments/assets/e5984916-18c1-41c4-9191-c1cb0bb1f63b" width="45%" alt="conversa" />
</div>

## Vídeo do projeto funcionando

[Vídeo Tyche Pay](https://drive.google.com/file/d/161Mraa9WyyG0bqy0KVHeLIReZNYCJt57/view?usp=drive_link)

## Arquitetura de deploy na OCI
 
O deploy foi feito na abordagem mais simples possível dentre as sugeridas
pelo desafio — uma única instância de Compute rodando a aplicação
containerizada — o suficiente para satisfazer o requisito de usar pelo
menos um serviço do ecossistema OCI, mantendo a operação e o custo
(zero, dentro do Always Free Tier) simples.
 
### Serviço OCI utilizado
 
- **OCI Compute** — instância de máquina virtual (`VM.Standard.E2.1.Micro`,
  Always Free Tier) responsável por executar o container Docker com toda
  a aplicação: pipeline de RAG, API (FastAPI) e interface web.
### Recursos de rede criados (provisionados junto com a instância)
 
- **VCN (Virtual Cloud Network)** dedicada ao projeto (`vcn-tyche-pay-agente`).
- **Subnet pública** (`subnet-tyche-pay-agente`, CIDR `10.0.1.0/24`),
  com atribuição automática de IP público à instância.
- **Internet Gateway**, associado à Route Table da subnet (rota
  `0.0.0.0/0` → Internet Gateway), permitindo tráfego de entrada/saída
  da instância para a internet.
- **Security List** com regras de entrada (*ingress*) liberando:
  - Porta `22` (TCP) — acesso SSH para administração da instância.
  - Porta `8000` (TCP) — porta em que a aplicação (Uvicorn) escuta,
    exposta publicamente para acesso ao chat.

### Diagrama simplificado
 
```text
                     Internet
                        │
                        ▼
              ┌───────────────────────┐
              │  Internet Gateway     │
              └──────────┬────────────┘
                         │
              ┌──────────▼────────────────┐
              │   VCN (10.0.1.0/24)       │
              │  ┌─────────────────────┐  │
              │  │   Subnet pública    │  │
              │  │  ┌────────────────┐ │  │
              │  │  │ OCI Compute    │ │  │
              │  │  │ (E2.1.Micro)   │ │  │
              │  │  │                │ │  │
              │  │  │  Docker        │ │  │
              │  │  │  ├─ FastAPI    │ │  │
              │  │  │  ├─ RAG        │ │  │
              │  │  │  ├─ ChromaDB   │ │  │
              │  │  │  └─ Interface  │ │  │
              │  │  │    (porta 8000)│ │  │
              │  │  └────────────────┘ │  │
              │  └─────────────────────┘  │
              └───────────────────────────┘
                Security List: 22, 8000
```
 
### Como a aplicação chega até a instância
 
Os documentos processados (`saida/chunks.json`) e o índice vetorial
(`chroma_db/`) são gerados **localmente** antes do deploy e embarcados
diretamente na imagem Docker construída na própria instância — não há,
nesta versão, um serviço de armazenamento externo (como o OCI Object
Storage) hospedando os documentos originais. Essa é uma simplificação
deliberada; o passo a passo completo, incluindo uma alternativa mais
robusta com Object Storage e IAM, está descrito nos documentos
`DEPLOY_OCI.md` e `DEPLOY_OCI_AVANCADO_referencia.md` do projeto.
 
### Segredos e credenciais
 
As chaves de API (`GROQ_API_KEY`, `COHERE_API_KEY`) são passadas ao
container em tempo de execução via `--env-file .env` no `docker run`,
não ficam embutidas na imagem Docker. O uso do **OCI Vault** para
gerenciamento centralizado de segredos, sugerido pelo desafio, não foi
implementado nesta versão — é um próximo passo natural caso o projeto
evolua para múltiplos ambientes ou precise de rotação de credenciais.
 
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
