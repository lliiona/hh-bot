import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

print("🔄 Инициализация базы данных...")

from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
print(f"📊 DATABASE_URL: {DATABASE_URL}")

# Исправляем URL для asyncpg - убираем все query параметры
if DATABASE_URL.startswith("postgresql"):
    # Разбираем URL на части
    if "?" in DATABASE_URL:
        base_url = DATABASE_URL.split("?")[0]
        print(f"🔄 Убираем query параметры: {base_url}")
        DATABASE_URL = base_url
    
    # Обязательно используем asyncpg
    if not DATABASE_URL.startswith("postgresql+asyncpg"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    print(f"🔄 Финальный URL: {DATABASE_URL}")

# Создаем engine с правильными параметрами SSL
try:
    if DATABASE_URL.startswith("postgresql+asyncpg"):
        # Для Neon.tech обязательно нужен SSL
        engine = create_async_engine(
            DATABASE_URL,
            echo=True,
            connect_args={
                "ssl": "require"  # Правильный способ указать SSL для asyncpg
            }
        )
    else:
        # Для SQLite
        engine = create_async_engine(
            DATABASE_URL,
            echo=True,
            connect_args={"check_same_thread": False}
        )
    print("✅ Асинхронный engine создан")
except Exception as e:
    print(f"❌ Ошибка создания engine: {e}")
    # Fallback на SQLite
    print("🔄 Используем SQLite как fallback...")
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        connect_args={"check_same_thread": False}
    )

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def create_tables():
    try:
        from db.models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблицы созданы успешно!")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
