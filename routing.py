import json
from fastapi import APIRouter
import psycopg2

from db import get_conn

# --------------------------------------------------
# Router
# --------------------------------------------------
router = APIRouter()


# --------------------------------------------------
# SAFETY-WEIGHTED ROUTE (PostGIS + pgRouting)
# --------------------------------------------------
@router.get("/")
def get_route(
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    safety_weight: float = 0.5
):
    """
    Returns a safety-weighted walking route between two points.

    safety_weight:
      0.0 → shortest distance
      1.0 → safest route
    """
    safety_weight = max(0.0, min(1.0, safety_weight))

    conn = get_conn()
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
        ST_AsGeoJSON(ST_Union(e.geom)),
        (SELECT node_id FROM start_node),
        (SELECT node_id FROM end_node)
    FROM route r
    JOIN routing_edges_main e
      ON r.edge = e.edge_id;
    """

    cur.execute(
        sql,
        (
            start_lng, start_lat,
            end_lng, end_lat,
            safety_weight, safety_weight
        )
    )

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row or not row[0]:
        return {
            "error": "No route found",
            "safety_weight": safety_weight
        }

    return {
        "type": "Feature",
        "geometry": json.loads(row[0]),
        "properties": {
            "start_node": row[1],
            "end_node": row[2],
            "safety_weight": safety_weight
        }
    }

# --------------------------------------------------
# TEST ROUTE (known nodes)
# --------------------------------------------------
@router.get("/test")
def test_route():
    """
    Hardcoded test route for debugging geometry output.
    """
    conn = get_conn()
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

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row or not row[0]:
        return {"error": "No route"}

    return {
        "type": "Feature",
        "geometry": json.loads(row[0]),
        "properties": {
            "start_node": 602393,
            "end_node": 606661
        }
    }
