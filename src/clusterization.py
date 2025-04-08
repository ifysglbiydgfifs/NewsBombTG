from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import numpy as np
from sqlalchemy.orm import sessionmaker
from models import Entity, engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cluster_entities(entities):
    vectorizer = TfidfVectorizer(stop_words=None)
    entity_names = [entity[1] for entity in entities]
    X = vectorizer.fit_transform(entity_names)

    clustering = DBSCAN(eps=0.5, min_samples=2, metric="cosine").fit(X)

    return dict(zip([entity[0] for entity in entities], clustering.labels_))

Session = sessionmaker(bind=engine)
session = Session()

def clusterization_start():
    try:
        entities = session.query(Entity.id, Entity.name).all()

        if not entities:
            logger.warning("Нет сущностей в базе данных.")
        else:
            clusters = cluster_entities(entities)

            if clusters:
                for entity_id, cluster_id in clusters.items():
                    entity = session.query(Entity).filter(Entity.id == entity_id).first()
                    if entity:
                        entity.cluster_id = int(cluster_id)
                        session.add(entity)
                session.commit()
                logger.info("Кластеры успешно сохранены в базе данных.")
            else:
                logger.warning("Кластеры не были созданы.")
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при кластеризации: {e}")
    finally:
        session.close()