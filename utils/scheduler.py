from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from sqlalchemy import select
from db.models import User, SearchSettings, Vacancy, UserVacancy
from db.connection import get_session
from services.hh_service import search_vacancies
import logging

logger = logging.getLogger(__name__)

async def send_daily_vacancies(bot: Bot):
    async for session in get_session():
        users = await session.execute(select(User))
        users = users.scalars().all()

        for user in users:
            settings = await session.execute(select(SearchSettings).where(SearchSettings.user_id == user.id))
            settings = settings.scalar_one_or_none()

            if not settings:
                continue

            try:
                vacancies_data = await search_vacancies(settings)

                new_vacancies = []
                for v_data in vacancies_data[:10]:  # Ограничим 10
                    # Проверить, не отправляли ли уже
                    existing = await session.execute(
                        select(Vacancy).where(Vacancy.hh_id == v_data['hh_id'])
                    )
                    vacancy = existing.scalar_one_or_none()

                    if not vacancy:
                        vacancy = Vacancy(**v_data)
                        session.add(vacancy)
                        await session.flush()  # Получить ID

                    # Проверить, отправляли ли пользователю
                    user_vacancy = await session.execute(
                        select(UserVacancy).where(
                            UserVacancy.user_id == user.id,
                            UserVacancy.vacancy_id == vacancy.id
                        )
                    )
                    if user_vacancy.scalar_one_or_none():
                        continue

                    new_vacancies.append(vacancy)
                    user_vacancy = UserVacancy(user_id=user.id, vacancy_id=vacancy.id)
                    session.add(user_vacancy)

                await session.commit()

                if new_vacancies:
                    message = "Новые вакансии для вас:\n\n"
                    for v in new_vacancies:
                        message += f"• {v.title} в {v.company}, {v.city}\nЗарплата: {v.salary}\n{v.url}\n\n"
                    await bot.send_message(user.telegram_id, message)

            except Exception as e:
                logger.error(f"Error sending vacancies to user {user.telegram_id}: {e}")

def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_vacancies, CronTrigger(hour=9), args=[bot])  # Каждый день в 9 утра
    return scheduler