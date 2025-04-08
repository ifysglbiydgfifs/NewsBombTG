from sqlalchemy import create_engine, ForeignKey, Table, Column, Integer, String, BigInteger
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

DATABASE_URL = "postgresql://postgres:123@localhost/DigestBot"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Промежуточная таблица для связи многие-ко-многим
news_entity_link = Table(
    "news_entity_links", Base.metadata,
    Column("news_id", Integer, ForeignKey("news.id"), primary_key=True),
    Column("entity_id", Integer, ForeignKey("entities.id"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, nullable=True)
    credits = Column(Integer, default=0)  # Внутренняя валюта
    channels = relationship("Channel", back_populates="user", cascade="all, delete-orphan")

class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    cluster_id = Column(Integer, nullable=True)
    link = Column(String, nullable=True)

    news = relationship("News", secondary=news_entity_link, back_populates="entities")

class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    text = Column(String, nullable=False)
    time = Column(BigInteger, nullable=False)

    entities = relationship("Entity", secondary=news_entity_link, back_populates="news")

class UserChannel(Base):
    __tablename__ = "user_channels"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    channel_url = Column(String, nullable=False)

    user = relationship("User", back_populates="channels")

User.channels = relationship("UserChannel", back_populates="user")

Base.metadata.create_all(engine)