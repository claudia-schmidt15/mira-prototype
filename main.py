from typing import List
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# In-memory store for whispers (temporary)
whispers: List[dict] = []

app = FastAPI()

# Allow Chrome extension + Google Maps to talk to us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # OK for prototype
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/score/route")
def score_route():
    demo_score = 25  # 🔧 change this number to demo different routes

    if demo_score >= 70:
        label = "comfortable"
    elif demo_score >= 40:
        label = "mixed"
    else:
        label = "avoid"

    return {
        "city": "NYC",
        "score": demo_score,
        "label": label
    }

@app.post("/whisper")
def add_whisper(data: dict):
    whisper = {
        "value": data.get("value"),
        "timestamp": datetime.utcnow().isoformat()
    }
    whispers.append(whisper)
    return {"status": "ok", "whisper": whisper}

@app.get("/whisper/latest")
def get_latest_whisper():
    if not whispers:
        return {"whisper": None}
    return {"whisper": whispers[-1]}


