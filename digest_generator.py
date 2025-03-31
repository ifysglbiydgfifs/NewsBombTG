import ollama

def generate_digest(news_list, topic=None):
    news_text = "\n".join([f"➖ {news['text']} ({news['link']})" for news in news_list])
    """
    Генерирует дайджест на основе списка новостей с использованием модели Ollama.
    :param news_list: Список новостей (словарь с текстом и ссылкой).
    :param topic: Опциональная тема дайджеста.
    :return: Сформированный дайджест.
    """
    prompt = f"""Ты — помощник для составления новостных дайджестов. 
        Отвечай строго на русском языке. Используй только предоставленные новости, не придумывай ничего. 

        Формат дайджеста:
        ☀️ {topic} — свежие новости:  
        {news_text}

        Составь связный дайджест по этим новостям.
        \n\n"""

    response = ollama.chat(model="llama3:8b", messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"]