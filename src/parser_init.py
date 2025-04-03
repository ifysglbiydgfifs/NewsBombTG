from parser import get_messages_from_channel
from url_converter import convert_url
from datetime import datetime
from models import News, Entity, engine, news_entity_link
from sqlalchemy.orm import Session

session = Session(engine)

def parse(link: str, from_date: datetime, to_date: datetime, channel_name: str):
    url = convert_url(link)
    messages = get_messages_from_channel(url, from_date, to_date, channel_name)
    
    for message in messages:
        text = message['text']
        link = message['link']
        
        existing_news = session.query(News).filter_by(text=text).first()
        if existing_news:
            if not existing_news.link or existing_news.link == "(нет ссылки)":
                existing_news.link = link
                session.commit()
        else:
            print(link)
            new_news = News(title="Новость", text=text, link=link)
            session.add(new_news)
            session.commit()
    return messages