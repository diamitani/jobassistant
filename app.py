from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse

app = FastAPI()

# Enable CORS for any frontend like v0.dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load DeepSeek API Key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


@app.post("/parse-resume")
async def parse_resume(file: UploadFile = File(...)):
    text = await file.read()
    resume_text = text.decode("utf-8", errors="ignore")

    if not DEEPSEEK_API_KEY:
        return {"mode": "demo", "summary": "John Doe, skilled in Python, ML, and AWS."}

    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Summarize this resume and extract skills."},
                    {"role": "user", "content": resume_text}
                ]
            },
            timeout=30
        )
        summary = response.json()["choices"][0]["message"]["content"]
        return {"mode": "live", "summary": summary}

    except Exception as e:
        return {"mode": "demo", "summary": "John Doe, skilled in Python, ML, and AWS.", "error": str(e)}


@app.get("/search-jobs")
def search_jobs(query: str = "AI Engineer", location: str = "Remote"):
    try:
        url = f"https://remoteok.com/remote-{query.lower().replace(' ', '-')}-jobs"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')

        jobs = []
        for div in soup.find_all("tr", class_="job")[:10]:
            title_tag = div.find("h2")
            link_tag = div.find("a", href=True)
            if title_tag and link_tag:
                jobs.append({
                    "title": title_tag.text.strip(),
                    "link": "https://remoteok.com" + link_tag["href"]
                })
        return {"jobs": jobs}
    except Exception as e:
        return {"error": str(e), "jobs": []}


@app.post("/parse-job-link")
async def parse_job_link(url: str):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.find("h1") or soup.find("h2")
        description = (
            soup.find("div", class_="description")
            or soup.find("div", class_="job-description")
            or soup.find("article")
        )

        return {
            "title": title.get_text(strip=True) if title else "N/A",
            "description": description.get_text(strip=True)[:1000] if description else "N/A",
            "source": urlparse(url).netloc,
            "link": url
        }

    except Exception as e:
        return {"error": str(e)}


# Optional: Local dev only
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
