import ollama
from sqlalchemy.orm import Session
from datetime import datetime
from models import Digest, SessionLocal, Entity

def generate_digest(news_list, topic=None):
    # Изменяем доступ к атрибутам объектов News
    news_text = "\n".join([f"➖ {news.text} ({news.link})" for news in news_list])

    prompt = f"""Ты — помощник для составления новостных дайджестов. 
        Отвечай строго на русском языке. Используй только предоставленные новости, не придумывай ничего. 

        Формат дайджеста:
        ☀️ {topic} — свежие новости:  
        {news_text}

        Составь связный дайджест по этим новостям.
        \n\n"""

    response = ollama.chat(model="llama3:8b", messages=[{"role": "user", "content": prompt}])
    digest_content = str(response["message"]["content"])

    return digest_content
