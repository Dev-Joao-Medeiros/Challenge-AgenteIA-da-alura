const API_BASE_URL = "";

const form = document.getElementById("form-pergunta");
const input = document.getElementById("input-pergunta");
const historico = document.getElementById("historico");
const chatWrapper = document.getElementById("chat-wrapper"); // Referência adicionada

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    const pergunta = input.value.trim();
    if (!pergunta) return;

    // Transição: Remove a tela de boas-vindas e move o título para o topo
    if (chatWrapper.classList.contains("novo-chat")) {
        chatWrapper.classList.remove("novo-chat");
    }

    adicionarMensagemUsuario(pergunta);
    input.value = "";
    input.disabled = true;

    const indicadorCarregando = adicionarIndicadorCarregando();

    try {
        const resposta = await fetch(`${API_BASE_URL}/api/perguntar`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pergunta }),
        });

        if (!resposta.ok) {
            throw new Error(`Erro na API: ${resposta.status}`);
        }

        const dados = await resposta.json();
        indicadorCarregando.remove();
        adicionarMensagemAgente(pergunta, dados.resposta, dados.fontes || []);
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

function formatarMarkdownSimples(texto) {
    // Converte negrito (**texto**) em <strong>, e escapa o resto para
    // evitar que HTML acidental no texto quebre a página.
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
            fontes
                .map((f) => `<li>${f.arquivo} (${f.categoria})</li>`)
                .join("") +
            "</ul>";
        container.appendChild(blocoFontes);
    }

    const blocoFeedback = document.createElement("div");
    blocoFeedback.className = "feedback";

    const botaoPositivo = document.createElement("button");
    botaoPositivo.textContent = "👍";
    const botaoNegativo = document.createElement("button");
    botaoNegativo.textContent = "👎";

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

    historico.appendChild(container);
    rolarParaBaixo();
}

function rolarParaBaixo() {
    historico.scrollTop = historico.scrollHeight;
}