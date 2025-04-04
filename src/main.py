from parser_init import parse
from datetime import datetime
from entities_extractor import extract_and_save_entities
from clusterization import clusterization_start
from digest_generator import generate_digest

channel_url = "https://t.me/csu76"
channel_name = channel_url.split('/')[-1]
messages = parse(channel_url, datetime.strptime("2025-03-27", '%Y-%m-%d'), datetime.strptime("2025-03-28", '%Y-%m-%d'), channel_name)

generate_digest(messages)
extract_and_save_entities(messages)
clusterization_start()