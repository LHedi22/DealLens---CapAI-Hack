import httpx
import json
import logging
import time

logger = logging.getLogger(__name__)

OLLAMA_BASE = "http://localhost:11434"
MODEL_A = "mistral"
MODEL_B = "llama3.2:3b"


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
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(f"{OLLAMA_BASE}/api/chat", json=payload)
            response.raise_for_status()
            content = response.json()["message"]["content"].strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content.strip()), content.strip()

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
        emit_log("ERROR", "ollama", "Ollama unreachable", {
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
            return r.status_code == 200
    except Exception:
        return False
