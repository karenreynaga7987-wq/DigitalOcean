from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import time

app = FastAPI()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: Optional[str] = "gpt-4"
    messages: List[Message]

@app.post("/v1/chat/completions")
def chat_completions(req: ChatRequest):
    last = req.messages[-1].content if req.messages else ""
    resp_text = f"Backend mock reply: {last}"
    return {
        "id": "mockcmpl-1",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": resp_text},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }

