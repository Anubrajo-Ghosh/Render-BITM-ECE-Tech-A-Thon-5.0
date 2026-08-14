# 🌱 AgroScan — Crop Disease Detection Web App for Farmers

Built for **BITM ECE Tech-A-Thon** — Agro-Tech Problem Statement 1: *Crop Disease Detection Web App for Farmers*.

Upload a photo of a crop leaf → get an instant AI diagnosis, a confidence score, a severity rating, and a remedy tip in English or Hindi.

**Live demo:** `https://render-bitm-ece-tech-a-thon-5-0.onrender.com`

## Problem

Farmers often notice a diseased leaf too late, after the infection has already spread. Expert or veterinary access is sparse in rural areas, and without a clear diagnosis, wrong remedies waste money and time.

## Solution

A fine-tuned MobileNetV2 model classifies the uploaded leaf image. The app returns a diagnosis with a confidence score, a severity badge, and a remedy tip — with English/Hindi support and a persistent log of past scans.

## Features

- 📸 Drag-and-drop or click-to-upload leaf photo, with a live preview
- 🔬 Animated scan sweep while the model runs inference
- 🧠 Disease classification via a fine-tuned MobileNetV2
- 🔢 Top-3 predictions with confidence bars, for when the model is unsure
- ⚠️ Low-confidence warning banner
- 🩺 Color-coded severity badge (Healthy / Moderate / Critical)
- 🌐 English / Hindi remedy toggle, switched instantly client-side
- 📋 Persistent scan log (SQLite)
- 📄 Downloadable diagnostic report (.txt)
- 📱 Fully responsive, down to mobile

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Flask (Python) — serves the page and a JSON prediction API |
| Model | PyTorch, torchvision — MobileNetV2 (transfer learning) |
| Frontend | Hand-written HTML, CSS, and vanilla JS (no framework) |
| Storage | SQLite (prediction history) |
| Production server | Gunicorn |

## Project Structure

```
.
├── app.py                    # Flask app + inference API
├── templates/
│   └── index.html
├── static/
│   ├── css/style.css
│   └── js/script.js
├── crop_disease_model.pth    # Trained model weights (add this — see below)
├── requirements.txt
└── Procfile                  # Deployment entry point (gunicorn)
```

## Getting the model file

The app expects a trained `crop_disease_model.pth` in the project root. Add your already-trained model file here before running or deploying.

## Run locally

```bash
git clone <your-repo-url>
cd <repo-folder>
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000**. A `history.db` SQLite file is created automatically on first run.

## API

- `POST /api/predict` — multipart form with a `file` field (image). Returns label, confidence, severity, top-3 predictions, and remedy text in both languages.
- `GET /api/history` — most recent scan log entries.
- `POST /api/history/clear` — clears the scan log.

## Deployment

This is a **Flask + PyTorch** app — a real Python process that loads a ~9 MB model and needs the full `torch`/`torchvision` install (several hundred MB). That rules out Netlify and Vercel for the backend: both are built around static hosting and lightweight serverless functions, with function-size limits (roughly 50–250 MB) that PyTorch alone blows past, plus no persistent process to keep the model loaded in memory.

**Render** is the right fit of the three:

1. Push this repo to GitHub, with `crop_disease_model.pth` committed at the root.
2. Go to [render.com](https://render.com) → **New +** → **Web Service** → connect this GitHub repo.
3. Set:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app` (already set via the included `Procfile` — Render should auto-detect it)
4. Deploy. Render builds the image and gives `https://render-bitm-ece-tech-a-thon-5-0.onrender.com` URL.
5. Paste that URL into the **Live demo** line at the top of this README and commit.

Render's free web-service tier (750 hrs/month) covers this comfortably. It has 512 MB RAM, which is enough for MobileNetV2 inference, and it spins down after ~15 minutes of inactivity — the first request after idling takes 20–30 seconds to "wake up." If you're demoing live to judges, open the link a minute or two before your slot so it's already warm.

## Future Scope

- Expand beyond potato to 3–5+ crop classes using the full PlantVillage dataset
- On-device / offline inference for low-connectivity villages
- SMS-based remedy delivery for farmers without smartphones
- Farmer login with per-user history

## **Team**

**Team Binary Biologists**

- Anubrajo Ghosh
- Prabrisha Basu

2nd Year B.Sc. (Honours) Microbiology

Postgraduate and Research Department of Microbiology

St. Xavier's College (Autonomous), Kolkata

Built for BITM ECE Tech-A-Thon — Agro-Tech Problem Statement 1.
