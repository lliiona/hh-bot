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
Создай подробное профессиональное резюме, максимально адаптированное под конкретную вакансию.

ИНФОРМАЦИЯ О КАНДИДАТЕ:
👤 ФИО: {user.name}
📍 Город: {user.city}
🎯 Желаемая должность: {user.desired_position}
🛠️ Ключевые навыки: {user.skills}
📋 Опыт работы: {user.base_resume}

ИНФОРМАЦИЯ О ВАКАНСИИ:
💼 Должность: {vacancy.title}
🏢 Компания: {vacancy.company}
📍 Город: {vacancy.city}
💰 Зарплата: {vacancy.salary}
📝 Описание вакансии: {vacancy.description}

ТРЕБОВАНИЯ К РЕЗЮМЕ:
1. Тщательно проанализируй описание вакансии и выдели ключевые требования
2. Адаптируй резюме под конкретные требования вакансии
3. Выдели наиболее релевантные навыки кандидата для этой должности
4. Подчеркни опыт, который соответствует требованиям вакансии
5. Структурируй информацию в профессиональном формате
6. Используй ключевые слова из описания вакансии
7. Сделай акцент на достижениях и результатах

СТРУКТУРА РЕЗЮМЕ:
1. Контактная информация и личные данные
2. Цель/Профессиональное резюме (адаптированная под вакансию)
3. Ключевые навыки (сгруппированные по релевантности)
4. Опыт работы (с акцентом на соответствующий опыт)
5. Образование (если уместно)
6. Дополнительная информация (сертификаты, проекты и т.д.)

Важно: сделай резюме максимально релевантным для конкретной вакансии в компании {vacancy.company}.
"""

    messages = [{"role": "user", "content": prompt}]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model, 
                    "messages": messages,
                    "max_tokens": 3000,
                    "temperature": 0.7
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise Exception(f"LLM API error: {response.status_code} - {response.text}")
                
            data = response.json()
            return data['choices'][0]['message']['content']
            
    except Exception as e:
        raise Exception(f"Ошибка при генерации резюме: {str(e)}")

async def generate_cover_letter(user: User, vacancy: Vacancy, llm_settings: Optional[LLMSettings] = None) -> str:
    base_url = llm_settings.base_url if llm_settings else config.LLM_BASE_URL
    api_key = llm_settings.api_key if llm_settings else config.LLM_API_KEY
    model = llm_settings.model if llm_settings else config.LLM_MODEL

    if not base_url or not api_key:
        raise ValueError("LLM settings not configured")

    prompt = f"""
Напиши подробное персонализированное сопроводительное письмо для отклика на вакансию.

ИНФОРМАЦИЯ О КАНДИДАТЕ:
👤 Имя: {user.name}
📍 Город: {user.city}
🎯 Желаемая должность: {user.desired_position}
🛠️ Навыки: {user.skills}
📋 Опыт: {user.base_resume}

ИНФОРМАЦИЯ О ВАКАНСИИ:
💼 Должность: {vacancy.title}
🏢 Компания: {vacancy.company}
📍 Город: {vacancy.city}
💰 Зарплата: {vacancy.salary}
📝 Описание: {vacancy.description}

ТРЕБОВАНИЯ К ПИСЬМУ:
1. Тщательно проанализируй описание вакансии и компанию
2. Персонализируй обращение к компании {vacancy.company}
3. Обоснуй интерес именно к этой вакансии и компании
4. Подчеркни релевантный опыт и навыки для требований вакансии
5. Приведи конкретные примеры из опыта кандидата
6. Объясни почему кандидат подходит для этой должности
7. Продемонстрируй энтузиазм по поводу работы в компании
8. Включи призыв к действию (предложи собеседование/встречу)

СТРУКТУРА ПИСЬМА:
1. Персонализированное приветствие
2. Введение с указанием вакансии и выражения интереса
3. Основная часть с обоснованием соответствия требованиям
4. Конкретные примеры релевантного опыта и навыков
5. Объяснение почему кандидат хочет работать в этой компании
6. Заключение с призывом к действию
7. Профессиональная подпись

Тон: профессиональный, уверенный, но не самонадеянный.
"""

    messages = [{"role": "user", "content": prompt}]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model, 
                    "messages": messages,
                    "max_tokens": 2500,
                    "temperature": 0.7
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise Exception(f"LLM API error: {response.status_code} - {response.text}")
                
            data = response.json()
            return data['choices'][0]['message']['content']
            
    except Exception as e:
        raise Exception(f"Ошибка при генерации письма: {str(e)}")