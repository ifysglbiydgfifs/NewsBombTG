from database import SessionLocal
from models import UserChannel

def convert_url(url):
    url = url.strip()

    if url.startswith("https://t.me/s/"):
        return url
    if url.startswith("t.me/") or url.startswith("https://t.me/"):
        channel_name = url.split("/")[-1]
        return f"https://t.me/s/{channel_name}"
    return url
