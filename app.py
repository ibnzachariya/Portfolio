"""Abdulfatai Ibn Zachariya — portfolio website.

All the text, projects, skills and links live in the JSON files in /data.
To add or change a project you edit data/projects.json — no HTML needed.
"""

import json
import logging
import os
import re
import secrets
import smtplib
import urllib.error
import urllib.request
from datetime import date
from email.message import EmailMessage
from pathlib import Path

from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)
from werkzeug.middleware.proxy_fix import ProxyFix

try:  # load .env when running locally (optional dependency)
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Static files live in public/static so they work locally AND on Vercel
# (Vercel serves everything in public/ from its CDN; URLs stay /static/...).
app = Flask(__name__, static_folder="public/static", static_url_path="/static")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
if not os.environ.get("SECRET_KEY"):
    logging.getLogger("portfolio").warning(
        "SECRET_KEY is not set — using a temporary one. Set it on your host "
        "so the contact form works reliably.")
# Behind a hosting proxy (Render, Railway, PythonAnywhere…) keep https URLs correct.
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

log = logging.getLogger("portfolio")
logging.basicConfig(level=logging.INFO)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# --------------------------------------------------------------------------- #
# Content helpers
# --------------------------------------------------------------------------- #
def load_json(name):
    with open(DATA_DIR / name, encoding="utf-8") as fh:
        return json.load(fh)


def get_formspree_id():
    """Formspree form ID: from the FORMSPREE_ID env variable, or "formspree_id" in data/site.json.
    Accepts either the short ID (e.g. xyzabcde) or the full https://formspree.io/f/xyzabcde link."""
    raw = (os.environ.get("FORMSPREE_ID") or load_json("site.json").get("formspree_id") or "").strip()
    return raw.rstrip("/").split("/")[-1] if raw else ""


def get_projects():
    return load_json("projects.json")


def get_project(slug):
    return next((p for p in get_projects() if p["slug"] == slug), None)


@app.context_processor
def inject_globals():
    """Make site settings and the current year available in every template."""
    return {"site": load_json("site.json"), "current_year": date.today().year,
            "formspree_id": get_formspree_id()}


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #
@app.route("/")
def home():
    projects = get_projects()
    featured = next((p for p in projects if p.get("featured")), projects[0])
    return render_template("index.html", projects=projects, featured=featured)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/projects")
def projects():
    return render_template("projects.html", projects=get_projects())


@app.route("/projects/<slug>")
def project_detail(slug):
    project = get_project(slug)
    if project is None:
        abort(404)
    return render_template("project_detail.html", project=project)


@app.route("/oil-gas-platform")
def oil_gas_platform():
    # Old URL kept working so existing shared links don't break.
    return redirect(url_for("project_detail", slug="oil-gas-compliance-platform"), 301)


# --------------------------------------------------------------------------- #
# Contact form
# --------------------------------------------------------------------------- #
def send_via_formspree(name, email, message):
    form_id = get_formspree_id()
    if not form_id:
        return False
    payload = json.dumps({"name": name, "email": email, "message": message,
                          "_subject": f"Portfolio message from {name}"}).encode()
    req = urllib.request.Request(
        f"https://formspree.io/f/{form_id}", data=payload, method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 "User-Agent": "Mozilla/5.0 (portfolio contact form)",
                 "Referer": request.host_url})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except urllib.error.HTTPError as err:  # log Formspree's reason (visible in Vercel logs)
        log.error("Formspree rejected the message: %s %s", err.code, err.read()[:500])
        return False


def send_via_smtp(name, email, message):
    user = os.environ.get("MAIL_USERNAME", "").strip()
    password = os.environ.get("MAIL_PASSWORD", "").strip()
    if not (user and password):
        return False
    msg = EmailMessage()
    msg["Subject"] = f"Portfolio message from {name}"
    msg["From"] = user
    msg["To"] = os.environ.get("MAIL_TO", user)
    msg["Reply-To"] = email
    msg.set_content(f"Name: {name}\nEmail: {email}\n\n{message}")
    server = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    port = int(os.environ.get("MAIL_PORT", "587"))
    with smtplib.SMTP(server, port, timeout=15) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(msg)
    return True


@app.route("/contact", methods=["GET", "POST"])
def contact():
    form = {"name": "", "email": "", "message": ""}
    errors = {}

    if request.method == "POST":
        form = {k: request.form.get(k, "").strip() for k in form}

        # Spam trap: real people never fill the hidden "website" field.
        if request.form.get("website"):
            flash("Thanks! Your message has been sent.", "success")
            return redirect(url_for("contact"))

        if request.form.get("csrf_token") != session.get("_csrf"):
            flash("Your session expired. Please try sending the message again.", "danger")
            return render_template("contact.html", form=form, errors=errors), 400

        if len(form["name"]) < 2:
            errors["name"] = "Please enter your name."
        if not EMAIL_RE.match(form["email"]):
            errors["email"] = "Please enter a valid email address."
        if len(form["message"]) < 10:
            errors["message"] = "Please write a message (at least 10 characters)."
        if len(form["message"]) > 5000:
            errors["message"] = "Message is too long (5,000 characters max)."

        if not errors:
            sent = False
            try:
                sent = (send_via_formspree(**form) or send_via_smtp(**form))
            except Exception:  # network / auth problems
                log.exception("Contact form delivery failed")
            if sent:
                flash("Thanks! Your message has been sent. I'll get back to you soon.", "success")
                return redirect(url_for("contact"))
            log.warning("Contact form not delivered — set FORMSPREE_ID or MAIL_USERNAME/MAIL_PASSWORD")
            email_addr = load_json("site.json")["email"]
            flash(f"Sorry, the message couldn't be sent right now. "
                  f"Please email me directly at {email_addr}.", "danger")

    return render_template("contact.html", form=form, errors=errors)


# --------------------------------------------------------------------------- #
# Errors, robots, sitemap
# --------------------------------------------------------------------------- #
@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(_e):
    return render_template("404.html", server_error=True), 500


@app.route("/robots.txt")
def robots():
    body = f"User-agent: *\nAllow: /\nSitemap: {url_for('sitemap', _external=True)}\n"
    return body, 200, {"Content-Type": "text/plain"}


@app.route("/sitemap.xml")
def sitemap():
    urls = [url_for(e, _external=True) for e in ("home", "about", "projects", "contact")]
    urls += [url_for("project_detail", slug=p["slug"], _external=True) for p in get_projects()]
    items = "".join(f"<url><loc>{u}</loc></url>" for u in urls)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{items}</urlset>')
    return xml, 200, {"Content-Type": "application/xml"}


if __name__ == "__main__":
    # Debug mode only when you ask for it locally: set FLASK_DEBUG=1 in .env
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
