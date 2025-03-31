from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Подключение к PostgreSQL
DATABASE_URL = "postgresql://postgres:123@localhost/DigestBot"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Функция для получения сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
