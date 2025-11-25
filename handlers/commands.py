from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import User, SearchSettings, UserVacancy, Vacancy, LLMSettings,LLMSettings 
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
    
class EditProfileStates(StatesGroup):
    waiting_for_field = State()
    waiting_for_new_value = State()

class DeleteProfileStates(StatesGroup):
    waiting_for_confirmation = State()

# ========== РЕГИСТРАЦИЯ ==========

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    telegram_id = message.from_user.id
    user = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user.scalar_one_or_none()

    if user:
        help_text = """
✅ Вы уже зарегистрированы!

📋 **Что можно сделать:**
/profile - Управление профилем
/search_settings - Настроить поиск вакансий
/vacancies - Посмотреть подобранные вакансии
/help - Помощь по командам

💡 Используйте /search_settings для настройки параметров поиска
        """
        await message.reply(help_text)
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
    
    help_text = """
✅ **Регистрация завершена!**

📋 **Что дальше:**
1. /search_settings - Настройте параметры поиска вакансий
2. /vacancies - Смотрите подобранные вакансии
3. Под каждой вакансией генерируйте резюме и cover letter

💡 Начните с /search_settings для настройки поиска!
    """
    await message.reply(help_text)
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
    
    # Сохраняем настройки поиска
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

    # Преобразуем данные для сохранения
    metro_stations = []
    
    # Создаем company_filters
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
        user_id=user.id,
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
    
    # Запускаем поиск вакансий
    search_message = ""
    try:
        from services.hh_service import search_vacancies
        
        await callback.message.edit_text("✅ Настройки сохранены! 🔍 Ищу вакансии на HH.ru...")
        
        # Ищем вакансии
        vacancies_data = await search_vacancies(search_settings)
        
        if vacancies_data:
            saved_count = 0
            for vacancy_data in vacancies_data:
                # Проверяем, нет ли уже такой вакансии
                existing_vacancy = await session.execute(
                    select(Vacancy).where(Vacancy.hh_id == vacancy_data['hh_id'])
                )
                existing_vacancy = existing_vacancy.scalar_one_or_none()
                
                if not existing_vacancy:
                    # Создаем новую вакансию
                    vacancy = Vacancy(
                        hh_id=vacancy_data['hh_id'],
                        title=vacancy_data['title'],
                        company=vacancy_data['company'],
                        city=vacancy_data['city'],
                        salary=vacancy_data['salary'],
                        url=vacancy_data['url'],
                        description=vacancy_data['description']
                    )
                    session.add(vacancy)
                    await session.flush()
                    
                    # Связываем с пользователем
                    user_vacancy = UserVacancy(
                        user_id=user.id,
                        vacancy_id=vacancy.id
                    )
                    session.add(user_vacancy)
                    saved_count += 1
            
            await session.commit()
            search_message = f"✅ Найдено {len(vacancies_data)} вакансий, сохранено {saved_count} новых!"
        else:
            search_message = "❌ По вашему запросу вакансий не найдено. Попробуйте изменить критерии."
            
    except Exception as e:
        search_message = f"❌ Ошибка при поиске вакансий: {str(e)}"
    
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

{search_message}

