from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import User, SearchSettings, UserVacancy, Vacancy, LLMSettings
import json

router = Router()

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_city = State()
    waiting_for_position = State()
    waiting_for_skills = State()
    waiting_for_resume = State()

class SearchSettingsStates(StatesGroup):
    waiting_for_position = State()
    waiting_for_city = State()
    waiting_for_min_salary = State()
    waiting_for_metro = State()
    waiting_for_freshness = State()
    waiting_for_employment = State()
    waiting_for_experience = State()
    waiting_for_company = State()

class LLMConfigStates(StatesGroup):
    waiting_for_base_url = State()
    waiting_for_api_key = State()
    waiting_for_model = State()

# ========== КОМАНДА ОЧИСТКИ ТЕСТОВЫХ ДАННЫХ ==========

@router.message(F.text == "/clear_test_data")
async def cmd_clear_test_data(message: Message, session: AsyncSession):
    """Очистка тестовых данных из базы"""
    try:
        # Удаляем тестовые вакансии
        result = await session.execute(
            select(Vacancy).where(Vacancy.hh_id.like("test_%"))
        )
        test_vacancies = result.scalars().all()
        
        deleted_count = 0
        for vacancy in test_vacancies:
            # Сначала удаляем связи в UserVacancy
            await session.execute(
                UserVacancy.__table__.delete().where(UserVacancy.vacancy_id == vacancy.id)
            )
            # Затем удаляем саму вакансию
            await session.delete(vacancy)
            deleted_count += 1
        
        await session.commit()
        await message.reply(f"✅ Удалено {deleted_count} тестовых вакансий")
        
    except Exception as e:
        await session.rollback()
        await message.reply(f"❌ Ошибка при очистке: {e}")

# ========== РЕГИСТРАЦИЯ ==========

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    telegram_id = message.from_user.id
    user = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user.scalar_one_or_none()

    if user:
        await message.reply("Вы уже зарегистрированы! Используйте /search_settings для настройки поиска.")
        return

    await message.reply("Добро пожаловать! Давайте создадим ваш профиль.\nВведите ваше ФИО:")
    await state.set_state(RegistrationStates.waiting_for_name)

@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(name=message.text)
    await message.reply("Введите ваш город:")
    await state.set_state(RegistrationStates.waiting_for_city)

