from sqlalchemy.orm import Session
from models import News, Entity, engine, news_entity_link

session = Session(engine)

def link_news_entities(news_id, entity_ids):
    news = session.get(News, news_id)
    if not news:
        print(f"Новость с ID {news_id} не найдена")
        return

    entities = session.query(Entity).filter(Entity.id.in_(entity_ids)).all()
    if not entities:
        print("Не найдены сущности с указанными ID")
        return

    for entity in entities:
        if entity not in news.entities:
            news.entities.append(entity)

    session.commit()
