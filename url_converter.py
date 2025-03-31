def convert_url(url):
    url = url.strip()

    if url.startswith("https://t.me/s/"):
        return url
    if url.startswith("t.me/") or url.startswith("https://t.me/"):
        channel_name = url.split("/")[-1]
        return f"https://t.me/s/{channel_name}"
    return url

def process_channels(user_id):
    db = SessionLocal()
    channels = db.query(UserChannel).filter_by(user_id=user_id).all()
    urls = [convert_url(ch.channel_url) for ch in channels]
    db.close()
    return urls
