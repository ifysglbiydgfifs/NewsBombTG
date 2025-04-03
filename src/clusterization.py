import fasttext.util
from sklearn.cluster import DBSCAN
import numpy as np
from sqlalchemy.orm import sessionmaker
from models import Entity, engine
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Если не скачана модель для кластеризации (нет файла cc.ru.300.bin), раскоментить!!!!!!!!!!!

# try:
#     fasttext.util.download_model('ru', if_exists='ignore')  # Загрузка модели
#     model = fasttext.load_model('cc.ru.300.bin')  # Подключаем FastText
#     logger.info("FastText model loaded successfully.")
# except MemoryError as e:
#     logger.error(f"MemoryError: {e}")
#     logger.error("Not enough memory to load the FastText model.")
#     exit(1)
# except Exception as e:
#     logger.error(f"Error loading FastText model: {e}")
#     exit(1)

def get_entity_vector(entity_name, model):
    words = entity_name.split()
    vectors = [model[word] for word in words if word in model]

    if not vectors:
        return np.random.rand(300)  # Генерируем случайный вектор вместо пустого

    return sum(vectors) / len(vectors)

def cluster_entities(entities, model):
    vectors = []
    entity_ids = []

    for entity_id, entity_name in entities:
        vec = get_entity_vector(entity_name, model)
        if vec is not None:
            vectors.append(vec)
            entity_ids.append(entity_id)

    if not vectors:
        logger.warning("Нет данных для кластеризации.")
        return {}

    vectors = np.array(vectors)  # Преобразуем в numpy-массив

    # Запускаем DBSCAN
    clustering = DBSCAN(eps=0.5, min_samples=2, metric="cosine").fit(vectors)

    # Возвращаем соответствие: ID сущности -> кластер
    return dict(zip(entity_ids, clustering.labels_))

# Создание сессии для работы с БД
Session = sessionmaker(bind=engine)
session = Session()

def clusterization_start():
    try:
        # Получаем все сущности
        entities = session.query(Entity.id, Entity.name).all()

        if not entities:
            logger.warning("Нет сущностей в базе данных.")
        else:
            # Кластеризуем
            clusters = cluster_entities(entities, model)

            if clusters:
                # Записываем кластеры в базу
                for entity_id, cluster_id in clusters.items():
                    print(entity_id)
                    entity = session.query(Entity).filter(Entity.id == entity_id).first()
                    if entity:
                        # Преобразуем cluster_id в стандартный Python int
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