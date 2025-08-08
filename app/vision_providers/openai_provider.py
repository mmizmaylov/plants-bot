import os
from typing import Any, Dict, Optional

from openai import AsyncOpenAI

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        _client = AsyncOpenAI(api_key=api_key)
    return _client


def _strip_code_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        lines = t.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```"):
            lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            return "\n".join(lines).strip()
    return t


async def analyze_plant(
    image_data_url: Optional[str] = None, 
    system_prompt: str = "", 
    text_description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Анализирует растение по фото, текстовому описанию или их комбинации.
    
    Args:
        image_data_url: Base64 изображение в формате data:image/jpeg;base64,... (опционально)
        system_prompt: Системный промпт
        text_description: Текстовое описание растения (опционально)
    
    Returns:
        Словарь с анализом растения
    """
    model = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")
    client = _get_client()

    # Формируем инструкцию в зависимости от входных данных
    if image_data_url and text_description:
        user_instruction = (
            f"Проанализируй изображение растения и дополнительное описание: '{text_description}'. "
            "Учти оба источника информации при анализе. "
            "Верни информацию о растении в формате JSON с ключами: "
            "plant_name (строка), scientific_name (строка), family (строка), "
            "description (строка), care_tips (строка), fun_facts (строка), "
            "is_toxic (boolean), difficulty (easy/medium/hard), low_quality (boolean). Без комментариев."
        )
        content = [
            {"type": "text", "text": user_instruction},
            {"type": "image_url", "image_url": {"url": image_data_url, "detail": "auto"}},
        ]
    elif image_data_url:
        user_instruction = (
            "Проанализируй изображение растения и верни информацию о нём. Ответ строго в формате JSON с ключами: "
            "plant_name (строка), scientific_name (строка), family (строка), "
            "description (строка), care_tips (строка), fun_facts (строка), "
            "is_toxic (boolean), difficulty (easy/medium/hard), low_quality (boolean). Без комментариев."
        )
        content = [
            {"type": "text", "text": user_instruction},
            {"type": "image_url", "image_url": {"url": image_data_url, "detail": "auto"}},
        ]
    elif text_description:
        user_instruction = (
            f"Проанализируй описание растения: '{text_description}'. "
            "Определи растение и дай информацию о нём на основе описания. "
            "Верни информацию в формате JSON с ключами: "
            "plant_name (строка), scientific_name (строка), family (строка), "
            "description (строка), care_tips (строка), fun_facts (строка), "
            "is_toxic (boolean), difficulty (easy/medium/hard), low_quality (boolean). "
            "Поскольку это текстовое описание, установи low_quality=false. Без комментариев."
        )
        content = [{"type": "text", "text": user_instruction}]
    else:
        # Если ничего не передано, возвращаем заглушку
        return {
            "plant_name": "Неизвестное растение",
            "scientific_name": None,
            "family": None,
            "description": "Не удалось определить растение",
            "care_tips": None,
            "fun_facts": None,
            "is_toxic": None,
            "difficulty": None,
            "low_quality": True,
        }

    resp = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        temperature=0.2,
        max_tokens=800,
    )

    content_text = resp.choices[0].message.content or "{}"
    content_text = _strip_code_fences(content_text)
    try:
        import json
        data = json.loads(content_text)
        if not isinstance(data, dict):
            raise ValueError
        return data
    except Exception:
        return {
            "plant_name": "Растение",
            "scientific_name": None,
            "family": None,
            "description": "Не удалось получить подробную информацию",
            "care_tips": None,
            "fun_facts": None,
            "is_toxic": None,
            "difficulty": None,
            "low_quality": False,
        } 