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

MAX_FILE_SIZE = 15 * 1024 * 1024

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
}


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
    "5. La reponse destinee a l'eleve doit etre tres detaillee, complete, claire et structuree.\n"
    "Pour chaque exercice, traite toutes les questions et sous-questions dans leur ordre, sans en oublier.\n"
    "Montre toutes les etapes utiles : methode choisie, proprietes ou theoremes utilises, calculs intermediaires, justification et conclusion.\n"
    "Ne donne jamais seulement le resultat. Adapte les explications au niveau d'un eleve et verifie le resultat final.\n"
    "Si une image ou un PDF est fourni, recopie d'abord fidelement l'enonce. Si une partie est illisible, signale-la au lieu de l'inventer.\n"

    "6. Toutes les expressions mathematiques doivent utiliser LaTeX entre $ $ "
    "(ex: $x^2 - 5x + 6 = 0$).\n"

    "7. Pour les expressions importantes, utilise $$ $$ "
    "(ex: $$\\Delta = b^2 - 4ac$$).\n"

    "8. N'utilise JAMAIS \\[...\\] dans la reponse eleve. Evite les formules excessivement longues sur une seule ligne.\n"

    "9. A la fin, produis obligatoirement le document LaTeX complet et compilable.\n"

    "10. Le document LaTeX doit contenir \\documentclass{article}, les packages "
    "et \\begin{document} \\end{document}.\n"

    "11. Structure obligatoire :\n\n"

    "===REPONSE_ELEVE===\n\n"
    "Texte de la solution destine a l'eleve.\n\n"
    "===FIN_REPONSE_ELEVE===\n\n"

    "===CODE_LATEX===\n\n"
    "Code LaTeX complet compilable contenant toute la correction detaillee, et non un simple resume.\n\n"
    "===FIN_CODE_LATEX===\n\n"

    "12. Ne mets aucun texte avant ===REPONSE_ELEVE=== ni apres ===FIN_CODE_LATEX===."
)


# ======================================================
# FLASK
# ======================================================

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE + (1024 * 1024)
CORS(app)


# ======================================================
# ROUTE CHAT
# ======================================================

@app.route("/chat", methods=["POST"])
def chat():

    try:

        # Les anciennes questions texte arrivent en JSON.
        # Les questions avec image/PDF arrivent en multipart/form-data.
        uploaded_file = request.files.get("file")

        if request.is_json:

            data = request.get_json(silent=True) or {}
            question = str(data.get("message", "")).strip()

        else:

            question = str(request.form.get("message", "")).strip()


        # ==================================================
        # QUESTION VIDE
        # ==================================================

        if not question and not uploaded_file:

            return jsonify({
                "response": "Veuillez écrire une question ou ajouter une image/PDF.",
                "latex": ""
            })


        # Question utilisée lorsqu'un document est envoyé sans texte.
        if uploaded_file and not question:

            question = (
                "Analyse ce document, recopie clairement l'énoncé mathématique, "
                "puis donne une solution détaillée étape par étape."
            )


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

        if not uploaded_file and salutation == "bonjour":

            return jsonify({
                "response":
                    "Bonjour, je suis Douma Ali, votre professeur de mathématiques. "
                    "Comment puis-je vous aider en mathématiques ?",
                "latex": ""
            })


        # --------------------------
        # BONSOIR
        # --------------------------

        if not uploaded_file and salutation == "bonsoir":

            return jsonify({
                "response":
                    "Bonsoir, je suis Douma Ali, votre professeur de mathématiques. "
                    "Comment puis-je vous aider en mathématiques ?",
                "latex": ""
            })


        # --------------------------
        # SALUT
        # --------------------------

        if not uploaded_file and salutation == "salut":

            return jsonify({
                "response":
                    "Salut, je suis Douma Ali, votre professeur de mathématiques. "
                    "Comment puis-je vous aider en mathématiques ?",
                "latex": ""
            })


        # ==================================================
        # QUESTION MATHEMATIQUE → GEMINI
        # ==================================================

        print("Question recue")


        gemini_contents = [question]


        # ==================================================
        # IMAGE OU PDF → GEMINI MULTIMODAL
        # ==================================================

        if uploaded_file:

            mime_type = (uploaded_file.mimetype or "").lower()

            if mime_type not in ALLOWED_MIME_TYPES:

                return jsonify({
                    "response": "❌ Format non accepté. Utilisez JPG, PNG, WEBP ou PDF.",
                    "latex": "",
                    "error": "Format non accepté. Utilisez JPG, PNG, WEBP ou PDF."
                }), 415


            file_bytes = uploaded_file.read()

            if not file_bytes:

                return jsonify({
                    "response": "❌ Le fichier envoyé est vide.",
                    "latex": "",
                    "error": "Le fichier envoyé est vide."
                }), 400


            gemini_contents.append(
                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=mime_type
                )
            )


        response = client.models.generate_content(

            model=MODEL,

            contents=gemini_contents,

            config=types.GenerateContentConfig(

                system_instruction=SYSTEM_PROMPT,

                temperature=0.1,
                max_output_tokens=8192

            )

        )


        text = response.text

        print("Reponse Gemini recue.")


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

            "latex": "",

            "error": "Erreur Gemini : " + str(e)

        }), 500


# ======================================================
# FICHIER TROP GRAND
# ======================================================

@app.errorhandler(413)
def fichier_trop_grand(_error):

    return jsonify({
        "response": "❌ Le fichier dépasse la limite de 15 Mo.",
        "latex": "",
        "error": "Le fichier dépasse la limite de 15 Mo."
    }), 413


# ======================================================
# LANCEMENT LOCAL
# ======================================================

if __name__ == "__main__":

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=os.getenv("FLASK_DEBUG", "0") == "1"

    )
