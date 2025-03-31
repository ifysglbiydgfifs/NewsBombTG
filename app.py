from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, get_db
from models import News, Entity

app = FastAPI()

# Получение графа сущностей с привязанными к ним новостями
@app.get("/graph")
def get_graph(db: Session = Depends(get_db)):
    entities = db.query(Entity).all()
    graph_data = []

    for entity in entities:
        news_list = [{"id": news.id, "text": news.text, "link": news.link} for news in entity.news]
        graph_data.append({
            "id": entity.id,
            "name": entity.name,
            "type": entity.type,
            "news": news_list
        })

    return {"nodes": graph_data}
