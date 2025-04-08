from parser import get_messages_from_channel
from url_converter import convert_url
from datetime import datetime
from models import News, engine
from sqlalchemy.orm import Session

session = Session(engine)


def parse(link: str, from_date: datetime, to_date: datetime, channel_name: str):
    # Перед началом парсинга очищаем таблицу news
    session.query(News).delete()
    session.commit()

    url = convert_url(link)
    messages = get_messages_from_channel(url, from_date, to_date, channel_name)

    for message in messages:
        text = message['text']
        link = message['link']
        date = datetime.strptime(message['date'], '%Y-%m-%d %H:%M:%S')

        # Преобразуем datetime в UNIX timestamp в миллисекундах
        timestamp = int(date.timestamp() * 1000)

        # Проверяем, есть ли новость с таким текстом
        existing_news = session.query(News).filter_by(text=text).first()
        if existing_news:
            if not existing_news.link or existing_news.link == "(нет ссылки)":
                existing_news.link = link
                session.commit()
        else:
            new_news = News(title="Новость", text=text, time=timestamp, link=link)  # Сохраняем link
            session.add(new_news)
            session.commit()
    return messages
