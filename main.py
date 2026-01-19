from typing import List
from datetime import datetime
import json
import psycopg2

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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
app.mount("/static", StaticFiles(directory="static"), name="static")

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
# 🧠 SAFETY-WEIGHTED ROUTE
# -------------------------
@app.get("/route")
def get_route(
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    safety_weight: float = 0.5
):
    safety_weight = max(0.0, min(1.0, safety_weight))

    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="mira",
        user="mira",
        password="mira"
    )
    cur = conn.cursor()

    sql = """
    WITH
    start_node AS (
      SELECT node_id
      FROM routing_nodes
      ORDER BY geom <-> ST_SetSRID(ST_Point(%s, %s), 4326)
      LIMIT 1
    ),
    start_component AS (
      SELECT component
      FROM pgr_connectedComponents(
        $$
        SELECT edge_id AS id, source, target, 1 AS cost
        FROM routing_edges_main
        $$
      )
      WHERE node = (SELECT node_id FROM start_node)
    ),
    end_node AS (
      SELECT rn.node_id
      FROM routing_nodes rn
      JOIN pgr_connectedComponents(
        $$
        SELECT edge_id AS id, source, target, 1 AS cost
        FROM routing_edges_main
        $$
      ) cc
        ON cc.node = rn.node_id
      JOIN start_component sc
        ON cc.component = sc.component
      ORDER BY rn.geom <-> ST_SetSRID(ST_Point(%s, %s), 4326)
      LIMIT 1
    ),
    route AS (
      SELECT *
      FROM pgr_dijkstra(
        $$
        SELECT
          edge_id AS id,
          source,
          target,
          ((1 - %s) * length_m + %s * risk_cost) AS cost
        FROM routing_edges_main
        $$,
        (SELECT node_id FROM start_node),
        (SELECT node_id FROM end_node),
        directed := false
      )
    )
    SELECT
      ST_AsGeoJSON(ST_Union(rm.geom)),
      (SELECT node_id FROM start_node),
      (SELECT node_id FROM end_node)
    FROM route r
    JOIN routing_edges_main rm
      ON r.edge = rm.edge_id;
    """

    cur.execute(
        sql,
        (
            start_lng, start_lat,
            end_lng, end_lat,
            safety_weight, safety_weight
        )
    )

    result = cur.fetchone()
    cur.close()
    conn.close()

    if not result or not result[0]:
        return {
            "error": "No route found",
            "safety_weight": safety_weight
        }

    return {
        "type": "Feature",
        "geometry": json.loads(result[0]),
        "properties": {
            "start_node": result[1],
            "end_node": result[2],
            "safety_weight": safety_weight
        }
    }

# -------------------------
# 🚨 Existing test route
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

from fastapi import Query
from psycopg2.extras import RealDictCursor
from db import get_conn

@app.get("/v1/segments")
def get_segments(
    city_id: str = Query(...),
    min_lng: float = Query(...),
    min_lat: float = Query(...),
    max_lng: float = Query(...),
    max_lat: float = Query(...)
):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT jsonb_build_object(
  'type', 'FeatureCollection',
  'features', jsonb_agg(
    jsonb_build_object(
      'type', 'Feature',
      'geometry', ST_AsGeoJSON(geom)::jsonb,
      'properties', jsonb_build_object(
        'osm_id', osm_id,
        'name', name,
        'highway', highway,
        'safety_score', safety_score,
        'length_m', length_m
      )
    )
  )
) AS geojson
FROM (
    SELECT osm_id, name, highway, safety_score, length_m, geom
    FROM road_segments
    WHERE city_id = %s
      AND geom && ST_MakeEnvelope(%s, %s, %s, %s, 4326)
    LIMIT 500
) AS limited_segments;


            """, (city_id, min_lng, min_lat, max_lng, max_lat))

            row = cur.fetchone()
            return row["geojson"] if row["geojson"] else {
                "type": "FeatureCollection",
                "features": []
            }
    finally:
        conn.close()





