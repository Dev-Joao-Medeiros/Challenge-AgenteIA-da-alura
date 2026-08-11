const API_BASE_URL = "";

const form = document.getElementById("form-pergunta");
const input = document.getElementById("input-pergunta");
const historico = document.getElementById("historico");
const listaConversas = document.getElementById("lista-conversas");
const btnNovaConversa = document.getElementById("btn-nova-conversa");
const chatWrapper = document.querySelector(".chat-wrapper");

let idConversaAtual = null;

// ---------- Inicialização ----------

carregarListaConversas();
atualizarEstadoVisualDaConversa();

btnNovaConversa.addEventListener("click", () => {
    idConversaAtual = null;
    historico.innerHTML = "";
    marcarConversaAtivaNaLista(null);
    atualizarEstadoVisualDaConversa();
    input.focus();
});

// ---------- Envio de pergunta ----------

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    const pergunta = input.value.trim();
    if (!pergunta) return;

    adicionarMensagemUsuario(pergunta);
    atualizarEstadoVisualDaConversa();
    input.value = "";
    input.disabled = true;

    const indicadorCarregando = adicionarIndicadorCarregando();

    try {
        if (!idConversaAtual) {
            idConversaAtual = await criarNovaConversa(pergunta);
            await carregarListaConversas();
            marcarConversaAtivaNaLista(idConversaAtual);
        }

        const resposta = await fetch(`${API_BASE_URL}/api/perguntar`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pergunta, id_conversa: idConversaAtual }),
        });

        if (!resposta.ok) {
            throw new Error(`Erro na API: ${resposta.status}`);
        }

        const dados = await resposta.json();
        indicadorCarregando.remove();
        adicionarMensagemAgente(pergunta, dados.resposta, dados.fontes || []);
        atualizarEstadoVisualDaConversa();
    } catch (erro) {
        indicadorCarregando.remove();
        adicionarMensagemAgente(
            pergunta,
            "Desculpe, ocorreu um erro ao processar sua pergunta. Tente novamente em instantes.",
            []
        );
        console.error(erro);
    } finally {
        input.disabled = false;
        input.focus();
    }
});

async function criarNovaConversa(pergunta) {
    try {
        const resultado = await fetch(`${API_BASE_URL}/api/conversas`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ primeira_pergunta: pergunta }),
        });
        const dados = await resultado.json();
        return dados.id;
    } catch (erro) {
        console.error("Erro ao criar conversa:", erro);
        throw erro;
    }
}

// ---------- Sidebar de conversas ----------

async function carregarListaConversas() {
    try {
        const resposta = await fetch(`${API_BASE_URL}/api/conversas`);
        const conversas = await resposta.json();

        listaConversas.innerHTML = "";

        if (conversas.length === 0) {
            listaConversas.innerHTML = '<div class="vazio">Nenhuma conversa salva ainda.</div>';
            return;
        }

        conversas.forEach((conversa) => {
            const item = document.createElement("div");
            item.className = "item-conversa";
            item.textContent = conversa.titulo;
            item.dataset.id = conversa.id;
            item.addEventListener("click", () => abrirConversa(conversa.id));
            listaConversas.appendChild(item);
        });

        marcarConversaAtivaNaLista(idConversaAtual);
    } catch (erro) {
        console.error("Erro ao carregar lista de conversas:", erro);
    }
}

function marcarConversaAtivaNaLista(id) {
    document.querySelectorAll(".item-conversa").forEach((el) => {
        el.classList.toggle("ativa", el.dataset.id === id);
    });
}

async function abrirConversa(id) {
    try {
        const resposta = await fetch(`${API_BASE_URL}/api/conversas/${id}`);
        if (!resposta.ok) throw new Error("Conversa não encontrada");

        const conversa = await resposta.json();
        idConversaAtual = id;
        historico.innerHTML = "";

        conversa.mensagens.forEach((msg) => {
            if (msg.papel === "usuario") {
                adicionarMensagemUsuario(msg.texto);
            } else {
                adicionarMensagemAgente(null, msg.texto, msg.fontes || []);
            }
        });

        marcarConversaAtivaNaLista(id);
        atualizarEstadoVisualDaConversa();
    } catch (erro) {
        console.error("Erro ao abrir conversa:", erro);
    }
}

// ---------- Renderização de mensagens ----------

function formatarMarkdownSimples(texto) {
    const escapado = texto
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    return escapado.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

function adicionarMensagemUsuario(texto) {
    const div = document.createElement("div");
    div.className = "mensagem usuario";
    div.textContent = texto;
    historico.appendChild(div);
    rolarParaBaixo();
}

function adicionarIndicadorCarregando() {
    const div = document.createElement("div");
    div.className = "carregando";
    div.textContent = "Consultando os documentos...";
    historico.appendChild(div);
    rolarParaBaixo();
    return div;
}

function adicionarMensagemAgente(pergunta, texto, fontes) {
    const container = document.createElement("div");
    container.className = "mensagem agente";

    const textoResposta = document.createElement("div");
    textoResposta.innerHTML = formatarMarkdownSimples(texto);
    container.appendChild(textoResposta);

    if (fontes.length > 0) {
        const blocoFontes = document.createElement("div");
        blocoFontes.className = "fontes";
        blocoFontes.innerHTML =
            "<strong>Fontes consultadas:</strong><ul>" +
            fontes.map((f) => `<li>${f.arquivo} (${f.categoria})</li>`).join("") +
            "</ul>";
        container.appendChild(blocoFontes);
    }

    // Feedback só faz sentido em mensagens recém-geradas (com a
    // pergunta original disponível); ao reabrir uma conversa salva,
    // omitimos os botões para simplificar.
    if (pergunta) {
        const blocoFeedback = document.createElement("div");
        blocoFeedback.className = "feedback";

        const botaoPositivo = document.createElement("button");
        botaoPositivo.textContent = "👍 Útil";
        const botaoNegativo = document.createElement("button");
        botaoNegativo.textContent = "👎 Não útil";

        const enviarFeedback = async (avaliacao, botaoClicado, botaoOutro) => {
            botaoClicado.classList.add("selecionado");
            botaoOutro.disabled = true;
            botaoClicado.disabled = true;

            try {
                await fetch(`${API_BASE_URL}/api/feedback`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ pergunta, resposta: texto, avaliacao, fontes }),
                });
            } catch (erro) {
                console.error("Erro ao enviar feedback:", erro);
            }
        };

        botaoPositivo.addEventListener("click", () =>
            enviarFeedback("positivo", botaoPositivo, botaoNegativo)
        );
        botaoNegativo.addEventListener("click", () =>
            enviarFeedback("negativo", botaoNegativo, botaoPositivo)
        );

        blocoFeedback.appendChild(botaoPositivo);
        blocoFeedback.appendChild(botaoNegativo);
        container.appendChild(blocoFeedback);
    }

    historico.appendChild(container);
    rolarParaBaixo();
}

function rolarParaBaixo() {
    historico.scrollTop = historico.scrollHeight;
}

function atualizarEstadoVisualDaConversa() {
    chatWrapper.classList.toggle("tem-mensagens", historico.children.length > 0);
}