import httpx
from typing import List, Dict, Any
from config import config
from db.models import SearchSettings

# Маппинг городов
CITY_MAPPING = {
    "москва": "1",
    "санкт-петербург": "2", 
    "спб": "2",
    "екатеринбург": "3",
    "новосибирск": "4",
    "казань": "88",
    "нижний новгород": "66",
    "ростов-на-дону": "76",
    "самара": "78",
    "волгоград": "24",
    "краснодар": "53",
    "воронеж": "26",
    "пермь": "72",
    "уфа": "99",
    "челябинск": "104",
    "красноярск": "54",
    "омск": "68",
    "тюмень": "95",
    "ижевск": "37",
    "барнаул": "22",
    "иркутск": "38",
    "хабаровск": "101",
    "владивосток": "25",
    "ярославль": "112"
}

# Маппинг опыта работы для HH API
EXPERIENCE_MAPPING = {
    "no_exp": "noExperience",
    "1-3": "between1And3", 
    "3-6": "between3And6",
    "6+": "moreThan6",
    "any": None
}

# Маппинг типа занятости для HH API
EMPLOYMENT_MAPPING = {
    "full": "full",
    "part": "part", 
    "remote": "remote",
    "any": None
}

async def search_vacancies(settings: SearchSettings) -> List[Dict[str, Any]]:
    """Поиск вакансий на HH.ru с правильными параметрами"""
    
    # Преобразуем город в ID HH.ru
    city_lower = settings.city.lower()
    city_id = CITY_MAPPING.get(city_lower, "113")  # 113 = Россия
    
    # Базовые параметры
    params = {
        'text': settings.position,
        'area': city_id,
        'per_page': 10,  # Уменьшим для теста
        'page': 0
    }

    # Добавляем зарплату если указана
    if settings.min_salary and settings.min_salary > 0:
        params['salary'] = settings.min_salary
        params['only_with_salary'] = True

    # Добавляем свежесть вакансий (в днях)
    if hasattr(settings, 'freshness') and settings.freshness:
        params['period'] = settings.freshness

    # Добавляем опыт работы
    if hasattr(settings, 'experience') and settings.experience != 'any':
        hh_experience = EXPERIENCE_MAPPING.get(settings.experience)
        if hh_experience:
            params['experience'] = hh_experience

    # Добавляем тип занятости
    if hasattr(settings, 'employment_type') and settings.employment_type != 'any':
        hh_employment = EMPLOYMENT_MAPPING.get(settings.employment_type)
        if hh_employment:
            params['employment'] = hh_employment

    print(f"🔍 Параметры запроса к HH.ru: {params}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config.HH_API_BASE_URL}/vacancies", 
                params=params,
                timeout=30.0
            )
            
            if response.status_code != 200:
                print(f"❌ Ошибка HH API: {response.status_code} - {response.text}")
                return []
                
            data = response.json()
            print(f"✅ Найдено вакансий: {data.get('found', 0)}")

            vacancies = []
            for item in data.get('items', []):
                try:
                    vacancy = {
                        'hh_id': str(item['id']),
                        'title': item['name'],
                        'company': item['employer']['name'] if item.get('employer') else 'Не указано',
                        'city': item['area']['name'] if item.get('area') else 'Не указан',
                        'salary': format_salary(item.get('salary')),
                        'url': item.get('alternate_url', ''),
                        'description': clean_description(
                            (item.get('snippet', {}).get('requirement', '') + ' ' + 
                             item.get('snippet', {}).get('responsibility', ''))
                        ),
                    }
                    vacancies.append(vacancy)
                except Exception as e:
                    print(f"❌ Ошибка обработки вакансии: {e}")
                    continue

            print(f"✅ Успешно обработано вакансий: {len(vacancies)}")
            return vacancies

    except httpx.RequestError as e:
        print(f"❌ Ошибка сети: {e}")
        return []
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return []

def format_salary(salary: Dict[str, Any]) -> str:
    if not salary:
        return "Не указана"
    
    try:
        from_ = salary.get('from')
        to = salary.get('to')
        currency = salary.get('currency', 'RUB')
        
        # Форматируем валюту
        currency_symbol = {
            'RUR': '₽',
            'RUB': '₽', 
            'USD': '$',
            'EUR': '€',
            'KZT': '₸'
        }.get(currency, currency)
        
        if from_ and to:
            return f"{from_:,} - {to:,} {currency_symbol}".replace(',', ' ')
        elif from_:
            return f"от {from_:,} {currency_symbol}".replace(',', ' ')
        elif to:
            return f"до {to:,} {currency_symbol}".replace(',', ' ')
        return "Не указана"
    except Exception:
        return "Не указана"

def clean_description(description: str) -> str:
    """Очистка описания от HTML тегов и лишних пробелов"""
    import re
    try:
        if not description:
            return "Описание отсутствует"
        # Удаляем HTML теги
        description = re.sub(r'<[^>]+>', '', description)
        # Заменяем множественные пробелы на один
        description = re.sub(r'\s+', ' ', description)
        # Обрезаем до разумной длины
        return description.strip()[:500]
    except Exception:
        return "Описание отсутствует"