Используйте /vacancies для просмотра вакансий!
    """
    
    await callback.message.edit_text(summary)
    await state.clear()
    await callback.answer()

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
    
    # Получаем вакансии пользователя
    user_vacancies = await session.execute(
        select(UserVacancy)
        .where(UserVacancy.user_id == user.id)
        .order_by(UserVacancy.sent_at.desc())
        .limit(10)
    )
    user_vacancies = user_vacancies.scalars().all()

    if not user_vacancies:
        await message.reply("🤷‍♂️ Пока нет подходящих вакансий по вашим настройкам.\n\nПопробуйте:\n• Изменить настройки поиска /search_settings\n• Расширить критерии поиска\n• Проверить позже - новые вакансии появляются каждый день!")
        return

    for uv in user_vacancies:
        vacancy = await session.get(Vacancy, uv.vacancy_id)
        if vacancy:
            await show_vacancy_with_buttons(message, vacancy)

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
async def generate_resume_handler(callback: CallbackQuery, session: AsyncSession):
    """Генерация адаптированного резюме"""
    vacancy_id = int(callback.data.split("_")[2])
    telegram_id = callback.from_user.id

    user = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user.scalar_one_or_none()
    vacancy = await session.get(Vacancy, vacancy_id)

    if not user or not vacancy:
        await callback.answer("Ошибка: данные не найдены")
        return

    # Получаем настройки LLM
    llm_settings = await session.execute(
    select(LLMSettings).where(LLMSettings.user_id == user.id)
)
    llm_settings = llm_settings.scalar_one_or_none()

    await callback.message.edit_text("🤖 Генерирую адаптированное резюме...")

    try:
        from services.llm_service import generate_resume
        resume_text = await generate_resume(user, vacancy, llm_settings)
        await callback.message.reply(f"📄 **АДАПТИРОВАННОЕ РЕЗЮМЕ ДЛЯ {vacancy.title}**\n\n{resume_text}")
    except ValueError as e:
        await callback.message.reply(
            "❌ LLM не настроен. Используйте /set_llm для настройки генерации документов.\n\n"
            "Для работы функции генерации адаптированных документов необходимо настроить LLM API."
        )
    except Exception as e:
        await callback.message.reply(f"❌ Ошибка при генерации резюме: {str(e)}")

    await callback.answer()

@router.callback_query(F.data.startswith("generate_cover_"))
async def generate_cover_handler(callback: CallbackQuery, session: AsyncSession):
    """Генерация сопроводительного письма"""
    vacancy_id = int(callback.data.split("_")[2])
    telegram_id = callback.from_user.id

    user = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user.scalar_one_or_none()
    vacancy = await session.get(Vacancy, vacancy_id)

    if not user or not vacancy:
        await callback.answer("Ошибка: данные не найдены")
        return

    # Получаем настройки LLM
    llm_settings = await session.execute(
        select(LLMSettings).where(LLMSettings.user_id == user.id)
    )
    llm_settings = llm_settings.scalar_one_or_none()

    await callback.message.edit_text("🤖 Генерирую сопроводительное письмо...")

    try:
        from services.llm_service import generate_cover_letter
        cover_text = await generate_cover_letter(user, vacancy, llm_settings)
        await callback.message.reply(f"📝 **СОПРОВОДИТЕЛЬНОЕ ПИСЬМО ДЛЯ {vacancy.title}**\n\n{cover_text}")
    except ValueError as e:
        await callback.message.reply(
            "❌ LLM не настроен. Используйте /set_llm для настройки генерации документов.\n\n"
            "Для работы функции генерации адаптированных документов необходимо настроить LLM API."
        )
    except Exception as e:
        await callback.message.reply(f"❌ Ошибка при генерации письма: {str(e)}")

    await callback.answer()

@router.callback_query(F.data.startswith("dismiss_"))
async def dismiss_vacancy(callback: CallbackQuery, session: AsyncSession):
    vacancy_id = int(callback.data.split("_")[1])
    await callback.answer("✅ Вакансия отмечена как неинтересная")

# ========== УПРАВЛЕНИЕ ПРОФИЛЕМ ==========

@router.message(F.text == "/profile")
async def cmd_profile(message: Message, session: AsyncSession):
    """Показать информацию о профиле и меню управления"""
    telegram_id = message.from_user.id
    
    user = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user.scalar_one_or_none()
    
    if not user:
        await message.reply("❌ Профиль не найден. Используйте /start для регистрации.")
        return
    
    # Клавиатура управления профилем
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать профиль", callback_data="edit_profile")],
        [InlineKeyboardButton(text="🗑️ Удалить профиль", callback_data="delete_profile")],
        [InlineKeyboardButton(text="📊 Информация о профиле", callback_data="profile_info")]
    ])
    
    profile_text = f"""
👤 **Ваш профиль**

📝 Имя: {user.name}
🏙️ Город: {user.city}
💼 Должность: {user.desired_position}
🛠️ Навыки: {user.skills}
📄 Резюме: {user.base_resume[:100]}... 
    """
    
    await message.reply(profile_text, reply_markup=keyboard)

@router.callback_query(F.data == "profile_info")
async def show_profile_info(callback: CallbackQuery, session: AsyncSession):
    """Показать подробную информацию о профиле"""
    telegram_id = callback.from_user.id
    
    user = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user.scalar_one_or_none()
    
    if not user:
        await callback.answer("❌ Профиль не найден")
        return
    
    # Получаем количество сохраненных вакансий
    vacancies_count = await session.execute(
        select(UserVacancy).where(UserVacancy.user_id == user.id)
    )
    vacancies_count = len(vacancies_count.scalars().all())
    
    # Получаем настройки поиска
    search_settings = await session.execute(
        select(SearchSettings).where(SearchSettings.user_id == user.id)
    )
    search_settings = search_settings.scalar_one_or_none()
    
    # Получаем настройки LLM
    llm_settings = await session.execute(
        select(LLMSettings).where(LLMSettings.user_id == user.id)
    )
    llm_settings = llm_settings.scalar_one_or_none()
    
    profile_info = f"""