@router.message(RegistrationStates.waiting_for_city)
async def process_city(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(city=message.text)
    await message.reply("Введите желаемую должность:")
    await state.set_state(RegistrationStates.waiting_for_position)

@router.message(RegistrationStates.waiting_for_position)
async def process_position(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(desired_position=message.text)
    await message.reply("Введите ваши навыки (через запятую):")
    await state.set_state(RegistrationStates.waiting_for_skills)

@router.message(RegistrationStates.waiting_for_skills)
async def process_skills(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(skills=message.text)
    await message.reply("Отправьте ваше базовое резюме (текстом):")
    await state.set_state(RegistrationStates.waiting_for_resume)

@router.message(RegistrationStates.waiting_for_resume)
async def process_resume(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    user = User(
        telegram_id=message.from_user.id,
        name=data['name'],
        city=data['city'],
        desired_position=data['desired_position'],
        skills=data['skills'],
        base_resume=message.text
    )
    session.add(user)
    await session.commit()
    await message.reply("✅ Регистрация завершена! Используйте /search_settings для настройки поиска вакансий.")
    await state.clear()

# ========== НАСТРОЙКИ ПОИСКА ==========

@router.message(F.text == "/search_settings")
async def cmd_search_settings(message: Message, state: FSMContext, session: AsyncSession):
    telegram_id = message.from_user.id
    user = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user.scalar_one_or_none()

    if not user:
        await message.reply("Сначала зарегистрируйтесь с помощью /start")
        return

    await message.reply("Настройка поиска вакансий.\nВведите желаемую должность:")
    await state.set_state(SearchSettingsStates.waiting_for_position)

@router.message(SearchSettingsStates.waiting_for_position)
async def process_search_position(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(position=message.text)
    await message.reply("Введите город для поиска:")
    await state.set_state(SearchSettingsStates.waiting_for_city)

@router.message(SearchSettingsStates.waiting_for_city)
async def process_search_city(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(city=message.text)
    await message.reply("Введите минимальную зарплату (только цифры):")
    await state.set_state(SearchSettingsStates.waiting_for_min_salary)

@router.message(SearchSettingsStates.waiting_for_min_salary)
async def process_search_salary(message: Message, state: FSMContext, session: AsyncSession):
    try:
        min_salary = int(message.text)
        await state.update_data(min_salary=min_salary)
    except ValueError:
        await message.reply("Пожалуйста, введите только цифры. Установлена зарплата 0.")
        await state.update_data(min_salary=0)
    
    # Клавиатура для выбора удаленности
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚇 Любое метро", callback_data="metro_any")],
        [InlineKeyboardButton(text="🚶‍♂️ Пешая доступность", callback_data="metro_walking")],
        [InlineKeyboardButton(text="🚍 До 15 минут", callback_data="metro_15min")],
        [InlineKeyboardButton(text="🚊 До 30 минут", callback_data="metro_30min")],
        [InlineKeyboardButton(text="🏠 Удаленная работа", callback_data="metro_remote")]
    ])
    await message.reply("Выберите удаленность от метро:", reply_markup=keyboard)
    await state.set_state(SearchSettingsStates.waiting_for_metro)

@router.callback_query(SearchSettingsStates.waiting_for_metro, F.data.startswith("metro_"))
async def process_search_metro(callback: CallbackQuery, state: FSMContext):
    metro_mapping = {
        "metro_any": "Любое",
        "metro_walking": "Пешая доступность", 
        "metro_15min": "До 15 минут",
        "metro_30min": "До 30 минут",
        "metro_remote": "Удаленная работа"
    }
    
    metro_value = metro_mapping.get(callback.data, "Любое")
    await state.update_data(metro=metro_value)
    
    # Клавиатура для свежести вакансий
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 1 день", callback_data="freshness_1")],
        [InlineKeyboardButton(text="🆒 3 дня", callback_data="freshness_3")],
        [InlineKeyboardButton(text="📅 7 дней", callback_data="freshness_7")],
        [InlineKeyboardButton(text="📆 14 дней", callback_data="freshness_14")],
        [InlineKeyboardButton(text="🕐 Любая", callback_data="freshness_any")]
    ])
    await callback.message.edit_text("Выберите свежесть вакансий:")
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await state.set_state(SearchSettingsStates.waiting_for_freshness)
    await callback.answer()

@router.callback_query(SearchSettingsStates.waiting_for_freshness, F.data.startswith("freshness_"))
async def process_search_freshness(callback: CallbackQuery, state: FSMContext):
    freshness_mapping = {
        "freshness_1": 1,
        "freshness_3": 3,
        "freshness_7": 7,
        "freshness_14": 14,
        "freshness_any": 30
    }
    
    freshness = freshness_mapping.get(callback.data, 30)
    await state.update_data(freshness=freshness)
    
    # Клавиатура для типа занятости
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Полная занятость", callback_data="employment_full")],
        [InlineKeyboardButton(text="⏰ Частичная занятость", callback_data="employment_part")],
        [InlineKeyboardButton(text="🏠 Удаленная работа", callback_data="employment_remote")],
        [InlineKeyboardButton(text="🔀 Любой тип", callback_data="employment_any")]
    ])
    await callback.message.edit_text("Выберите тип занятости:")
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await state.set_state(SearchSettingsStates.waiting_for_employment)
    await callback.answer()

@router.callback_query(SearchSettingsStates.waiting_for_employment, F.data.startswith("employment_"))
async def process_search_employment(callback: CallbackQuery, state: FSMContext):
    employment_mapping = {
        "employment_full": "full",
        "employment_part": "part", 
        "employment_remote": "remote",
        "employment_any": "any"
    }
    
    employment = employment_mapping.get(callback.data, "any")
    await state.update_data(employment=employment)
    
    # Клавиатура для опыта работы
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎓 Нет опыта", callback_data="experience_none")],
        [InlineKeyboardButton(text="👶 1-3 года", callback_data="experience_1-3")],
        [InlineKeyboardButton(text="👨‍💼 3-6 лет", callback_data="experience_3-6")],
        [InlineKeyboardButton(text="👴 Более 6 лет", callback_data="experience_6plus")],
        [InlineKeyboardButton(text="🔀 Любой опыт", callback_data="experience_any")]
    ])
    await callback.message.edit_text("Выберите опыт работы:")
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await state.set_state(SearchSettingsStates.waiting_for_experience)
    await callback.answer()

