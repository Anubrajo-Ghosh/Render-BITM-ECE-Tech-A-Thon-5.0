import os
import io
import datetime
import sqlite3

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB upload limit


@app.errorhandler(413)
def file_too_large(e):
    return jsonify({"error": "File too large. Please upload an image under 8 MB."}), 413

# ---------------------------------------------------------
# Config / constants
# ---------------------------------------------------------
DB_PATH = "history.db"
MODEL_PATH = "crop_disease_model.pth"

CLASSES = ['Potato Early Blight', 'Potato Late Blight', 'Potato Healthy']

SEVERITY = {
    'Potato Early Blight': {'level': 'Moderate Alert', 'code': 'moderate'},
    'Potato Late Blight': {'level': 'Critical Action Required', 'code': 'critical'},
    'Potato Healthy': {'level': 'Healthy / Low Risk', 'code': 'healthy'},
}

REMEDIES = {
    "en": {
        'Potato Early Blight': 'Apply copper-based fungicides. Prune affected bottom leaves to improve airflow.',
        'Potato Late Blight': 'Apply systemic fungicides immediately. Avoid overhead watering and ensure drainage.',
        'Potato Healthy': 'Plant is healthy! Maintain regular watering and monitor periodically.',
    },
    "hi": {
        'Potato Early Blight': 'कॉपर-आधारित कवकनाशी का प्रयोग करें। हवा का प्रवाह सुधारने के लिए निचले पत्तों को काट दें।',
        'Potato Late Blight': 'तुरंत सिस्टमिक कवकनाशी का छिड़काव करें। ऊपर से सिंचाई करने से बचें।',
        'Potato Healthy': 'पौधा पूरी तरह स्वस्थ है! नियमित सिंचाई बनाए रखें।',
    },
}

TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

# ---------------------------------------------------------
# DB helpers
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            result TEXT,
            confidence TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()  # ensure the history table exists whether run directly or via a WSGI server (gunicorn)


def log_prediction(filename, result, confidence):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO history (filename, result, confidence, timestamp) VALUES (?, ?, ?, ?)",
        (filename, result, confidence, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()


def get_history(limit=25):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT filename, result, confidence, timestamp FROM history ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [
        {"filename": r[0], "result": r[1], "confidence": r[2], "timestamp": r[3]}
        for r in rows
    ]


def clear_history():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM history")
    conn.commit()
    conn.close()


# ---------------------------------------------------------
# Model loading
# ---------------------------------------------------------
_model = None


def get_model():
    global _model
    if _model is None:
        m = models.mobilenet_v2()
        m.classifier[1] = nn.Linear(m.last_channel, len(CLASSES))
        m.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device("cpu")))
        m.eval()
        _model = m
    return _model


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    try:
        model = get_model()
    except Exception:
        return jsonify({"error": "Model file not found on server. Place crop_disease_model.pth in the project root."}), 500

    try:
        image = Image.open(io.BytesIO(file.read())).convert("RGB")
        tensor_img = TRANSFORM(image).unsqueeze(0)

        with torch.no_grad():
            outputs = model(tensor_img)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)

        top_prob, top_cat = torch.topk(probabilities, k=min(3, len(CLASSES)))
        top_class = CLASSES[top_cat[0]]
        confidence = top_prob[0].item() * 100

        top3 = [
            {"label": CLASSES[top_cat[i]], "confidence": round(top_prob[i].item() * 100, 1)}
            for i in range(len(top_prob))
        ]

        sev = SEVERITY.get(top_class, {"level": "Unknown", "code": "unknown"})

        log_prediction(file.filename, top_class, f"{confidence:.1f}%")

        return jsonify({
            "label": top_class,
            "confidence": round(confidence, 1),
            "low_confidence": confidence < 60,
            "severity": sev,
            "top3": top3,
            "remedy": {
                "en": REMEDIES["en"].get(top_class, "No tip available."),
                "hi": REMEDIES["hi"].get(top_class, "कोई सुझाव उपलब्ध नहीं है।"),
            },
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "filename": file.filename,
        })
    except Exception as e:
        return jsonify({"error": f"Couldn't analyze this image ({e}). Try a clearer leaf photo."}), 400


@app.route("/api/history", methods=["GET"])
def history():
    return jsonify(get_history())


@app.route("/api/history/clear", methods=["POST"])
def history_clear():
    clear_history()
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
