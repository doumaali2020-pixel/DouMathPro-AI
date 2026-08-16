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

# CORRECTION 1 : Le nom du modèle correct est gemini-1.5-flash
MODEL = "gemini-3.5-flash-lite"

SYSTEM_PROMPT = (
    "Tu es l'assistant mathematique de Douma Ali, professeur de mathematiques.\n"
    "Ta mission est de repondre aux questions mathematiques de maniere rigoureuse, claire et pedagogique.\n\n"

    "PRESENTATION :\n"
    "1. Si l'utilisateur dit simplement bonjour, salut, bonsoir ou une salutation equivalente, "
    "reponds : Bonjour, je suis Douma Ali. Comment puis-je vous aider en mathematiques ?\n"
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

app = Flask(__name__)
CORS(app)

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        question = data.get("message", "").strip()

        if not question:
            return jsonify({
                "response": "Veuillez écrire une question de mathématiques.",
                "latex": ""
            })

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

        # Extraction de la réponse élève
        if "===REPONSE_ELEVE===" in text and "===FIN_REPONSE_ELEVE===" in text:
            student_response = text.split("===REPONSE_ELEVE===")[1].split("===FIN_REPONSE_ELEVE===")[0].strip()
        else:
            student_response = text

        # Extraction du code LaTeX
        if "===CODE_LATEX===" in text and "===FIN_CODE_LATEX===" in text:
            latex_code = text.split("===CODE_LATEX===")[1].split("===FIN_CODE_LATEX===")[0].strip()
            # Nettoyage des balises markdown si Gemini les a ajoutées
            latex_code = re.sub(r"^```latex\s*|^```\s*|```\s*$", "", latex_code, flags=re.MULTILINE).strip()

        # CORRECTION 3 : On réinjecte le code LaTeX dans la réponse sous forme de bloc markdown
        # pour que le script.js puisse le détecter et créer le bouton "Afficher le code LaTeX"
        final_response = student_response
        if latex_code:
            final_response += "\n\n```latex\n" + latex_code + "\n```"

        return jsonify({
            "response": final_response,
            "latex": latex_code
        })

    except Exception as e:
        print("ERREUR :", e)
        return jsonify({
            "response": "❌ Erreur Gemini : " + str(e),
            "latex": ""
        }), 500

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        # CORRECTION 2 : Remis à 5000 car votre script.js s'attend à parler au port 5000
        port=5000,  
        debug=True
    )