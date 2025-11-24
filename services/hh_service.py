import httpx
from typing import List, Dict, Any
from config import config
from db.models import SearchSettings

async def search_vacancies(settings: SearchSettings) -> List[Dict[str, Any]]:
    params = {
        'text': settings.position,
        'area': settings.city,  # Нужно маппинг городов на ID hh.ru
        'salary': settings.min_salary,
        'period': settings.freshness,
        'employment': settings.employment_type,
        'experience': settings.experience,
        # Другие параметры
    }

    # Удалить None значения
    params = {k: v for k, v in params.items() if v is not None}

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{config.HH_API_BASE_URL}/vacancies", params=params)
        response.raise_for_status()
        data = response.json()

    vacancies = []
    for item in data.get('items', []):
        vacancy = {
            'hh_id': item['id'],
            'title': item['name'],
            'company': item['employer']['name'] if item.get('employer') else '',
            'city': item['area']['name'] if item.get('area') else '',
            'salary': format_salary(item.get('salary')),
            'url': item['alternate_url'],
            'description': item.get('snippet', {}).get('requirement', '') + ' ' + item.get('snippet', {}).get('responsibility', ''),
        }
        vacancies.append(vacancy)

    return vacancies

def format_salary(salary: Dict[str, Any]) -> str:
    if not salary:
        return "Не указана"
    from_ = salary.get('from')
    to = salary.get('to')
    currency = salary.get('currency', 'RUB')
    if from_ and to:
        return f"{from_} - {to} {currency}"
    elif from_:
        return f"от {from_} {currency}"
    elif to:
        return f"до {to} {currency}"
    return "Не указана"