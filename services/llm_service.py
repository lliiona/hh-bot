import httpx
from typing import Optional
from config import config
from db.models import User, Vacancy, LLMSettings

async def generate_resume(user: User, vacancy: Vacancy, llm_settings: Optional[LLMSettings] = None) -> str:
    base_url = llm_settings.base_url if llm_settings else config.LLM_BASE_URL
    api_key = llm_settings.api_key if llm_settings else config.LLM_API_KEY
    model = llm_settings.model if llm_settings else config.LLM_MODEL

    if not base_url or not api_key:
        raise ValueError("LLM settings not configured")

    prompt = f"""
    Адаптируйте резюме пользователя под вакансию.

    Базовое резюме пользователя:
    {user.base_resume}

    Вакансия:
    Название: {vacancy.title}
    Компания: {vacancy.company}
    Описание: {vacancy.description}

    Сгенерируйте адаптированное резюме, выделив релевантные навыки и опыт.
    """

    messages = [{"role": "user", "content": prompt}]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": messages}
        )
        response.raise_for_status()
        data = response.json()

    return data['choices'][0]['message']['content']

async def generate_cover_letter(user: User, vacancy: Vacancy, llm_settings: Optional[LLMSettings] = None) -> str:
    base_url = llm_settings.base_url if llm_settings else config.LLM_BASE_URL
    api_key = llm_settings.api_key if llm_settings else config.LLM_API_KEY
    model = llm_settings.model if llm_settings else config.LLM_MODEL

    if not base_url or not api_key:
        raise ValueError("LLM settings not configured")

    prompt = f"""
    Напишите сопроводительное письмо для вакансии.

    Пользователь: {user.name}
    Должность: {user.desired_position}
    Навыки: {user.skills}

    Вакансия:
    Название: {vacancy.title}
    Компания: {vacancy.company}
    Описание: {vacancy.description}

    Сопроводительное письмо должно быть профессиональным и персонализированным.
    """

    messages = [{"role": "user", "content": prompt}]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": messages}
        )
        response.raise_for_status()
        data = response.json()

    return data['choices'][0]['message']['content']