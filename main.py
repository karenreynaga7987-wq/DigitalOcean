from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import requests
import os
import logging
import json
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: Optional[str] = "gpt-4"
    messages: List[Message]


# Backend LLM endpoints
BACKEND_URL = os.getenv("LLM_ENDPOINT", "http://localhost:8001")
SHADOW_BACKEND_URL = os.getenv("SHADOW_LLM_ENDPOINT", "http://localhost:8002")


def compare_and_log_payloads(correlation_id: str, request_body: dict, primary_payload: dict):
    if not SHADOW_BACKEND_URL:
        return

    try:
        shadow_response = requests.post(
            f"{SHADOW_BACKEND_URL}/v1/chat/completions",
            json=request_body,
            timeout=30,
        )
        shadow_payload = shadow_response.json()

        if primary_payload != shadow_payload:
            logger.warning(f"[{correlation_id}] MISMATCH detected between primary and shadow:")
            logger.info(f"[{correlation_id}] PRIMARY_PAYLOAD: {json.dumps(primary_payload)}")
            logger.info(f"[{correlation_id}] SHADOW_PAYLOAD: {json.dumps(shadow_payload)}")
        else:
            logger.info(f"[{correlation_id}] Payloads match")

    except Exception as e:
        logger.error(f"[{correlation_id}] Shadow comparison error: {e}")


@app.post("/v1/chat/completions")
def chat_completions(req: ChatRequest, background_tasks: BackgroundTasks):
    correlation_id = str(uuid.uuid4())
    request_body = req.model_dump()

    try:
        response = requests.post(
            f"{BACKEND_URL}/v1/chat/completions",
            json=request_body,
            timeout=30,
        )
        response.raise_for_status()
        primary_payload = response.json()
    except Exception as e:
        return {
            "error": str(e),
            "id": "error-1",
            "object": "chat.completion",
        }

    # Run shadow comparison in background
    background_tasks.add_task(compare_and_log_payloads, correlation_id, request_body, primary_payload)

    return primary_payload
