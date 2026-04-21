import os
import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": os.getenv("PGPORT", "5432"),
    "dbname": os.getenv("PGDATABASE", "postgres"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", "postgres"),
}


def get_db():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    return conn


def init_db():
    """Create the greetings table if it doesn't exist."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS greetings (
                id SERIAL PRIMARY KEY,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.close()
        conn.close()
    except Exception:
        pass  # DB may not be available yet


@app.route("/")
def hello():
    """Insert a greeting and return all greetings."""
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS greetings (
                id SERIAL PRIMARY KEY,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        cur.execute(
            "INSERT INTO greetings (message) VALUES (%s) RETURNING id",
            ("Hello, World!",),
        )
        new_id = cur.fetchone()[0]

        cur.execute("SELECT id, message, created_at FROM greetings ORDER BY id")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify({
            "inserted_id": new_id,
            "greetings": [
                {"id": r[0], "message": r[1], "created_at": str(r[2])}
                for r in rows
            ],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
