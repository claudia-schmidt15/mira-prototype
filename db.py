import psycopg2
import os

def get_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
        dbname=os.getenv("POSTGRES_DB", "mira"),
        user=os.getenv("POSTGRES_USER", "mira"),
        password=os.getenv("POSTGRES_PASSWORD", "mira")
    )
