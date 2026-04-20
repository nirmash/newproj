import os
import psycopg2

DB_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": os.getenv("PGPORT", "5432"),
    "dbname": os.getenv("PGDATABASE", "postgres"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", "postgres"),
}


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()

    # Create table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS greetings (
            id SERIAL PRIMARY KEY,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # Write
    cur.execute(
        "INSERT INTO greetings (message) VALUES (%s) RETURNING id",
        ("Hello, World!",),
    )
    row_id = cur.fetchone()[0]
    print(f"Inserted greeting with id={row_id}")

    # Read
    cur.execute("SELECT id, message, created_at FROM greetings ORDER BY id")
    rows = cur.fetchall()
    print(f"\nAll greetings ({len(rows)} total):")
    for row in rows:
        print(f"  [{row[0]}] {row[1]}  (at {row[2]})")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
