from natasha import (
    Segmenter, MorphVocab, NewsEmbedding, NewsMorphTagger,
    NewsSyntaxParser, NewsNERTagger, Doc
)
from entity_link import link_news_entities
from models import News, Entity, engine, news_entity_link, Digest
from sqlalchemy.orm import Session
import time

from digest_generator import generate_digest

segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)
syntax_parser = NewsSyntaxParser(emb)
ner_tagger = NewsNERTagger(emb)
session = Session(engine)

def extract_entities(text):
    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    doc.parse_syntax(syntax_parser)
    doc.tag_ner(ner_tagger)

    entities = []
    for span in doc.spans:
        span.normalize(morph_vocab)
        entities.append((span.text, span.type))

    return entities

def extract_and_save_entities(messages):
    topics_to_news = {}

    for message in messages:
        text = message.text
        link = message.link
        print(link)
        print(f"\n📌 Обрабатываем новость: {text[:100]}...")

        existing_news = session.query(News).filter_by(text=text).first()
        if existing_news:
            news_id = existing_news.id
        else:
            print(link)
            new_news = News(title="Новость", text=text, link=link)
            session.add(new_news)
            session.commit()
            news_id = new_news.id

        extracted_entities = extract_entities(text)
        if not extracted_entities:
            print("⚠️ Natasha не нашла ни одной сущности в этом тексте!")
        else:
            print(f"✅ Найденные сущности: {extracted_entities}")

        entity_ids = []
        for entity_text, entity_type in extracted_entities:
            existing_entity = session.query(Entity).filter_by(name=entity_text).first()
            if existing_entity:
                entity_ids.append(existing_entity.id)
            else:
                new_entity = Entity(name=entity_text, type=entity_type, time=int(time.time() * 1000))  # Время в миллисекундах
                session.add(new_entity)
                session.commit()
                entity_ids.append(new_entity.id)

        if entity_ids:
            entity_ids = list(set(entity_ids))
            linked_entities = ",".join(map(str, entity_ids))

            print(f"🔗 Связываем новость ID {news_id} с сущностями {entity_ids}")

            for entity_id in entity_ids:
                entity = session.query(Entity).filter_by(id=entity_id).first()
                if entity:
                    other_ids = [eid for eid in entity_ids if eid != entity.id]
                    if other_ids:
                        entity.link = ",".join(map(str, other_ids))
                    else:
                        entity.link = None
                    session.add(entity)

            link_news_entities(news_id, entity_ids)

            topic = extracted_entities[0][1]
            if topic not in topics_to_news:
                topics_to_news[topic] = []
            topics_to_news[topic].append(message)

    for topic, news_list in topics_to_news.items():
        existing_digest = session.query(Digest).filter_by(type=topic).first()

        if not existing_digest:
            print(f"❗ Тема '{topic}' не найдена в таблице дайджестов, создаем новый.")
            digest_content = generate_digest(news_list, topic)
            new_digest = Digest(type=topic, content=digest_content)
            session.add(new_digest)
            session.commit()
            print(f"✅ Новый дайджест создан для темы: {topic}")

    session.commit()
