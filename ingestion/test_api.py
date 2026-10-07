import os
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}

def fetch_commits(owner: str, repo: str, per_page: int = 30):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    response = requests.get(
        url, headers=HEADERS, params={"per_page": per_page}, timeout=30
    )
    response.raise_for_status()
    print("Rate limit remaining:", response.headers.get("X-RateLimit-Remaining"))
    return response.json()

if __name__ == "__main__":
    commits = fetch_commits("apache", "airflow")
    for c in commits[:5]:
        info = c["commit"]
        print(
            c["sha"][:7],
            info["author"]["date"],
            info["author"]["name"],
            "|",
            info["message"].split("\n")[0],
        )