@router.callback_query(SearchSettingsStates.waiting_for_experience, F.data.startswith("experience_"))
async def process_search_experience(callback: CallbackQuery, state: FSMContext):
    experience_mapping = {
        "experience_none": "no_exp",
        "experience_1-3": "1-3", 
        "experience_3-6": "3-6",
        "experience_6plus": "6+", 
        "experience_any": "any"
    }
    
    experience = experience_mapping.get(callback.data, "any")
    await state.update_data(experience=experience)
    
    # Клавиатура для типа компании
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏢 Только прямые работодатели", callback_data="company_direct")],
        [InlineKeyboardButton(text="🔍 Размер компании", callback_data="company_size")],
        [InlineKeyboardButton(text="⭐ Только ТОП-компании", callback_data="company_top")],
        [InlineKeyboardButton(text="🔀 Любые компании", callback_data="company_any")]
    ])
    await callback.message.edit_text("Выберите предпочтения по компаниям:")
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await state.set_state(SearchSettingsStates.waiting_for_company)
    await callback.answer()

@router.callback_query(SearchSettingsStates.waiting_for_company, F.data.startswith("company_"))
async def process_search_company(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    company_mapping = {
        "company_direct": "direct",
        "company_size": "size", 
        "company_top": "top",
        "company_any": "any"
    }
    
    company_type = company_mapping.get(callback.data, "any")
    await state.update_data(company_type=company_type)
    
    # Сохраняем настройки поиска с ПРАВИЛЬНЫМИ названиями полей
    data = await state.get_data()
    telegram_id = callback.from_user.id
    
    # Получаем пользователя
    user = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user.scalar_one_or_none()
    
    if not user:
        await callback.message.edit_text("❌ Ошибка: пользователь не найден")
        await state.clear()
        await callback.answer()
        return

    # Преобразуем данные для сохранения в JSON поля согласно модели
    metro_stations = []  # Пока пустой список станций
    
    # Создаем company_filters в зависимости от выбора
    company_filters = {}
    if company_type == "size":
        company_filters = {"size": ["small", "medium", "large"]}
    elif company_type == "direct":
        company_filters = {"type": "direct"}
    elif company_type == "top":
        company_filters = {"rating": "top"}
    else:
        company_filters = {"type": "any"}
    
    search_settings = SearchSettings(
        user_id=user.id,  # Используем ID пользователя из БД
        position=data['position'],
        city=data['city'],
        min_salary=data.get('min_salary', 0),
        metro_stations=metro_stations,
        freshness=data.get('freshness', 30),
        employment_type=data.get('employment', 'any'),
        experience=data.get('experience', 'any'),
        company_filters=company_filters
    )
    
    session.add(search_settings)
    await session.commit()
    
    # Показываем сводку настроек
    summary = f"""
✅ Настройки поиска сохранены!

📋 Сводка:
• Должность: {data['position']}
• Город: {data['city']}
• Зарплата: от {data.get('min_salary', 0)} руб.
• Удаленность: {data.get('metro', 'Любое')}
• Свежесть: {data.get('freshness', 30)} дней
• Занятость: {data.get('employment', 'любая')}
• Опыт: {data.get('experience', 'любой')}
• Компании: {data.get('company_type', 'любые')}

Используйте /vacancies для поиска вакансий!
    """
    
    await callback.message.edit_text(summary)
    await state.clear()
    await callback.answer()

# ========== LLM НАСТРОЙКИ ==========

@router.message(F.text == "/set_llm")
async def cmd_set_llm(message: Message, state: FSMContext, session: AsyncSession):
    telegram_id = message.from_user.id
    user = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user.scalar_one_or_none()

    if not user:
        await message.reply("Сначала зарегистрируйтесь с помощью /start")
        return

    await message.reply("Настройка LLM.\nВведите Base URL (например, https://api.openai.com/v1):")
    await state.set_state(LLMConfigStates.waiting_for_base_url)

@router.message(LLMConfigStates.waiting_for_base_url)
async def process_base_url(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(base_url=message.text)
    await message.reply("Введите API Key:")
    await state.set_state(LLMConfigStates.waiting_for_api_key)

@router.message(LLMConfigStates.waiting_for_api_key)
async def process_api_key(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(api_key=message.text)
    await message.reply("Введите название модели (например, gpt-3.5-turbo):")
    await state.set_state(LLMConfigStates.waiting_for_model)

@router.message(LLMConfigStates.waiting_for_model)
async def process_model(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    telegram_id = message.from_user.id
    
    # Получаем пользователя
    user = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user.scalar_one_or_none()
    
    if not user:
        await message.reply("❌ Ошибка: пользователь не найден")
        await state.clear()
        return

    # Сохраняем настройки LLM
    llm_settings = LLMSettings(
        user_id=user.id,
        base_url=data['base_url'],
        api_key=data['api_key'],
        model=message.text
    )
    session.add(llm_settings)
    await session.commit()
    
    await message.reply(f"✅ Настройки LLM сохранены!\nURL: {data['base_url']}\nМодель: {message.text}")
    await state.clear()

# ========== ВАКАНСИИ ==========

@router.message(F.text == "/vacancies")
async def cmd_vacancies(message: Message, session: AsyncSession):
    telegram_id = message.from_user.id
    
    # Получаем пользователя
    user = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user.scalar_one_or_none()
    
    if not user:
        await message.reply("Сначала зарегистрируйтесь с помощью /start")
        return
    
    # Получаем только НЕ тестовые вакансии пользователя
    user_vacancies = await session.execute(
        select(UserVacancy)
        .join(Vacancy, UserVacancy.vacancy_id == Vacancy.id)
        .where(
            UserVacancy.user_id == user.id,
            ~Vacancy.hh_id.like("test_%")  # Исключаем тестовые вакансии
        )
        .order_by(UserVacancy.sent_at.desc())
        .limit(10)
    )
    user_vacancies = user_vacancies.scalars().all()

    if not user_vacancies:
        await message.reply("🤷‍♂️ Пока нет подходящих вакансий по вашим настройкам.\n\nПопробуйте:\n• Изменить настройки поиска /search_settings\n• Расширить критерии поиска\n• Проверить позже - новые вакансии появляются каждый день!")
        return

    vacancy_count = 0
    for uv in user_vacancies:
        vacancy = await session.get(Vacancy, uv.vacancy_id)
        if vacancy and not vacancy.hh_id.startswith("test_"):  # Дополнительная проверка
            await show_vacancy_with_buttons(message, vacancy)
            vacancy_count += 1
    
    if vacancy_count == 0:
        await message.reply("🤷‍♂️ Пока нет подходящих вакансий по вашим настройкам.")

async def show_vacancy_with_buttons(message: Message, vacancy: Vacancy):
    """Показывает вакансию с кнопками"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Сгенерировать резюме", callback_data=f"generate_resume_{vacancy.id}")],
        [InlineKeyboardButton(text="📝 Сгенерировать cover letter", callback_data=f"generate_cover_{vacancy.id}")],
        [InlineKeyboardButton(text="👎 Неинтересно", callback_data=f"dismiss_{vacancy.id}")]
    ])
    
    vacancy_text = f"""
💼 {vacancy.title}
🏢 {vacancy.company}
📍 {vacancy.city}
💰 {vacancy.salary}
🔗 {vacancy.url}
    """
    
    await message.answer(vacancy_text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("generate_resume_"))
async def generate_resume(callback: CallbackQuery, session: AsyncSession):
    vacancy_id = int(callback.data.split("_")[2])
    telegram_id = callback.from_user.id

    user = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user.scalar_one_or_none()
    vacancy = await session.get(Vacancy, vacancy_id)

    if not user or not vacancy:
        await callback.answer("Ошибка")
        return

    # Генерация резюме
    try:
        resume = f"""
📄 РЕЗЮМЕ ДЛЯ: {vacancy.title}

👤 Кандидат: {user.name}
📍 Город: {user.city}
🎯 Целевая должность: {user.desired_position}

🛠️ НАВЫКИ:
{user.skills}

📋 ОПЫТ:
{user.base_resume}

💪 Готов рассмотреть предложение от компании {vacancy.company}!
        """
        await callback.message.reply(resume)
    except Exception as e:
        await callback.message.reply(f"❌ Ошибка генерации: {e}")

    await callback.answer()

@router.callback_query(F.data.startswith("generate_cover_"))
async def generate_cover(callback: CallbackQuery, session: AsyncSession):
    vacancy_id = int(callback.data.split("_")[2])
    telegram_id = callback.from_user.id

    user = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user.scalar_one_or_none()
    vacancy = await session.get(Vacancy, vacancy_id)

    if not user or not vacancy:
        await callback.answer("Ошибка")
        return

    # Генерация cover letter
    try:
        cover = f"""
📝 COVER LETTER ДЛЯ: {vacancy.title} в {vacancy.company}

Уважаемые коллеги!

Меня зовут {user.name}, и я заинтересован в вакансии {vacancy.title} в компании {vacancy.company}.

Мой опыт и навыки:
{user.skills}

{user.base_resume}

Буду рад обсудить возможность сотрудничества!

С уважением,
{user.name}
        """
        await callback.message.reply(cover)
    except Exception as e:
        await callback.message.reply(f"❌ Ошибка генерации: {e}")

    await callback.answer()

@router.callback_query(F.data.startswith("dismiss_"))
async def dismiss_vacancy(callback: CallbackQuery, session: AsyncSession):
    vacancy_id = int(callback.data.split("_")[1])
    await callback.answer("✅ Вакансия отмечена как неинтересная")

def register_handlers(dp):
    dp.include_router(router)