import os
from flask import Flask, request, redirect, render_template, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import string, random
from dotenv import load_dotenv
app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///UGlink.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

load_dotenv()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

class ShortLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    original_url = db.Column(db.String(500), nullable=False)

def generate_slug(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/", methods=["POST"])
def create_shortlink():
    # Cek apakah request dari JavaScript (JSON)
    if request.is_json:
        data = request.get_json()
        original_url = data.get("url")
        custom_slug = data.get("slug")
    else:
        # fallback kalau form biasa
        original_url = request.form.get("url")
        custom_slug = request.form.get("slug")

    if not original_url:
        if request.is_json:
            return jsonify({"status": "error", "message": "URL tidak boleh kosong"}), 400
        flash("URL tidak boleh kosong!", "error")
        return redirect(url_for("index"))

    slug = custom_slug or generate_slug()
    if ShortLink.query.filter_by(slug=slug).first():
        if request.is_json:
            return jsonify({"status": "error", "message": "Slug sudah dipakai"}), 400
        flash("Slug sudah dipakai, silakan pilih yang lain.", "error")
        return redirect(url_for("index"))

    new_link = ShortLink(slug=slug, original_url=original_url)
    db.session.add(new_link)
    db.session.commit()

    if request.is_json:
        return jsonify({
            "status": "success",
            "message": "Shortlink berhasil dibuat",
            "shortlink": f"{request.host_url}{slug}"
        })

    flash(f"Shortlink berhasil dibuat: {request.host_url}{slug}", "success")
    return redirect(url_for("index"))

@app.route("/delete/<int:link_id>")
def delete_link(link_id):
    link = ShortLink.query.get_or_404(link_id)
    db.session.delete(link)
    db.session.commit()
    flash("Shortlink berhasil dihapus!", "success")
    return redirect(url_for("admin"))

@app.route("/<slug>")
def redirect_to_original(slug):
    link = ShortLink.query.filter_by(slug=slug).first_or_404()
    return redirect(link.original_url)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            flash("Login berhasil!", "success")
            return redirect(url_for("admin"))
        else:
            flash("Username atau password salah", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    flash("Berhasil logout!", "success")
    return redirect(url_for("login"))

# --- Admin Routes ---
@app.route("/admin")
def admin():
    if not session.get("logged_in"):
        flash("Silakan login terlebih dahulu", "error")
        return redirect(url_for("login"))

    links = ShortLink.query.all()
    return render_template("admin.html", links=links)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
