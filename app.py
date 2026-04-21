import os
import psycopg
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://{user}:{password}@{host}:{port}/{dbname}".format(
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres"),
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "postgres"),
    ),
)

SQL_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>Postgres Query Runner</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
           background: #0d1117; color: #c9d1d9; padding: 2rem; }
    h1 { color: #58a6ff; margin-bottom: 0.5rem; }
    .subtitle { color: #8b949e; margin-bottom: 1.5rem; }
    textarea { width: 100%%; height: 120px; background: #161b22; color: #c9d1d9;
               border: 1px solid #30363d; border-radius: 6px; padding: 12px;
               font-family: 'SFMono-Regular', Consolas, monospace; font-size: 14px;
               resize: vertical; }
    textarea:focus { outline: none; border-color: #58a6ff; }
    button { background: #238636; color: #fff; border: none; padding: 10px 24px;
             border-radius: 6px; font-size: 14px; cursor: pointer; margin-top: 0.75rem; }
    button:hover { background: #2ea043; }
    .results { margin-top: 1.5rem; }
    table { width: 100%%; border-collapse: collapse; background: #161b22;
            border-radius: 6px; overflow: hidden; }
    th { background: #21262d; color: #58a6ff; text-align: left;
         padding: 10px 14px; font-size: 13px; border-bottom: 1px solid #30363d; }
    td { padding: 8px 14px; border-bottom: 1px solid #21262d; font-size: 13px;
         font-family: 'SFMono-Regular', Consolas, monospace; }
    tr:hover td { background: #1c2128; }
    .error { background: #3d1a1a; border: 1px solid #f85149; color: #f85149;
             padding: 12px; border-radius: 6px; margin-top: 1rem;
             font-family: monospace; white-space: pre-wrap; }
    .info { color: #8b949e; margin-top: 0.75rem; font-size: 13px; }
    .badge { display: inline-block; background: #21262d; border: 1px solid #30363d;
             padding: 2px 8px; border-radius: 12px; font-size: 12px; color: #8b949e; }
  </style>
</head>
<body>
  <h1>🐘 Postgres Query Runner</h1>
  <p class="subtitle">Run SQL queries against the database</p>
  <form method="POST" action="/query">
    <textarea name="sql" placeholder="SELECT * FROM greetings;">{{ query or '' }}</textarea>
    <br>
    <button type="submit">▶ Run Query</button>
  </form>
  {% if error %}
    <div class="error">{{ error }}</div>
  {% endif %}
  {% if columns %}
    <div class="results">
      <p class="info">
        <span class="badge">{{ rows|length }} row{{ 's' if rows|length != 1 }}</span>
        &nbsp;{{ columns|length }} column{{ 's' if columns|length != 1 }}
      </p>
      <table>
        <thead><tr>{% for col in columns %}<th>{{ col }}</th>{% endfor %}</tr></thead>
        <tbody>
          {% for row in rows %}
          <tr>{% for val in row %}<td>{{ val }}</td>{% endfor %}</tr>
          {% endfor %}
          {% if not rows %}
          <tr><td colspan="{{ columns|length }}" style="text-align:center;color:#8b949e">
            No rows returned</td></tr>
          {% endif %}
        </tbody>
      </table>
    </div>
  {% endif %}
  {% if message %}
    <div class="info" style="margin-top:1rem;color:#3fb950">✓ {{ message }}</div>
  {% endif %}
</body>
</html>
"""


def get_db():
    conn = psycopg.connect(DB_URL, autocommit=True)
    return conn


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


@app.route("/query", methods=["GET", "POST"])
def query_page():
    """Web UI for running arbitrary SQL queries."""
    query = ""
    columns = None
    rows = None
    error = None
    message = None

    if request.method == "POST":
        query = request.form.get("sql", "").strip()
        if not query:
            error = "Please enter a SQL query."
        else:
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute(query)
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    rows = [[str(v) for v in row] for row in cur.fetchall()]
                else:
                    message = f"Query executed successfully. Rows affected: {cur.rowcount}"
                cur.close()
                conn.close()
            except Exception as e:
                error = str(e)

    return render_template_string(SQL_PAGE, query=query, columns=columns,
                                  rows=rows, error=error, message=message)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
