from typing import List
from datetime import datetime
import json
import psycopg2

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# -------------------------
# Whisper scoring config
# -------------------------
WHISPER_WEIGHTS = {
    "Well-lit": 10,
    "Busy": 5,
    "Empty": -5,
    "Sketchy": -15
}

# In-memory store (prototype only)
whispers: List[dict] = []

# -------------------------
# App setup
# -------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # OK for prototype
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Health
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# -------------------------
# Route scoring (existing)
# -------------------------
@app.post("/score/route")
def score_route():
    base_score = 60

    score = base_score
    for w in whispers[-3:]:
        impact = WHISPER_WEIGHTS.get(w["value"], 0)
        score += impact

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

# -------------------------
# Whisper endpoints
# -------------------------
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
    return {"whispers": whispers[-limit:] if whispers else []}

# -------------------------
# 🚨 NEW: Safest route API
# -------------------------
@app.get("/route/test")
def test_route():
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="mira",
        user="mira",
        password="mira"
    )
    cur = conn.cursor()

    cur.execute("""
        WITH route AS (
          SELECT *
          FROM pgr_dijkstra(
            $$
            SELECT edge_id AS id, source, target, risk_cost AS cost
            FROM routing_edges_main
            $$,
            602393,
            606661,
            directed := false
          )
        )
        SELECT ST_AsGeoJSON(ST_Union(e.geom))
        FROM route r
        JOIN routing_edges_main e
          ON r.edge = e.edge_id;
    """)

    result = cur.fetchone()
    cur.close()
    conn.close()

    if not result or not result[0]:
        return {"error": "No route"}

    return {
        "type": "Feature",
        "geometry": json.loads(result[0]),
        "properties": {
            "start_node": 602393,
            "end_node": 606661
        }
    }



