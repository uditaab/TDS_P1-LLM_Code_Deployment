import os, re, httpx
# from utils.config import AIPIPE_API_URL, AIPIPE_API_KEY

AIPIPE_API_URL = os.getenv("AIPIPE_API_URL")
AIPIPE_API_KEY = os.getenv("AIPIPE_API_KEY")

async def generate_app_code(brief: str, attachments: list):
    """Generate initial app code using AI Pipe, with attachments."""
    headers = {"Authorization": f"Bearer {AIPIPE_API_KEY}", "Content-Type": "application/json"}

    attach_text = ""
    for a in attachments:
        attach_text += f"\nAttachment: {a['name']} - Data: {a['url']}\n"

    payload = {
        "model": "gpt-4.1-nano",
        "messages": [
            {"role": "system", "content": f"You are a helpful assistant that generates minimal web apps based on the brief provided by the user.\n\nThe attachment file(s) are embedded directly in the request (if any) as Base64-encoded data — decode it to get the original file content.\n\nYour code will be checked against the given brief strictly, so do adhere to them, and don't miss anything provided."},
            {"role": "user", "content": f"Brief: {brief}\nAttachments (Provided in the format: ['attachment name' - Data: 'Data URI']):\n{attach_text}\nReturn full HTML code with inline CSS/JS. Parse the Data URIs correctly to include images or other media in the code as needed."},
        ],
        "temperature": 0.3,
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(200.0)) as client:
        resp = await client.post(AIPIPE_API_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    code = data["choices"][0]["message"]["content"]
    code = re.sub(r"^```(?:html)?\s*|```$", "", code.strip(), flags=re.IGNORECASE)
    readme = f"# \n\nGenerated via AI Pipe for the following brief:\n{brief}.\n\n## Setup:\nOpen index.html in your browser."
    return code, readme

async def modify_app_code(existing_code: str, new_brief: str, attachments: list):
    """Modify existing code based on new brief and attachments."""
    headers = {"Authorization": f"Bearer {AIPIPE_API_KEY}", "Content-Type": "application/json"}

    attach_text = ""
    for a in attachments:
        attach_text += f"\nAttachment: {a['name']}\nData: {a['url']}\n"

    payload = {
        "model": "gpt-4.1-nano",
        "messages": [
            {"role": "system", "content": f"You are an assistant that updates a pre-existing simple webapps based on the new requirements provided by the user in a brief, and return the newly generated webapp code only.\n\nThe attachment file(s) are embedded directly in the request (if any) as Base64-encoded data — decode it to get the original file content.\n\nYour code will be checked against the given brief strictly, so do adhere to them, and don't miss anything provided.\n\nExisting Code:\n{existing_code}"},

            {"role": "user", "content": f"Brief to be used for updating the existing code:\n{new_brief};\n\nAttachments (encoded in base64): {attach_text}\n\nReturn only updated complete HTML code, with inline CSS/JS if and when required. You have all the sylistic freedom, so aim to make it look good!"},
        ],
        "temperature": 0.3,
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(200.0)) as client:
        resp = await client.post(AIPIPE_API_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    updated_code = data["choices"][0]["message"]["content"]
    updated_code = re.sub(r"^```(?:html)?\s*|```$", "", updated_code.strip(), flags=re.IGNORECASE)
    updated_readme = f"# Update Round 2\n\nBrief: {new_brief}\n\nUpdated version of previous app."
    return updated_code, updated_readme
