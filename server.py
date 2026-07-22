"""Iconografo — Generatore di icone da descrizione testuale.
Backend Flask: serve la pagina, gestisce la galleria condivisa in memoria.
"""

import os
import json
import uuid
import time
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "iconografo-secret-" + str(uuid.uuid4()))

# ── Galleria condivisa in memoria ──────────────────────────────────────────
gallery: list[dict] = []  # ultimi 100 elementi


@app.route("/")
def index():
    """Serve la pagina principale."""
    return render_template("index.html")


# ── API Galleria ────────────────────────────────────────────────────────────

@app.route("/api/icons", methods=["GET"])
def list_icons():
    """Restituisce le ultime 50 icone salvate (più recenti per prime)."""
    recent = sorted(gallery, key=lambda x: x.get("created", 0), reverse=True)[:50]
    return jsonify(recent)


@app.route("/api/icons", methods=["POST"])
def save_icon():
    """Salva un'icona nella galleria condivisa."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Richiesta non valida: corpo JSON mancante"}), 400
    word = (data.get("word") or "").strip()
    png_data = (data.get("data") or "").strip()
    if not word:
        return jsonify({"error": "Campo 'word' obbligatorio"}), 400
    if not png_data or not png_data.startswith("data:image/png;base64,"):
        return jsonify({"error": "Campo 'data' deve essere un PNG in base64"}), 400

    icon = {
        "id": str(uuid.uuid4())[:8],
        "word": word,
        "variant": data.get("variant", 0),
        "data": png_data,
        "created": time.time(),
    }
    gallery.append(icon)

    # Mantieni solo gli ultimi 100
    if len(gallery) > 100:
        del gallery[:-100]

    return jsonify(icon), 201


# ── SEO routes ──────────────────────────────────────────────────────────────

@app.route("/robots.txt")
def robots():
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Sitemap: https://github.com/bonciarello/iconografo/sitemap.xml\n"
    ), 200, {"Content-Type": "text/plain"}


@app.route("/sitemap.xml")
def sitemap():
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        "  <url>\n"
        "    <loc>https://github.com/bonciarello/iconografo/</loc>\n"
        "    <changefreq>monthly</changefreq>\n"
        "    <priority>0.8</priority>\n"
        "  </url>\n"
        "</urlset>\n"
    )
    return xml, 200, {"Content-Type": "application/xml"}


# ── Avvio ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 4601))
    app.run(host="0.0.0.0", port=port, debug=False)
