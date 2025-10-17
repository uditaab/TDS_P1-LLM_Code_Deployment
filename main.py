import traceback
import os, httpx, asyncio
# from utils.config import STUDENT_SECRET
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request, HTTPException
from utils.repo_db import set_repo_data, get_repo_data
from utils.ai_generator import generate_app_code, modify_app_code
from utils.github_utils import create_and_deploy_repo, update_existing_repo, fetch_existing_repo_and_code

STUDENT_SECRET = os.getenv("STUDENT_SECRET")

app = FastAPI(title="LLM Code Deployment API")

@app.post("/api-endpoint")
async def handle_task(request: Request):
    data = await request.json()
    print("Received task:", data.get("task"), "round:", data.get("round"))

    # Verify secret
    if data.get("secret") != STUDENT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    # Respond immediately
    response = {"status": "ok", "message": "Task received"}

    print(f"Received task for Round {data.get("round")}...")

    if data.get("round") == 1:
        asyncio.create_task(process_task_r1(data))
    elif data.get("round") == 2:
        asyncio.create_task(process_task_r2(data))

    return JSONResponse(content=response)


# ---------------- ROUND 1 ----------------
async def process_task_r1(data):
    """Build the app, deploy to GitHub Pages, and notify evaluation API."""
    try:
        email = data["email"]
        task = data["task"]
        round_ = data["round"]
        nonce = data["nonce"]
        brief = data["brief"]
        checks = data["checks"]
        eval_url = data["evaluation_url"]
        attachments = data.get("attachments", [])

        print(f"Starting Round 1 for task: {task}")

        # Step 1. Generate code using AI Pipe, including attachments
        code, readme = await generate_app_code(brief, attachments)
        print("1.1. Generated app code.")

        # Step 2. Push to GitHub and enable Pages
        repo_url, commit_sha, pages_url = await create_and_deploy_repo(task, code, readme)
        print("1.2. Created and published Github Repo.")

        # Step 3. Save repo mapping for future rounds
        repo_name = repo_url.split("/")[-1]
        set_repo_data(task, repo_name, repo_url)
        print("1.3. Saved repo data for future rounds.")

        # Step 4. Notify evaluation API
        payload = {
            "email": email,
            "task": task,
            "round": round_,
            "nonce": nonce,
            "repo_url": repo_url,
            "commit_sha": commit_sha,
            "pages_url": pages_url
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(100.0)) as client:
            r = await client.post(eval_url, json=payload, timeout=30)
            r.raise_for_status()
            print(f"1.4. Evaluation notified for {task}")

    except Exception as e:
        print(f"{repr(e)} - Error during Round 1 process: {e}")
        traceback.print_exc()


# ---------------- ROUND 2 ----------------
async def process_task_r2(data):
    """Modify existing app based on new brief, update GitHub Pages, notify evaluation API."""
    try:
        email = data["email"]
        task = data["task"]
        round_ = data["round"]
        nonce = data["nonce"]
        brief = data["brief"]
        # checks = data["checks"]
        eval_url = data["evaluation_url"]
        attachments = data.get("attachments", [])

        print(f"Starting Round 2 update for {task}")

        # Step 1. Retrieve repo name from persistent mapping
        repo = get_repo_data(task)
        if not repo:
            print(f"2.1. Repo for task '{task}' not found!")
            return
        else:
            print(f"2.1. Found repo '{repo["repo_name"]}' for task '{task}'")

        # Step 2. Fetch existing repo and code
        repo, existing_code = fetch_existing_repo_and_code(repo["repo_name"])

        print("2.2. Fetched existing code in Repo.")

        # Step 3. Modify code using AI Pipe, include attachments
        updated_code, updated_readme = await modify_app_code(existing_code, brief, attachments)
        print("2.3. Generated updated code.")

        # Step 4. Commit updated code and README
        commit_sha, pages_url = await update_existing_repo(repo, updated_code, updated_readme)
        print("2.4. Updated existing code in Repo.")

        # Step 5. Notify evaluation API
        payload = {
            "email": email,
            "task": task,
            "round": round_,
            "nonce": nonce,
            "repo_url": repo.html_url,
            "commit_sha": commit_sha,
            "pages_url": pages_url
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            r = await client.post(eval_url, json=payload, timeout=30)
            r.raise_for_status()

        print(f"2.5. Round 2 evaluation notified for {task}")

    except Exception as e:
        print(f"{repr(e)} - Error during Round 2 process: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
