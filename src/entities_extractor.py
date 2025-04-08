from natasha import (
    Segmenter, MorphVocab, NewsEmbedding, NewsMorphTagger, 
    NewsSyntaxParser, NewsNERTagger, Doc
)
from entity_link import link_news_entities
from models import News, Entity, engine, news_entity_link
from sqlalchemy.orm import Session

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
    for message in messages:
        text = message['text']
        link = message['link']
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
                new_entity = Entity(name=entity_text, type=entity_type)
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
        else:
            print(f"⚠️ Не найдено сущностей для новости ID {news_id}")
    session.commit()
