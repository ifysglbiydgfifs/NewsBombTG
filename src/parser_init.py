from parser import get_messages_from_channel
from url_converter import convert_url
from datetime import datetime
from models import News, engine, news_entity_link, Entity
from sqlalchemy.orm import Session
from clusterization import clusterization_start
from digest_generator import generate_digest
from entities_extractor import extract_and_save_entities

session = Session(engine)

def parse(link: str, from_date: datetime, to_date: datetime, channel_name: str):
    session.query(news_entity_link).delete()
    session.query(Entity).delete()
    session.query(News).delete()
    session.commit()

    url = convert_url(link)
    messages = get_messages_from_channel(url, from_date, to_date, channel_name)

    for message in messages:
        text = message['text']
        link = message['link']
        date = datetime.strptime(message['date'], '%Y-%m-%d %H:%M:%S')

        timestamp = int(date.timestamp() * 1000)

        existing_news = session.query(News).filter_by(text=text).first()
        if existing_news:
            if not existing_news.link or existing_news.link == "(нет ссылки)":
                existing_news.link = link
                session.commit()
        else:
            new_news = News(title="Новость", text=text, time=timestamp, link=link)
            session.add(new_news)
            session.commit()

    generate_digest(messages)
    extract_and_save_entities(messages)
    clusterization_start()

    return messages
