from flask import Flask, render_template, request, redirect, flash, send_file
import requests
import io
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = '123456'

API_KEY = os.getenv("OPENSUBTITLES_API_KEY")
HEADERS = {
    "Api-Key": API_KEY,
    "Content-Type": "application/json",
    "User-Agent": "MySubtitleApp"
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search", methods=["POST"])
def search():
    query = request.form.get("query")
    language = request.form.get("language")

    if not query:
        flash("Por favor, insira um nome de filme.")
        return redirect("/")

    try:
        response = requests.get(
            "https://api.opensubtitles.com/api/v1/subtitles",
            headers=HEADERS,
            params={"query": query, "languages": language, "order_by": "downloads", "limit": 20}
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        flash(f"Erro ao procurar legendas: {e}")
        return redirect("/")

    results = response.json().get("data", [])
    return render_template("results.html", subtitles=results, query=query)

@app.route("/download/<file_id>")
def download(file_id):
    try:
        resp = requests.post(
            "https://api.opensubtitles.com/api/v1/download",
            headers=HEADERS,
            json={"file_id": file_id}
        )
        resp.raise_for_status()
        data = resp.json()
        download_link = data.get("link")
        if not download_link:
            flash("Não foi possível obter o link de download.")
            return redirect("/")

        file_resp = requests.get(download_link)
        file_resp.raise_for_status()

        content_type = file_resp.headers.get("Content-Type", "")
        content = file_resp.content

        if "application/zip" in content_type:
            return send_file(
                io.BytesIO(content),
                mimetype="application/zip",
                as_attachment=True,
                download_name=f"subtitle_{file_id}.zip"
            )
        elif "text/plain" in content_type or "application/x-subrip" in content_type or download_link.endswith(".srt"):
            return send_file(
                io.BytesIO(content),
                mimetype="text/plain",
                as_attachment=True,
                download_name=f"subtitle_{file_id}.srt"
            )
        else:
            return f"Tipo inesperado '{content_type}'. Conteúdo:<br><pre>{file_resp.text}</pre>"
    except requests.exceptions.RequestException as e:
        flash(f"Erro HTTP ao baixar legenda: {e}")
    except Exception as e:
        flash(f"Erro inesperado ao baixar legenda: {e}")

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)


