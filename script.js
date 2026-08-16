const input = document.getElementById("user-input");
const button = document.getElementById("send-btn");
const chatBox = document.getElementById("chat-box");


// ======================================================
// AFFICHER UN MESSAGE
// ======================================================

function addMessage(text, type) {

    const message = document.createElement("div");
    message.classList.add("message", type);

    message.innerHTML = text;

    chatBox.appendChild(message);
    chatBox.scrollTop = chatBox.scrollHeight;

    // MathJax
    if (window.MathJax && window.MathJax.typesetPromise) {
        MathJax.typesetPromise([message]).catch(function(error) {
            console.error("Erreur MathJax :", error);
        });
    }

    return message;
}


// ======================================================
// AFFICHER LA REPONSE DE MATHPRO AI
// ======================================================

function displayMathProResponse(response, latex) {

    let cleanResponse = response || "";

    // Retirer le code LaTeX de response
    cleanResponse = cleanResponse.replace(
        /```latex[\s\S]*?```/gi,
        ""
    );

    // Retirer les autres blocs de code éventuels
    cleanResponse = cleanResponse.replace(
        /```[\s\S]*?```/g,
        ""
    );

    cleanResponse = cleanResponse.trim();


    // --------------------------------------------------
    // MESSAGE
    // --------------------------------------------------

    const message = document.createElement("div");
    message.classList.add("message", "bot");


    // --------------------------------------------------
    // REPONSE NORMALE
    // --------------------------------------------------

    const responseContent = document.createElement("div");
    responseContent.classList.add("response-content");

    responseContent.innerHTML = cleanResponse;

    message.appendChild(responseContent);


    // --------------------------------------------------
    // CODE LATEX
    // --------------------------------------------------

    if (latex && latex.trim() !== "") {

        const latexContainer = document.createElement("div");
        latexContainer.classList.add("latex-container");


        // Bouton afficher
        const latexButton = document.createElement("button");

        latexButton.classList.add("latex-button");

        latexButton.textContent = "📋 Afficher le code LaTeX";


        // Zone du code
        const codeContainer = document.createElement("div");

        codeContainer.classList.add("latex-code-container");

        codeContainer.style.display = "none";


        const pre = document.createElement("pre");

        const code = document.createElement("code");

        code.textContent = latex;

        pre.appendChild(code);

        codeContainer.appendChild(pre);


        // --------------------------------------------------
        // Bouton COPIER
        // --------------------------------------------------

        const copyButton = document.createElement("button");

        copyButton.classList.add("copy-latex-button");

        copyButton.textContent = "📋 Copier le code";


        copyButton.addEventListener("click", async function() {

            try {

                await navigator.clipboard.writeText(latex);

                copyButton.textContent = "✅ Code copié !";

                setTimeout(function() {

                    copyButton.textContent = "📋 Copier le code";

                }, 2000);

            }

            catch (error) {

                console.error("Erreur de copie :", error);

                copyButton.textContent = "❌ Impossible de copier";

            }

        });


        // --------------------------------------------------
        // AFFICHER / MASQUER
        // --------------------------------------------------

        latexButton.addEventListener("click", function() {

            if (codeContainer.style.display === "none") {

                codeContainer.style.display = "block";

                latexButton.textContent = "➖ Masquer le code LaTeX";

            }

            else {

                codeContainer.style.display = "none";

                latexButton.textContent = "📋 Afficher le code LaTeX";

            }

        });


        latexContainer.appendChild(latexButton);

        latexContainer.appendChild(codeContainer);

        latexContainer.appendChild(copyButton);

        message.appendChild(latexContainer);
    }


    // --------------------------------------------------
    // AJOUTER LE MESSAGE
    // --------------------------------------------------

    chatBox.appendChild(message);

    chatBox.scrollTop = chatBox.scrollHeight;


    // --------------------------------------------------
    // MATHJAX
    // --------------------------------------------------

    if (window.MathJax && window.MathJax.typesetPromise) {

        MathJax.typesetPromise([message]).catch(function(error) {

            console.error("Erreur MathJax :", error);

        });

    }

}


// ======================================================
// ENVOYER UNE QUESTION
// ======================================================

async function sendMessage() {

    const question = input.value.trim();

    if (question === "") {
        return;
    }


    // Afficher la question
    addMessage(question, "user");

    // Vider le champ
    input.value = "";


    // Désactiver le bouton
    button.disabled = true;
    button.textContent = "⏳";


    try {

        console.log("Envoi vers Flask :", question);


        const response = await fetch(
            ""https://doumathpro-ai.onrender.com/chat"",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    message: question
                })
            }
        );


        console.log("Statut HTTP :", response.status);


        if (!response.ok) {

            throw new Error(
                "Erreur HTTP : " + response.status
            );

        }


        const data = await response.json();


        console.log("Réponse Flask :", data);


        // Vérifier que Flask renvoie bien response
        if (!data.response) {

            throw new Error(
                "La réponse du serveur ne contient pas 'response'."
            );

        }


        // Afficher réponse + LaTeX
        displayMathProResponse(
            data.response,
            data.latex || ""
        );


    }

    catch (error) {

        console.error("ERREUR COMPLETE :", error);


        addMessage(
            "❌ <strong>Erreur de connexion avec le serveur.</strong><br>" +
            "Détails : " + error.message,
            "bot"
        );

    }

    finally {

        button.disabled = false;
        button.textContent = "Envoyer";

    }

}


// ======================================================
// BOUTON ENVOYER
// ======================================================

button.addEventListener(
    "click",
    sendMessage
);


// ======================================================
// TOUCHE ENTREE
// ======================================================

input.addEventListener(
    "keydown",
    function(event) {

        if (event.key === "Enter") {

            event.preventDefault();

            sendMessage();

        }

    }
);