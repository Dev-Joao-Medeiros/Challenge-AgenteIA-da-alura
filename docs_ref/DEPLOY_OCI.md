# Deploy na OCI — Guia Passo a Passo (OCI Compute + Docker)

Este guia sobe o agente Tyche Pay numa única VM do **OCI Compute**
(Always Free), rodando o projeto inteiro dentro de um container Docker.
É a arquitetura mais simples que ainda satisfaz o requisito do desafio
de usar pelo menos 1 serviço OCI.

---

## Passo 0 — Preparar o projeto localmente (antes de qualquer coisa na OCI)

Na sua máquina, com o `.env` preenchido:

```bash
python main.py       # gera saida/chunks.json
python indexer.py    # gera chroma_db/
```

Confirme que as pastas `saida/` e `chroma_db/` existem e estão
preenchidas antes de continuar — elas vão dentro da imagem Docker.

---

## Passo 1 — Criar a instância de Compute na OCI

1. No Console OCI, vá em **Compute → Instances → Create Instance**.
2. Nome: `tyche-pay-agente` (ou o que preferir).
3. **Imagem**: Canonical Ubuntu 22.04 (ou a mais recente disponível).
4. **Shape**: se estiver no Always Free, use `VM.Standard.A1.Flex`
   (ARM, gratuito) ou `VM.Standard.E2.1.Micro` (x86, gratuito) —
   confirme qual está disponível na sua conta.
5. Em **Networking**, use a VCN padrão (ou crie uma nova com
   configuração automática) e marque **"Assign a public IPv4 address"**.
6. Em **Add SSH keys**, cole sua chave pública SSH (ou gere uma nova e
   baixe a privada — vai precisar dela para conectar).
7. Clique em **Create**.

---

## Passo 2 — Abrir a porta 8000 no firewall da OCI

Por padrão, a OCI só libera a porta 22 (SSH). Você precisa liberar a
porta 8000 (ou 80, se preferir mapear depois) para acessar o chat.

1. Na página da instância criada, clique na **VCN** associada.
2. Vá em **Security Lists** → clique na lista padrão (Default Security List).
3. Em **Ingress Rules**, clique em **Add Ingress Rules**:
   - Source CIDR: `0.0.0.0/0`
   - IP Protocol: TCP
   - Destination Port Range: `8000`
4. Salve.

---

## Passo 3 — Conectar na VM via SSH

```bash
ssh -i /caminho/para/sua-chave-privada.key ubuntu@<IP_PUBLICO_DA_INSTANCIA>
```

(O usuário padrão é `ubuntu` para imagens Canonical Ubuntu.)

---

## Passo 4 — Instalar o Docker na VM

```bash
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

Depois do último comando, saia (`exit`) e conecte via SSH de novo, para
o grupo `docker` ser aplicado ao seu usuário.

---

## Passo 5 — Levar o projeto para a VM

Opção mais simples: clonar direto do GitHub (já que o repositório é
público, conforme requisito do desafio):

```bash
git clone <url-do-seu-repositorio>
cd Challenge-AgenteIA-da-alura
```

> Atenção: como `chroma_db/`, `saida/chunks.json`, etc. estão no
> `.gitignore`, eles **não vêm** do `git clone`. Duas opções:
> 1. Rodar `python main.py` e `python indexer.py` também na VM (exige
>    instalar Python + Tesseract + Poppler na VM antes do Docker, ou
>    rodar isso depois dentro do próprio container).
> 2. Copiar as pastas já geradas localmente para a VM via `scp`, antes
>    de buildar a imagem:
>    ```bash
>    scp -i sua-chave.key -r saida chroma_db ubuntu@<IP>:~/Challenge-AgenteIA-da-alura/
>    ```
>    (Rode este comando a partir da sua máquina local, não da VM.)

---

## Passo 6 — Criar o arquivo `.env` na VM

```bash
nano .env
```

Cole (com suas chaves reais):
```
COHERE_API_KEY=sua_chave_aqui
GROQ_API_KEY=sua_chave_aqui
```

Salve e feche (`Ctrl+O`, `Enter`, `Ctrl+X` no nano).

> Este `.env` não vai para dentro da imagem Docker (está no
> `.dockerignore`) — ele é passado para o container em tempo de
> execução, no próximo passo.

---

## Passo 7 — Buildar e rodar o container

```bash
docker build -t tyche-pay-agente .

docker run -d \
  --name tyche-pay-agente \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  tyche-pay-agente
```

- `-d`: roda em segundo plano.
- `--restart unless-stopped`: reinicia automaticamente se a VM reiniciar
  ou o container cair.
- `--env-file .env`: injeta as variáveis de ambiente sem colocá-las
  dentro da imagem.

---

## Passo 8 — Acessar o agente

No navegador:
```
http://<IP_PUBLICO_DA_INSTANCIA>:8000
```

---

## Verificações úteis

```bash
docker logs -f tyche-pay-agente     # ver logs em tempo real
docker ps                            # confirmar que o container está rodando
```

---

## Atualizando o agente depois de uma mudança

```bash
git pull
docker build -t tyche-pay-agente .
docker stop tyche-pay-agente
docker rm tyche-pay-agente
docker run -d --name tyche-pay-agente --restart unless-stopped -p 8000:8000 --env-file .env tyche-pay-agente
```

---

## Serviço OCI utilizado

Este deploy usa o **OCI Compute** (instância de máquina virtual) como o
serviço OCI obrigatório do desafio. A VCN e a Security List também são
provisionadas automaticamente como parte da criação da instância.