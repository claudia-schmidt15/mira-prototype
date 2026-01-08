from typing import List
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

WHISPER_WEIGHTS = {
    "Well-lit": 10,
    "Busy": 5,
    "Empty": -5,
    "Sketchy": -15
}

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
    base_score = 60  # neutral starting point

    # Apply whisper effects
    score = base_score
    for w in whispers[-3:]:  # use last 3 whispers
        impact = WHISPER_WEIGHTS.get(w["value"], 0)
        score += impact

    # Clamp score between 0 and 100
    score = max(0, min(100, score))

    if score >= 70:
        label = "comfortable"
    elif score >= 40:
        label = "mixed"
    else:
        label = "avoid"

    return {
        "city": "NYC",
        "score": score,
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

@app.get("/whisper/recent")
def get_recent_whispers(limit: int = 3):
    return {
        "whispers": whispers[-limit:] if whispers else []
    }


