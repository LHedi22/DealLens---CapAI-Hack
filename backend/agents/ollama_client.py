import httpx
import json
import logging
import os
import re
import time

logger = logging.getLogger(__name__)

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_A = "mistral"
MODEL_B = "qwen2.5:3b"


def _extract_json(content: str) -> str:
    """Extract a JSON object from a string that may contain prose or markdown."""
    content = content.strip()
    # Strip markdown code fences
    if content.startswith("```"):
        content = re.sub(r'^```(?:json)?\s*', '', content)
        content = re.sub(r'\s*```$', '', content).strip()
    # If it's already valid JSON, return as-is
    if content.startswith("{"):
        return content
    # Try to extract the first {...} block from surrounding prose
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        return match.group()
    return content


async def call_ollama(model: str, system_prompt: str, user_content: str,
                      agent: str = "unknown") -> dict:
    from backend.debug_state import emit_log, add_ollama_call

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1, "num_predict": 1500},
    }

    emit_log("DEBUG", "ollama", f"Prompt sent to {model}", {
        "agent": agent,
        "model": model,
        "system_prompt": system_prompt,
        "user_prompt": user_content,
        "user_prompt_preview": user_content[:300],
    })

    start = time.time()

    async def _attempt() -> tuple[dict, str]:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(f"{OLLAMA_BASE}/api/chat", json=payload)
            response.raise_for_status()
            resp_json = response.json()
            # Ollama returns {"error": "..."} when the model is not found or unavailable
            if "error" in resp_json:
                raise RuntimeError(f"Ollama model error: {resp_json['error']}")
            content = _extract_json(resp_json["message"]["content"])
            return json.loads(content), content

    try:
        result, raw = await _attempt()
        duration = int((time.time() - start) * 1000)
        emit_log("DEBUG", "ollama", f"Response received from {model}", {
            "agent": agent,
            "response_preview": raw[:300],
            "parse_success": True,
            "duration_ms": duration,
        })
        add_ollama_call(agent, model, system_prompt, user_content, raw, duration, True)
        return result
    except (json.JSONDecodeError, KeyError):
        emit_log("WARN", "ollama", "JSON parse failed — retrying", {
            "agent": agent,
        })
        logger.warning("Ollama JSON parse failed on first attempt. Retrying...")
        try:
            result, raw = await _attempt()
            duration = int((time.time() - start) * 1000)
            emit_log("DEBUG", "ollama", f"Response received from {model} (retry)", {
                "agent": agent,
                "response_preview": raw[:300],
                "parse_success": True,
                "duration_ms": duration,
            })
            add_ollama_call(agent, model, system_prompt, user_content, raw, duration, True)
            return result
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            emit_log("ERROR", "ollama", f"Ollama call failed after retry", {
                "agent": agent,
                "error": str(e),
            })
            add_ollama_call(agent, model, system_prompt, user_content,
                            f"PARSE FAILED: {e}", duration, False)
            logger.error(f"Ollama call failed after retry: {e}")
            return {}
    except Exception as e:
        duration = int((time.time() - start) * 1000)
        emit_log("ERROR", "ollama", "Ollama unreachable or model error", {
            "agent": agent,
            "error": str(e),
        })
        add_ollama_call(agent, model, system_prompt, user_content,
                        f"ERROR: {e}", duration, False)
        logger.error(f"Ollama call failed: {e}")
        return {}


async def check_ollama_available() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_BASE}/api/tags")
            if r.status_code != 200:
                return False
            # Verify that MODEL_A (mistral) is actually pulled, not just that the server runs
            models = r.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            return any(MODEL_A in name for name in model_names)
    except Exception:
        return False
