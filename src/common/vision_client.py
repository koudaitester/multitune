import requests
from core.logger import logger
from core.config import cfg

async def vision_predict(img_b64: str, prompt: str) -> str:
    payload = {
        "model": cfg.ollama_vision_model,
        "prompt": prompt,
        "images": [img_b64],
        "stream": False,
        "options": {"temperature": 0, "num_predict": 512}
    }
    logger.info(f"VL payload: {payload}")
    try:
        resp = requests.post(
            f"{cfg.ollama_base_url}/api/generate",
            json=payload,
            timeout=cfg.vision_timeout
        )
        resp.raise_for_status()
        logger.info(f"VL response status: {resp.status_code}")
        logger.info(f"VL response content: {resp.text}")
        raw = resp.json().get("response", "").strip().lower()
        logger.info(f"VL raw output: {raw}")
        return raw
    except Exception as e:
        logger.exception("vision client call error")
        logger.error(f"vision client call error: {e}")
        return ""
