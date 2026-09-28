# Abdulfatai Ibn Zachariya — Portfolio

A Flask portfolio site. **All content lives in the `data/` folder**, so updating the site
never means editing HTML.

```
app.py                 routes, contact form, 404, sitemap
data/site.json         your name, bio, skills, links, certifications
data/projects.json     every project card and project page
public/static/images/  photos and screenshots
public/static/files/   CV and other downloads
templates/             page layouts (you rarely need to touch these)
```

## Run it on your computer

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # then open .env and set SECRET_KEY and FLASK_DEBUG=1
python app.py
```

Open http://127.0.0.1:5000

## Add a new project (with a photo)

1. Put the screenshot in `public/static/images/`, e.g. `public/static/images/my-app.png`
   (landscape, around 1600px wide works best).
2. Open `data/projects.json` and copy one of the existing `{ ... }` blocks, paste it
   into the list (mind the comma between blocks), and change the values:
   - `slug` — the page address, e.g. `my-app` → `/projects/my-app` (lowercase, dashes, unique)
   - `image` — `images/my-app.png` (leave `""` to show an icon instead)
   - `icon` — any [Bootstrap Icon](https://icons.getbootstrap.com) name, used when there's no image
   - `links.live`, `links.github`, `links.download` — buttons only appear when these are filled
   - `featured: true` on the one project you want highlighted on the home page
3. Save, commit and push. Your host redeploys automatically.

The order of projects in the file is the order they appear on the site.

## Replace your CV or profile photo

Overwrite `public/static/files/Abdulfatai_CV.pdf` or `public/static/images/profile.jpg` with a file of the
same name, or put in a new file and update `cv_file` / `profile_image` in `data/site.json`.

## Add a certificate

1. Put a photo/scan of it in `public/static/images/certificates/` (JPG, about 1000px wide).
2. In `data/site.json` → `certifications`, copy one block and fill in `title`, `issuer`,
   `year`, `text`, and `file` (e.g. `images/certificates/my-cert.jpg`).
   Leave `file` as `""` if you don't want a "View certificate" button.

Education (degrees) is in the `education` list in the same file.

## Fill in before going live

GitHub and LinkedIn are already set in `data/site.json`. For each project in
`data/projects.json`, add its `github` or `live` link once it exists — the buttons appear automatically.

## Contact form

Messages are delivered by **Formspree** (set `FORMSPREE_ID`) or by **Gmail** (set
`MAIL_USERNAME`, `MAIL_PASSWORD` — a Google *App Password*, not your normal password).
See `.env.example`. If neither is set, visitors see a friendly message with your email address.

## Deploy on Vercel (recommended — free, no card needed)

1. Push this folder to a GitHub repository (public or private).
2. On vercel.com → Add New → Project → import the repo. Vercel detects Flask from `app.py`
   automatically — leave all build settings as they are.
3. Before clicking Deploy, open **Environment Variables** and add:
   - `SECRET_KEY` — a long random string (required, or the contact form will fail)
   - `FORMSPREE_ID` — from formspree.io
4. Deploy. Every `git push` after that redeploys automatically.
5. Optional: Project → Settings → Domains to add your own domain.

Static files (images, CSS, CV) must stay inside `public/static/` — Vercel serves them from
there. Locally, `python app.py` serves the same folder, so nothing else changes.

## Other hosts

Render, Railway, Koyeb or PythonAnywhere also work: install `requirements.txt` and run
`gunicorn app:app` (or point the WSGI file at `app`), and set the same environment variables.
