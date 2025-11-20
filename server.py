import os
import json
import base64
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

app = FastAPI()

# CORS for GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://raja030972.github.io", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HistoryItem(BaseModel):
    role: str
    content: str

@app.post("/chat")
async def chat(
    payload: str = Form(...),
    files: Optional[List[UploadFile]] = File(None)
):

    try:
        data = json.loads(payload)
        text = data["message"]
        history = data.get("history", [])
    except Exception as ex:
        return {"error": f"Invalid JSON: {ex}"}

    extra_text = ""
    image_parts = []

    if files:
        for f in files:
            raw = await f.read()
            ct = f.content_type or ""

            if ct.startswith("text/") or any(f.filename.endswith(ext) for ext in [".css", ".html", ".js", ".txt"]):
                extra_text += f"\n--- {f.filename} ---\n" + raw.decode("utf-8", "ignore") + "\n"
            elif ct.startswith("image/"):
                b64 = base64.b64encode(raw).decode()
                image_parts.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{ct};base64,{b64}"}
                })

    content_parts = [
        {"type": "text", "text": f"User:\n{text}"},
        {"type": "text", "text": extra_text}
    ] + image_parts

    messages = [
        {"role": "system", "content": "You are a Power Apps / Power Pages architect."},
        *history,
        {"role": "user", "content": content_parts}
    ]

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages
        )
        reply = completion.choices[0].message.content
        return {"reply": reply}
    except Exception as ex:
        return {"error": str(ex)}
