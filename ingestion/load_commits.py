import os
import requests
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
    "Accept": "application/vnd.github+json",
}

REPOS = [
    ("apache", "airflow"),
    ("dbt-labs", "dbt-core"),
    ("pandas-dev", "pandas"),
]


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def create_table(conn):
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS raw.commits (
                repo         TEXT NOT NULL,
                sha          TEXT NOT NULL,
                author_name  TEXT,
                author_date  TIMESTAMPTZ,
                message      TEXT,
                payload      JSONB,
                loaded_at    TIMESTAMPTZ DEFAULT now(),
                PRIMARY KEY (repo, sha)
            );
            """
        )
    conn.commit()


def fetch_commits(owner, repo, per_page=100):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    response = requests.get(
        url, headers=HEADERS, params={"per_page": per_page}, timeout=30
    )
    response.raise_for_status()
    print(
        f"{owner}/{repo}: fetched {len(response.json())} commits, "
        f"rate limit remaining {response.headers.get('X-RateLimit-Remaining')}"
    )
    return response.json()


def load_commits(conn, owner, repo, commits):
    full_name = f"{owner}/{repo}"
    with conn.cursor() as cur:
        for c in commits:
            info = c["commit"]
            cur.execute(
                """
                INSERT INTO raw.commits
                    (repo, sha, author_name, author_date, message, payload)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (repo, sha) DO NOTHING;
                """,
                (
                    full_name,
                    c["sha"],
                    info["author"]["name"],
                    info["author"]["date"],
                    info["message"],
                    Json(c),
                ),
            )
    conn.commit()


if __name__ == "__main__":
    conn = get_connection()
    create_table(conn)
    for owner, repo in REPOS:
        commits = fetch_commits(owner, repo)
        load_commits(conn, owner, repo, commits)
    conn.close()
    print("Done.")