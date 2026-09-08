const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1"]);
const IS_LOCAL = location.protocol === "file:" || LOCAL_HOSTS.has(location.hostname);
const API_URL = window.MATHPRO_API_URL || (
    IS_LOCAL
        ? "http://127.0.0.1:5000/chat"
        : "https://doumathpro-ai.onrender.com/chat"
);
const MAX_FILE_SIZE = 15 * 1024 * 1024;
const ACCEPTED_TYPES = new Set(["image/jpeg", "image/png", "image/webp", "application/pdf"]);

const input = document.getElementById("user-input");
const sendButton = document.getElementById("send-btn");
const attachButton = document.getElementById("attach-btn");
const fileInput = document.getElementById("file-input");
const removeFileButton = document.getElementById("remove-file");
const attachmentPreview = document.getElementById("attachment-preview");
const imagePreview = document.getElementById("image-preview");
const fileIcon = document.getElementById("file-icon");
const fileName = document.getElementById("file-name");
const fileSize = document.getElementById("file-size");
const chatBox = document.getElementById("chat-box");

let selectedFile = null;
let previewUrl = null;

function escapeHtml(value) {
    const node = document.createElement("div");
    node.textContent = value;
    return node.innerHTML;
}

function renderMarkdown(text) {
    if (!window.marked) return escapeHtml(text).replace(/\n/g, "<br>");

    // Protéger le LaTeX : Marked ne doit pas transformer les _ et *
    // présents à l'intérieur de $...$ ou $$...$$ avant MathJax.
    const mathExpressions = [];
    const protectedText = text.replace(
        /\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)|\$(?!\$)(?:\\.|[^$\n])*?\$/g,
        expression => {
            const token = `MATHPROTOKEN${mathExpressions.length}X`;
            mathExpressions.push(expression);
            return token;
        }
    );

    const rendered = marked.parse(protectedText, { breaks: true });
    let safeHtml = window.DOMPurify
        ? DOMPurify.sanitize(rendered)
        : escapeHtml(protectedText).replace(/\n/g, "<br>");

    mathExpressions.forEach((expression, index) => {
        safeHtml = safeHtml.replace(
            `MATHPROTOKEN${index}X`,
            escapeHtml(expression)
        );
    });

    return safeHtml;
}

function typesetMath(element) {
    if (window.MathJax?.typesetPromise) {
        MathJax.typesetPromise([element]).catch(error => console.error("Erreur MathJax :", error));
    }
}

function scrollToBottom() {
    chatBox.scrollTop = chatBox.scrollHeight;
}

function addMessage(content, type, options = {}) {
    const message = document.createElement("div");
    message.className = `message ${type}`;

    if (options.file) {
        const attachment = document.createElement("div");
        attachment.className = "message-attachment";
        attachment.textContent = `${options.file.type.startsWith("image/") ? "🖼️" : "📄"} ${options.file.name}`;
        message.appendChild(attachment);
    }

    if (content) {
        const body = document.createElement("div");
        body.className = "response-content";
        body.innerHTML = type === "bot" ? renderMarkdown(content) : escapeHtml(content).replace(/\n/g, "<br>");
        message.appendChild(body);
    }

    chatBox.appendChild(message);
    scrollToBottom();
    typesetMath(message);
    return message;
}

function displayMathProResponse(response, latex = "") {
    const cleanResponse = (response || "")
        .replace(/```latex[\s\S]*?```/gi, "")
        .trim();
    const message = addMessage(cleanResponse, "bot");

    if (!latex.trim()) return;

    const container = document.createElement("div");
    container.className = "latex-container";

    const toggle = document.createElement("button");
    toggle.className = "latex-button";
    toggle.type = "button";
    toggle.textContent = "📋 Afficher le code LaTeX";

    const codeContainer = document.createElement("div");
    codeContainer.className = "latex-code-container";
    codeContainer.hidden = true;
    const pre = document.createElement("pre");
    const code = document.createElement("code");
    code.textContent = latex;
    pre.appendChild(code);
    codeContainer.appendChild(pre);

    const copy = document.createElement("button");
    copy.className = "copy-latex-button";
    copy.type = "button";
    copy.textContent = "📋 Copier le code";
    copy.addEventListener("click", async () => {
        try {
            await navigator.clipboard.writeText(latex);
            copy.textContent = "✅ Code copié !";
            setTimeout(() => { copy.textContent = "📋 Copier le code"; }, 2000);
        } catch {
            copy.textContent = "❌ Copie impossible";
        }
    });

    toggle.addEventListener("click", () => {
        codeContainer.hidden = !codeContainer.hidden;
        toggle.textContent = codeContainer.hidden ? "📋 Afficher le code LaTeX" : "➖ Masquer le code LaTeX";
    });

    container.append(toggle, codeContainer, copy);
    message.appendChild(container);
    scrollToBottom();
}

function readableSize(bytes) {
    if (bytes < 1024 * 1024) return `${Math.ceil(bytes / 1024)} Ko`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
}

function clearSelectedFile() {
    selectedFile = null;
    fileInput.value = "";
    attachmentPreview.hidden = true;
    imagePreview.hidden = true;
    imagePreview.removeAttribute("src");
    fileIcon.hidden = false;
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = null;
}

function selectFile(file) {
    if (!file) return;
    if (!ACCEPTED_TYPES.has(file.type)) {
        addMessage("❌ Format non accepté. Choisissez une image JPG, PNG, WEBP ou un PDF.", "bot");
        return;
    }
    if (file.size > MAX_FILE_SIZE) {
        addMessage("❌ Le fichier dépasse 15 Mo. Choisissez un fichier plus petit.", "bot");
        return;
    }

    clearSelectedFile();
    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = readableSize(file.size);
    attachmentPreview.hidden = false;

    if (file.type.startsWith("image/")) {
        previewUrl = URL.createObjectURL(file);
        imagePreview.src = previewUrl;
        imagePreview.hidden = false;
        fileIcon.hidden = true;
    }
    input.focus();
}

async function sendMessage() {
    const question = input.value.trim();
    const file = selectedFile;
    if (!question && !file) return;

    const defaultQuestion = file
        ? "Analyse ce document, recopie clairement l’énoncé mathématique, puis donne une solution détaillée étape par étape."
        : "";
    const message = question || defaultQuestion;

    addMessage(question || "Analyse et résous cet exercice.", "user", { file });
    input.value = "";
    clearSelectedFile();
    sendButton.disabled = true;
    attachButton.disabled = true;
    sendButton.textContent = "⏳";
    const waiting = addMessage("Lecture et analyse en cours…", "bot");
    waiting.classList.add("waiting");

    try {
        let body;
        let headers = {};

        if (file) {
            body = new FormData();
            body.append("message", message);
            body.append("file", file, file.name);
        } else {
            headers["Content-Type"] = "application/json";
            body = JSON.stringify({ message });
        }

        const response = await fetch(API_URL, { method: "POST", headers, body });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.error || `Erreur HTTP ${response.status}`);
        if (!data.response) throw new Error("Le serveur n’a retourné aucune réponse.");

        waiting.remove();
        displayMathProResponse(data.response, data.latex || "");
    } catch (error) {
        waiting.remove();
        addMessage(`❌ **Erreur de connexion avec le serveur.**\n${error.message}`, "bot");
    } finally {
        sendButton.disabled = false;
        attachButton.disabled = false;
        sendButton.textContent = "Envoyer";
        input.focus();
    }
}

attachButton.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => selectFile(fileInput.files[0]));
removeFileButton.addEventListener("click", clearSelectedFile);
sendButton.addEventListener("click", sendMessage);
input.addEventListener("keydown", event => {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
});
