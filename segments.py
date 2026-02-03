from fastapi import APIRouter, Query
from psycopg2.extras import RealDictCursor

from db import get_conn

router = APIRouter()


@router.get("")
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
            cur.execute(
                """
                SELECT jsonb_build_object(
                  'type', 'FeatureCollection',
                  'features', COALESCE(jsonb_agg(
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
                  ), '[]'::jsonb)
                ) AS geojson
                FROM (
                    SELECT osm_id, name, highway, safety_score, length_m, geom
                    FROM road_segments
                    WHERE city_id = %s
                      AND geom && ST_MakeEnvelope(%s, %s, %s, %s, 4326)
                    LIMIT 500
                ) s;
                """,
                (city_id, min_lng, min_lat, max_lng, max_lat),
            )

            row = cur.fetchone()
            return row["geojson"]

    finally:
        conn.close()