📊 **Детальная информация о профиле**

👤 **Основные данные:**
• ID: {user.id}
• Telegram ID: {user.telegram_id}
• Имя: {user.name}
• Город: {user.city}
• Желаемая должность: {user.desired_position}
• Навыки: {user.skills}
• Дата регистрации: {user.created_at.strftime('%d.%m.%Y %H:%M')}

📈 **Статистика:**
• Сохранено вакансий: {vacancies_count}
• Настроек поиска: {'Да' if search_settings else 'Нет'}
• Настроек LLM: {'Да' if llm_settings else 'Нет'}

💡 **Для изменения данных используйте 'Редактировать профиль'**
    """
    
    await callback.message.edit_text(profile_info)
    await callback.answer()

@router.callback_query(F.data == "edit_profile")
async def start_edit_profile(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование профиля"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Имя", callback_data="edit_name")],
        [InlineKeyboardButton(text="🏙️ Город", callback_data="edit_city")],
        [InlineKeyboardButton(text="💼 Должность", callback_data="edit_position")],
        [InlineKeyboardButton(text="🛠️ Навыки", callback_data="edit_skills")],
        [InlineKeyboardButton(text="📄 Резюме", callback_data="edit_resume")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_edit")]
    ])
    
    await callback.message.edit_text("✏️ **Редактирование профиля**\n\nВыберите поле для редактирования:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("edit_"))
async def select_field_to_edit(callback: CallbackQuery, state: FSMContext):
    """Выбор поля для редактирования"""
    field_map = {
        "edit_name": "name",
        "edit_city": "city", 
        "edit_position": "desired_position",
        "edit_skills": "skills",
        "edit_resume": "base_resume"
    }
    
    field = field_map.get(callback.data)
    if not field:
        await callback.answer("❌ Неизвестное поле")
        return
    
    field_names = {
        "name": "имя",
        "city": "город",
        "desired_position": "должность", 
        "skills": "навыки",
        "base_resume": "резюме"
    }
    
    await state.update_data(edit_field=field)
    await callback.message.edit_text(f"✏️ Введите новое значение для **{field_names[field]}**:")
    await state.set_state(EditProfileStates.waiting_for_new_value)
    await callback.answer()

@router.message(EditProfileStates.waiting_for_new_value)
async def process_field_edit(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка нового значения поля"""
    data = await state.get_data()
    field = data.get('edit_field')
    new_value = message.text
    
    if not field:
        await message.reply("❌ Ошибка: поле не выбрано")
        await state.clear()
        return
    
    telegram_id = message.from_user.id
    user = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user.scalar_one_or_none()
    
    if not user:
        await message.reply("❌ Пользователь не найден")
        await state.clear()
        return
    
    # Обновляем поле
    setattr(user, field, new_value)
    await session.commit()
    
    field_names = {
        "name": "Имя",
        "city": "Город",
        "desired_position": "Должность",
        "skills": "Навыки", 
        "base_resume": "Резюме"
    }
    
    await message.reply(f"✅ **{field_names[field]}** успешно обновлено!")
    await state.clear()
    
    # Показываем обновленный профиль
    await cmd_profile(message, session)

@router.callback_query(F.data == "cancel_edit")
async def cancel_edit(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Отмена редактирования"""
    await state.clear()
    await callback.message.edit_text("❌ Редактирование отменено")
    await callback.answer()
    
    # Возвращаемся к меню профиля
    await cmd_profile(callback.message, session)

@router.callback_query(F.data == "delete_profile")
async def start_delete_profile(callback: CallbackQuery, state: FSMContext):
    """Начать процесс удаления профиля"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data="confirm_delete")],
        [InlineKeyboardButton(text="❌ Нет, отменить", callback_data="cancel_delete")]
    ])
    
    warning_text = """
⚠️ **ВНИМАНИЕ: Удаление профиля**

Это действие:
• ❌ Удалит все ваши данные
• ❌ Удалит настройки поиска
• ❌ Удалит сохраненные вакансии
• ❌ Удалит настройки LLM

**Действие необратимо!**

Вы уверены, что хотите удалить профиль?
    """
    
    await callback.message.edit_text(warning_text, reply_markup=keyboard)
    await state.set_state(DeleteProfileStates.waiting_for_confirmation)
    await callback.answer()

