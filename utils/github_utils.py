import os, requests
from github import Github
# from utils.config import GITHUB_TOKEN, GITHUB_USERNAME

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

def fetch_existing_repo_and_code(repo_name):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(f"{GITHUB_USERNAME}/{repo_name}")
    index_file = repo.get_contents("index.html")
    return repo, index_file.decoded_content.decode("utf-8")

async def create_and_deploy_repo(task, code, readme):
    """Create a GitHub repo, push files, and enable GitHub Pages."""
    g = Github(GITHUB_TOKEN)
    user = g.get_user()

    repo_name = task.replace(' ', '-')
    repo = user.create_repo(repo_name, private=False, auto_init=False)

    mitLicense = """MIT License

Copyright (c) 2025 Udita Bagchi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

    # Commit files
    repo.create_file("index.html", "initial commit", code)
    repo.create_file("README.md", "add readme", readme)
    repo.create_file("LICENSE", "add license", mitLicense)

    # Enable GitHub Pages (via REST API)
    pages_api = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/pages"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    payload = {"source": {"branch": "main", "path": "/"}}
    requests.post(pages_api, headers=headers, json=payload)

    # Build response data
    pages_url = f"https://{GITHUB_USERNAME}.github.io/{repo_name}/"
    commit_sha = repo.get_commits()[0].sha
    repo_url = repo.html_url

    return repo_url, commit_sha, pages_url

async def update_existing_repo(repo, updated_code, updated_readme):
    """Commit updates to existing repo and redeploy Pages."""
    index_file = repo.get_contents("index.html")
    readme_file = repo.get_contents("README.md")

    repo.update_file(index_file.path, "update app for round 2", updated_code, index_file.sha)
    repo.update_file(readme_file.path, "update readme for round 2", updated_readme, readme_file.sha)

    commit_sha = repo.get_commits()[0].sha
    pages_url = f"https://{GITHUB_USERNAME}.github.io/{repo.name}/"
    return commit_sha, pages_url
