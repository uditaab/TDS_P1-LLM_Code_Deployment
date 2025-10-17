# utils/repo_db.py
import json
import os

# File to store repo mapping
DB_FILE = "repos.json"

# ---------------- Load existing mapping ----------------
def load_mapping():
    """Load the repo mapping from JSON file."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Warning: repos.json is invalid, resetting mapping.")
            return {}
    return {}

# ---------------- Save mapping ----------------
def save_mapping(mapping):
    """Save the repo mapping to JSON file."""
    with open(DB_FILE, "w") as f:
        json.dump(mapping, f, indent=2)

# ---------------- Set repo for a task ----------------
def set_repo_data(task: str, repo_name: str, repo_url: str):
    """
    Store repo info for a task.
    task: str - task identifier (same across rounds)
    repo_name: str - GitHub repo name
    repo_url: str - full GitHub repo URL
    """
    mapping = load_mapping()
    mapping[task] = {
        "repo_name": repo_name,
        "repo_url": repo_url
    }
    save_mapping(mapping)

# ---------------- Get repo info for a task ----------------
def get_repo_data(task: str):
    """
    Retrieve repo info for a task.
    Returns dict: {"repo_name": ..., "repo_url": ...} or None if not found.
    """
    mapping = load_mapping()
    return mapping.get(task)