@router.callback_query(DeleteProfileStates.waiting_for_confirmation, F.data == "confirm_delete")
async def confirm_delete_profile(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Подтверждение удаления профиля"""
    telegram_id = callback.from_user.id
    
    user = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user.scalar_one_or_none()
    
    if not user:
        await callback.message.edit_text("❌ Профиль не найден")
        await state.clear()
        await callback.answer()
        return
    
    user_id = user.id
    
    try:
        # Удаляем связанные данные в правильном порядке
        # 1. Удаляем настройки LLM
        llm_settings = await session.execute(
            select(LLMSettings).where(LLMSettings.user_id == user_id)
        )
        llm_settings = llm_settings.scalar_one_or_none()
        if llm_settings:
            await session.delete(llm_settings)
        
        # 2. Удаляем связи пользователь-вакансии
        user_vacancies = await session.execute(
            select(UserVacancy).where(UserVacancy.user_id == user_id)
        )
        user_vacancies = user_vacancies.scalars().all()
        for uv in user_vacancies:
            await session.delete(uv)
        
        # 3. Удаляем настройки поиска
        search_settings = await session.execute(
            select(SearchSettings).where(SearchSettings.user_id == user_id)
        )
        search_settings = search_settings.scalars().all()
        for ss in search_settings:
            await session.delete(ss)
        
        # 4. Удаляем самого пользователя
        await session.delete(user)
        
        await session.commit()
        
        await callback.message.edit_text("""
🗑️ **Профиль успешно удален**

Все ваши данные были полностью удалены из системы.

Если захотите снова воспользоваться ботом, используйте команду /start для новой регистрации.

Спасибо, что пользовались нашим ботом! 👋
        """)
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при удалении профиля: {str(e)}")
        await session.rollback()
    
    await state.clear()
    await callback.answer()

@router.callback_query(DeleteProfileStates.waiting_for_confirmation, F.data == "cancel_delete")
async def cancel_delete_profile(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Отмена удаления профиля"""
    await state.clear()
    await callback.message.edit_text("✅ Удаление профиля отменено")
    await callback.answer()
    
    # Возвращаемся к меню профиля
    await cmd_profile(callback.message, session)


# ========== СПРАВКА И ОБРАБОТКА НЕИЗВЕСТНЫХ КОМАНД ==========

@router.message(F.text == "/help")
async def cmd_help(message: Message):
    """Показать список всех команд"""
    help_text = """
🤖 **Доступные команды:**

🔹 **Регистрация и профиль**
/start - Зарегистрироваться и создать профиль
/profile - Управление профилем (редактирование, удаление)

🔹 **Поиск вакансий**  
/search_settings - Настроить параметры поиска
/vacancies - Показать подобранные вакансии

🔹 **Действия с вакансиями**
Под каждой вакансией есть кнопки:
• 📄 Сгенерировать резюме - создать резюме под вакансию
• 📝 Сгенерировать cover letter - создать сопроводительное письмо
• 👎 Неинтересно - скрыть вакансию

💡 **Как пользоваться:**
1. Сначала зарегистрируйтесь через /start
2. Настройте поиск через /search_settings
3. Смотрите вакансии через /vacancies
4. Генерируйте резюме и cover letter подходящим вакансиям
5. Управляйте профилем через /profile
    """
    await message.reply(help_text)

# ========== ОБРАБОТКА НЕИЗВЕСТНЫХ КОМАНД И СООБЩЕНИЙ ==========
# ЭТОТ ОБРАБОТЧИК ДОЛЖЕН БЫТЬ САМЫМ ПОСЛЕДНИМ!

@router.message()
async def handle_unknown(message: Message):
    """Обработчик всех сообщений, которые не попали в другие обработчики"""
    if message.text.startswith('/'):
        help_text = """
❌ Неизвестная команда

📋 **Доступные команды:**
/start - Регистрация
/profile - Управление профилем
/search_settings - Настройка поиска
/vacancies - Список вакансий  
/help - Помощь по боту

💡 Напишите /help для подробной информации
        """
        await message.reply(help_text)
    else:
        help_text = """
💡 Я понимаю только команды. 

📋 **Основные команды:**
/start - Начать работу с ботом
/profile - Управление профилем  
/search_settings - Настроить поиск вакансий
/vacancies - Посмотреть вакансии
/help - Помощь по командам

Напишите /help для полной информации
        """
        await message.reply(help_text)

def register_handlers(dp):
    dp.include_router(router)


