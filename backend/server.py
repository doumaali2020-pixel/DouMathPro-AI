from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import re
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY introuvable dans le fichier .env")

client = genai.Client(api_key=api_key)

MODEL = "gemini-3.5-flash-lite"


# ======================================================
# SYSTEM PROMPT
# ======================================================

SYSTEM_PROMPT = (
    "Tu es l'assistant mathematique de Douma Ali, professeur de mathematiques.\n"
    "Ta mission est de repondre aux questions mathematiques de maniere rigoureuse, claire et pedagogique.\n\n"

    "PRESENTATION :\n"
    "1. Tu es l'assistant mathematique de Douma Ali.\n"
    "2. Ne dis jamais : Je suis MathPro AI.\n"
    "3. Ne repete pas Bonjour, je suis Douma Ali au debut de chaque exercice.\n"
    "4. Si l'utilisateur pose directement une question mathematique, commence directement par la resolution.\n\n"

    "IMPORTANT :\n"
    "5. La reponse destinee a l'eleve doit etre claire, detaillee et structuree.\n"

    "6. Toutes les expressions mathematiques doivent utiliser LaTeX entre $ $ "
    "(ex: $x^2 - 5x + 6 = 0$).\n"

    "7. Pour les expressions importantes, utilise $$ $$ "
    "(ex: $$\\Delta = b^2 - 4ac$$).\n"

    "8. N'utilise JAMAIS \\[...\\] dans la reponse eleve.\n"

    "9. A la fin, produis obligatoirement le document LaTeX complet et compilable.\n"

    "10. Le document LaTeX doit contenir \\documentclass{article}, les packages "
    "et \\begin{document} \\end{document}.\n"

    "11. Structure obligatoire :\n\n"

    "===REPONSE_ELEVE===\n\n"
    "Texte de la solution destine a l'eleve.\n\n"
    "===FIN_REPONSE_ELEVE===\n\n"

    "===CODE_LATEX===\n\n"
    "Code LaTeX complet compilable.\n\n"
    "===FIN_CODE_LATEX===\n\n"

    "12. Ne mets aucun texte avant ===REPONSE_ELEVE=== ni apres ===FIN_CODE_LATEX===."
)


# ======================================================
# FLASK
# ======================================================

app = Flask(__name__)
CORS(app)


# ======================================================
# ROUTE CHAT
# ======================================================

@app.route("/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json()

        question = data.get("message", "").strip()


        # ==================================================
        # QUESTION VIDE
        # ==================================================

        if not question:

            return jsonify({
                "response": "Veuillez écrire une question de mathématiques.",
                "latex": ""
            })


        # ==================================================
        # SALUTATIONS DIRECTES
        # Gemini n'est PAS appelé ici
        # ==================================================

        salutation = question.lower().strip()

        # Retirer quelques ponctuations finales
        salutation = salutation.rstrip("!?. ")


        # --------------------------
        # BONJOUR
        # --------------------------

        if salutation == "bonjour":

            return jsonify({
                "response":
                    "Bonjour, je suis Douma Ali, votre professeur de mathématiques. "
                    "Comment puis-je vous aider en mathématiques ?",
                "latex": ""
            })


        # --------------------------
        # BONSOIR
        # --------------------------

        if salutation == "bonsoir":

            return jsonify({
                "response":
                    "Bonsoir, je suis Douma Ali, votre professeur de mathématiques. "
                    "Comment puis-je vous aider en mathématiques ?",
                "latex": ""
            })


        # --------------------------
        # SALUT
        # --------------------------

        if salutation == "salut":

            return jsonify({
                "response":
                    "Salut, je suis Douma Ali, votre professeur de mathématiques. "
                    "Comment puis-je vous aider en mathématiques ?",
                "latex": ""
            })


        # ==================================================
        # QUESTION MATHEMATIQUE → GEMINI
        # ==================================================

        print("Question reçue :", question)


        response = client.models.generate_content(

            model=MODEL,

            contents=question,

            config=types.GenerateContentConfig(

                system_instruction=SYSTEM_PROMPT,

                temperature=0.2

            )

        )


        text = response.text

        print("Réponse Gemini reçue.")


        student_response = ""

        latex_code = ""


        # ==================================================
        # EXTRACTION REPONSE ELEVE
        # ==================================================

        if (
            "===REPONSE_ELEVE===" in text
            and
            "===FIN_REPONSE_ELEVE===" in text
        ):

            student_response = (
                text
                .split("===REPONSE_ELEVE===")[1]
                .split("===FIN_REPONSE_ELEVE===")[0]
                .strip()
            )

        else:

            student_response = text


        # ==================================================
        # EXTRACTION CODE LATEX
        # ==================================================

        if (
            "===CODE_LATEX===" in text
            and
            "===FIN_CODE_LATEX===" in text
        ):

            latex_code = (
                text
                .split("===CODE_LATEX===")[1]
                .split("===FIN_CODE_LATEX===")[0]
                .strip()
            )


            # Nettoyer les ```latex éventuels

            latex_code = re.sub(
                r"^```latex\s*|^```\s*|```\s*$",
                "",
                latex_code,
                flags=re.MULTILINE
            ).strip()


        # ==================================================
        # REPONSE FINALE
        # ==================================================

        final_response = student_response


        if latex_code:

            final_response += (
                "\n\n```latex\n"
                + latex_code
                + "\n```"
            )


        return jsonify({

            "response": final_response,

            "latex": latex_code

        })


    # ======================================================
    # ERREUR
    # ======================================================

    except Exception as e:

        print("ERREUR :", e)

        return jsonify({

            "response":
                "❌ Erreur Gemini : " + str(e),

            "latex": ""

        }), 500


# ======================================================
# LANCEMENT LOCAL
# ======================================================

if __name__ == "__main__":

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )