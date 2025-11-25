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
Создай профессиональное резюме, адаптированное под конкретную вакансию.

ИНФОРМАЦИЯ О КАНДИДАТЕ:
- ФИО: {user.name}
- Город: {user.city} 
- Желаемая должность: {user.desired_position}
- Ключевые навыки: {user.skills}
- Опыт работы: {user.base_resume}

ИНФОРМАЦИЯ О ВАКАНСИИ:
- Должность: {vacancy.title}
- Компания: {vacancy.company}
- Город: {getattr(vacancy, 'city', 'Не указан')}
- Описание: {vacancy.description}
- Зарплата: {getattr(vacancy, 'salary', 'Не указана')}

ТРЕБОВАНИЯ К РЕЗЮМЕ:
1. Адаптируй резюме под требования вакансии
2. Выдели наиболее релевантные навыки кандидата
3. Структурируй информацию профессионально
4. Сделай акцент на соответствие требованиям вакансии
5. Используй деловой стиль
6. Укажи контактную информацию (город, возможный способ связи)

Формат: профессиональное резюме с разделами (Контакты, Опыт работы, Навыки, Образование и т.д.).
"""

    messages = [{"role": "user", "content": prompt}]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model, 
                    "messages": messages,
                    "max_tokens": 2000,
                    "temperature": 0.7,
                    "stream": False
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_data = response.json()
                    error_detail = error_data.get('error', {}).get('message', error_detail)
                except:
                    pass
                raise Exception(f"LLM API error: {response.status_code} - {error_detail}")
                
            data = response.json()
            if 'choices' not in data or not data['choices']:
                raise Exception("Пустой ответ от LLM API")
                
            return data['choices'][0]['message']['content'].strip()
            
    except httpx.TimeoutException:
        raise Exception("Таймаут при подключении к LLM API")
    except Exception as e:
        raise Exception(f"Ошибка при генерации резюме: {str(e)}")

async def generate_cover_letter(user: User, vacancy: Vacancy, llm_settings: Optional[LLMSettings] = None) -> str:
    base_url = llm_settings.base_url if llm_settings else config.LLM_BASE_URL
    api_key = llm_settings.api_key if llm_settings else config.LLM_API_KEY
    model = llm_settings.model if llm_settings else config.LLM_MODEL

    if not base_url or not api_key:
        raise ValueError("LLM settings not configured")

    prompt = f"""
Напиши сопроводительное письмо для отклика на вакансию.

ИНФОРМАЦИЯ О КАНДИДАТЕ:
- Имя: {user.name}
- Город: {user.city}
- Желаемая должность: {user.desired_position}
- Навыки: {user.skills}
- Опыт: {user.base_resume}

ИНФОРМАЦИЯ О ВАКАНСИИ:
- Должность: {vacancy.title}
- Компания: {vacancy.company}
- Город: {getattr(vacancy, 'city', 'Не указан')}
- Описание: {vacancy.description}
- Зарплата: {getattr(vacancy, 'salary', 'Не указана')}

ТРЕБОВАНИЯ К ПИСЬМУ:
1. Персонализированное обращение к компании
2. Обоснование интереса к вакансии
3. Подчеркивание релевантного опыта и навыков
4. Увяжи опыт кандидата с требованиями вакансии
5. Профессиональный деловой стиль
6. Призыв к дальнейшему общению
7. Укажи готовность к переезду если город вакансии отличается

Формат: деловое письмо с приветствием, основной частью и подписью.
Длина: 1-2 абзаца, информативно и по делу.
"""

    messages = [{"role": "user", "content": prompt}]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model, 
                    "messages": messages,
                    "max_tokens": 1500,
                    "temperature": 0.7,
                    "stream": False
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_data = response.json()
                    error_detail = error_data.get('error', {}).get('message', error_detail)
                except:
                    pass
                raise Exception(f"LLM API error: {response.status_code} - {error_detail}")
                
            data = response.json()
            if 'choices' not in data or not data['choices']:
                raise Exception("Пустой ответ от LLM API")
                
            return data['choices'][0]['message']['content'].strip()
            
    except httpx.TimeoutException:
        raise Exception("Таймаут при подключении к LLM API")
    except Exception as e:
        raise Exception(f"Ошибка при генерации письма: {str(e)}")