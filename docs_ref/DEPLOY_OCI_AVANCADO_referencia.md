# Deploy na OCI — Arquitetura Avançada (Compute + Object Storage)
## [Documento de referência — não implementado, apenas para entendimento]

Este é um guia de **como seria** uma versão mais robusta do deploy,
usando 2 serviços OCI em vez de 1 (Compute + Object Storage). Não é
necessário implementar isso para atender ao desafio — o guia
`DEPLOY_OCI.md` (só Compute) já satisfaz o requisito mínimo.

---

## O que muda conceitualmente

Na versão simples, os documentos (`Docs/`) e o índice vetorial
(`chroma_db/`) ficam **dentro da própria VM/imagem Docker** — se a VM
for destruída, tudo se perde, e qualquer atualização de documento exige
reconstruir e reenviar a imagem inteira.

Na versão avançada, os documentos **originais** ficam separados da
aplicação, no **OCI Object Storage** (equivalente ao S3 da AWS) — um
serviço de armazenamento de arquivos gerenciado, durável e independente
do ciclo de vida da VM. A aplicação passa a **baixar os documentos do
Object Storage** em vez de esperar que eles já estejam na imagem.

```
┌──────────────────────┐
│  OCI Object Storage  │  <- Docs/ originais (PDF, Word, Excel...)
│  (bucket: tyche-docs)│     e talvez o Tyche_Pay_Mapeamento.xlsx
└──────────┬───────────┘
           │ download via SDK/API na inicialização
           ▼
┌──────────────────────┐
│   OCI Compute (VM)   │  <- roda o container Docker
│   + Docker container │     (extractors, embeddings, RAG, API, chat)
└──────────┬───────────┘
           │
           ▼
     chroma_db/ local
     (regenerado no boot,
     ou também persistido
     em um Volume/Bucket)
```

---

## Passo 1 — Criar o bucket no Object Storage

1. Console OCI → **Storage → Object Storage → Buckets → Create Bucket**.
2. Nome: `tyche-pay-documentos`.
3. Deixe como **Standard** (não Archive, já que os documentos precisam
   ser lidos com frequência).
4. Visibilidade: **Private** (documentos internos não devem ser
   públicos) — o acesso será feito via credenciais da aplicação, não
   por URL pública.

## Passo 2 — Subir os documentos para o bucket

Via CLI da OCI (instalada localmente):

```bash
oci os object bulk-upload \
  --bucket-name tyche-pay-documentos \
  --src-dir ./Docs \
  --overwrite
```

Isso substitui o que hoje é só uma pasta local `Docs/` versionada no
Git — nessa arquitetura, o Git deixaria de ser a fonte de verdade dos
documentos, e o bucket passaria a ser.

## Passo 3 — Criar um usuário/política de IAM com acesso só-leitura ao bucket

Em vez de usar sua conta pessoal de administrador dentro da aplicação
(risco de segurança), cria-se um usuário técnico dedicado:

1. **Identity & Security → Users → Create User** (ex: `tyche-app-user`).
2. Gerar um **API Key** para esse usuário (Console → User Details →
   API Keys → Add API Key) — isso gera um arquivo de configuração e uma
   chave privada.
3. **Identity & Security → Policies → Create Policy**, com uma regra
   restringindo o acesso só ao bucket necessário, por exemplo:
   ```
   Allow group TycheAppGroup to read objects in compartment <seu-compartimento> where target.bucket.name='tyche-pay-documentos'
   ```

Isso segue o princípio de menor privilégio — a aplicação só pode *ler*
aquele bucket específico, nada mais.

## Passo 4 — Adaptar o código para baixar do Object Storage

Isso exigiria mudanças reais no projeto (ficaria como próximo passo se
você decidir seguir esse caminho):

- Adicionar a dependência `oci` (SDK Python oficial da Oracle) ao
  `requirements.txt`.
- Criar um módulo novo, por exemplo `object_storage.py`, com uma função
  `baixar_documentos(bucket_name, pasta_destino)` que lista os objetos
  do bucket e baixa cada um para `Docs/` localmente, antes de rodar
  `main.py`.
- No `Dockerfile` ou num script de inicialização do container,
  adicionar esse download como um passo antes de subir o Uvicorn — ex:
  `python baixar_documentos.py && python main.py && python indexer.py && uvicorn app:app ...`

Esse é o ponto onde a complexidade cresce de verdade: a etapa "processar
documentos" deixa de ser algo que você roda manualmente antes do deploy
e passa a fazer parte do processo de boot do próprio container.

## Passo 5 — Deploy da aplicação (igual à versão simples)

A partir daqui, os passos de Compute (criar VM, abrir porta, instalar
Docker, buildar e rodar a imagem) são os mesmos do `DEPLOY_OCI.md` —
com a diferença de que agora a VM também precisa ter as **credenciais
de API OCI** configuradas (arquivo `~/.oci/config` + chave privada),
para a aplicação conseguir autenticar no Object Storage.

---

## Trade-offs entre as duas versões

| Aspecto | Versão simples (Compute só) | Versão avançada (Compute + Object Storage) |
|---|---|---|
| Serviços OCI usados | 1 (Compute) | 2 (Compute + Object Storage) |
| Complexidade de setup | Baixa | Média-alta (IAM, políticas, SDK) |
| Atualizar um documento | Rebuild da imagem Docker inteira | Upload no bucket + reprocessar (sem rebuild de imagem) |
| Durabilidade dos documentos | Depende da VM/imagem | Independente da VM (bucket sobrevive a qualquer troca de VM) |
| Fonte de verdade dos documentos | Git (pasta `Docs/`) | Object Storage (Git deixaria de versionar os PDFs) |
| Adequado para este desafio? | Sim, plenamente | Sim, mas é esforço extra não exigido |

---

## Próximo nível (mencionado no enunciado, ainda mais além)

Se um dia você quisesse ir além até disso: trocar Compute por
**Container Instances** (roda o container sem gerenciar a VM
manualmente) ou **OKE** (Kubernetes, com escalonamento automático), e
mover o **Chroma** para o **Oracle Autonomous Database** (que suporta
busca vetorial nativa) em vez de um arquivo local `chroma_db/` — isso
desacoplaria completamente o banco vetorial do ciclo de vida da VM
também. Mas isso já é uma reformulação bem maior da arquitetura atual,
fora de escopo para este desafio.