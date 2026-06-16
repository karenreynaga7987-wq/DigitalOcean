
## Running the System

**Terminal 1 — Primary Backend:**
```bash
cd /workspaces && python -m uvicorn backend:app --port 8001
```

**Terminal 2 — Shadow Backend (optional):**
```bash
cd /workspaces && python -m uvicorn backend:app --port 8002
```

**Terminal 3 — Proxy:**
```bash
cd /workspaces && python -m uvicorn main:app --port 8000
```

**Terminal 4 — Test:**
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

## Sample Requests and Expected Responses

**Request:**
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

**Expected Response (200):**
```json
{
  "id": "mockcmpl-1",
  "object": "chat.completion",
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Backend mock reply: Hello"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 5,
    "total_tokens": 15
  }
}
```

## Background Task Decoupling

Shadow requests run asynchronously via `FastAPI.BackgroundTasks`.
Primary response returns to client immediately as shadow request executes in background, so failures in shadow do not affect primary response.
Payloads of the primary and shadow are compared asynchronously, and logged when a mismatch is identified.

This is covered in the `test_shadow_isolation.py` suite.


## Running unit tests

```bash
 /usr/local/python/3.14.6/bin/python -m pytest 
 ```