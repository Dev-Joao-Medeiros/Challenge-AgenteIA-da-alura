
# Manutenção Contínua — Agente Tyche Pay

Este documento descreve os processos que mantêm o agente confiável e
atualizado depois do lançamento, conforme a Etapa 6 do desafio.

---

## 1. Pipeline de atualização de documentos

**Situação atual (manual):**
Hoje, quando um documento é criado, alterado ou removido em `Docs/`, o
processo de atualização é:

1. Atualizar a planilha de mapeamento (`Tyche_Pay_Mapeamento_de_Documentos.xlsx`)
   com os metadados do documento novo/alterado.
2. Rodar `python main.py` (Etapa 2) — reprocessa todos os documentos e
   regenera `saida/chunks.json`.
3. Apagar a pasta `chroma_db/` e rodar `python indexer.py` (Etapa 3) —
   reindexação completa, evitando ids órfãos de chunking antigo.

**Evolução recomendada (automatizada):**

- Rotina agendada (ex: `cron` no servidor, ou um agendador da própria
  OCI) rodando diariamente ou semanalmente, executando os passos acima
  automaticamente.
- Alternativa mais reativa: um *watcher* de sistema de arquivos (ex:
  biblioteca `watchdog` em Python) que detecta mudanças em `Docs/` e
  dispara o reprocessamento apenas do arquivo alterado, em vez de tudo.
- Se os documentos migrarem para uma fonte externa (Google Drive,
  SharePoint, conforme discutido na Etapa 1), o pipeline passaria a
  consultar a API dessa fonte por mudanças, em vez de depender de
  upload manual na pasta local.

---

## 2. Curadoria de conteúdo

Cada categoria de documento tem um responsável definido na planilha de
mapeamento (coluna "Responsável Sugerido"), que deve revisar
periodicamente se os documentos indexados continuam sendo a versão
oficial vigente:

| Categoria              | Responsável                 |
| ---------------------- | ---------------------------- |
| Estratégico           | Helena Ramos (CEO)           |
| Financeiro e Contábil | Mariana Costa (CFO)          |
| Legal e Compliance     | Rodrigo Andrade (CCO)        |
| Recursos Humanos       | RH (owner nominal a definir) |
| Operacional            | Gabriel Mendonça (COO/CXO)  |
| Dados e Sistemas       | Lucas Siqueira (CTO)         |
| Qualidade              | Gabriel Mendonça (COO/CXO)  |
| Comunicação Interna  | RH / Comunicação Interna   |

**Processo sugerido**: revisão trimestral, ou sempre que uma política
oficial for atualizada — o responsável confirma se o documento na base
ainda é a versão vigente e, se não for, aciona o pipeline de atualização
(seção 1) com a versão nova.

---

## 3. Monitoramento de qualidade

O módulo `feedback.py` já registra, para cada resposta:

- A pergunta feita.
- A resposta gerada.
- A avaliação do colaborador (positivo/negativo).
- As fontes citadas.

**Métricas a acompanhar** (via `feedback.calcular_metricas_basicas()`,
ou evoluções futuras dessa função):

- **Taxa de feedback negativo** — sinaliza respostas de baixa qualidade.
- **Taxa de perguntas sem resposta** (fallback disparado) — sinaliza
  lacunas na base de documentos.
- **Tempo de resposta** — não implementado ainda; pode ser adicionado
  medindo o tempo entre o recebimento da pergunta e a resposta final em
  `app.py`, e incluído no registro de feedback ou em um log separado.

**Frequência sugerida**: revisão semanal das métricas nas primeiras
semanas após o lançamento (para captar problemas cedo), passando para
revisão mensal depois que o agente estabilizar.

---

## 4. Ciclo de melhoria

- **Perguntas recorrentes sem boa resposta** (identificáveis analisando
  o arquivo `feedback/feedback.jsonl`, agrupando perguntas semelhantes
  com feedback negativo) indicam a necessidade de:
  - Adicionar um novo documento à base (ex: se várias perguntas sobre
    um assunto não coberto aparecerem repetidamente).
  - Ou revisar se um documento existente está desatualizado/incompleto.
- **Respostas mal avaliadas mesmo com contexto correto recuperado**
  podem indicar necessidade de ajuste no **prompt** (`generator.py` →
  `montar_prompt()`) — por exemplo, instruções mais claras sobre
  formato de resposta.
- **Respostas mal avaliadas por contexto irrelevante recuperado** podem
  indicar necessidade de ajuste na **lógica de recuperação**
  (`retrieval.py`) — por exemplo, recalibrar `LIMITE_MINIMO_RELEVANCIA`
  (hoje calibrado em `0.05`, com base em testes manuais — ver histórico
  de decisões do projeto) ou `TOP_K_BUSCA_INICIAL`.

---

## 5. Atualização do modelo

- **LLM (Groq)**: modelos hospedados no Groq têm ciclo de vida curto e
  são descontinuados com relativa frequência (já aconteceu durante o
  desenvolvimento deste projeto — ver `llm.py`, constante `MODELO_LLM`).
  Processo recomendado:
  1. Verificar periodicamente `https://console.groq.com/docs/deprecations`
     ou o endpoint `https://api.groq.com/openai/v1/models`.
  2. Antes de trocar o modelo em produção, testar o novo modelo com o
     mesmo conjunto de perguntas de calibração usado no desenvolvimento
     (ver exemplos no histórico do projeto: perguntas sobre reembolso,
     onboarding, boletos, contatos).
  3. Comparar qualidade e formato das respostas antes de substituir
     definitivamente `MODELO_LLM`.
- **Embedding e Reranker (Cohere)**: o mesmo cuidado se aplica, com uma
  ressalva importante: se o modelo de **embedding** for trocado, **toda
  a base precisa ser reindexada** (apagar `chroma_db/` e rodar
  `indexer.py` novamente) — vetores gerados por modelos diferentes não
  são comparáveis entre si, como já discutido nas Etapas 3 e 4.

---

## Resumo de comandos úteis

```bash
# Reprocessar documentos após mudança em Docs/ ou na planilha
python main.py

# Reindexar do zero (apagar chroma_db/ antes)
python indexer.py

# Rodar a interface web localmente
uvicorn app:app --reload

# Consultar métricas básicas de feedback (via Python)
python -c "from feedback import calcular_metricas_basicas; print(calcular_metricas_basicas())"
```
