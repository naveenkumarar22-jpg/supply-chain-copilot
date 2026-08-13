---
title: Supply Chain Operations Copilot
emoji: 📦
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 6.23.1
app_file: ui/app.py
pinned: false
---

# Supply Chain Operations Copilot

See `docs/decisions_1.md` for the full architecture decision record.

## Running locally

Set up the environment once:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your OPENAI_API_KEY
```

Start the API (in one terminal):

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Verify it's up:

```bash
curl http://127.0.0.1:8000/health
```

Start the UI (in a second terminal):

```bash
source .venv/bin/activate
python ui/app.py
```

Then open the URL Gradio prints (typically `http://127.0.0.1:7860`) in a browser.
