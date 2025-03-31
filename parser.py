import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--headless")
options.add_argument("--window-size=1920x1080")



def get_messages_from_channel(url, from_date, to_date, channel_name):
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        time.sleep(5)

        messages = []
        unique_texts = set()
        reached_from_date = False
        reached_to_date = False
        scroll_attempts = 0

        while not reached_from_date and scroll_attempts < 30:
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(5)
            print("Ищем элементы с классом 'tgme_widget_message_wrap'...")
            
            message_elements = driver.find_elements(By.CLASS_NAME, 'tgme_widget_message_wrap')
            print(f"Найдено {len(message_elements)} сообщений")
            
            message_elements = driver.find_elements(By.CLASS_NAME, 'tgme_widget_message_wrap')
            for message_element in message_elements:
                try:
                    try:
                        time_element = message_element.find_element(By.TAG_NAME, 'time')
                        date_str = time_element.get_attribute('datetime')
                        print(f"Дата сообщения: {date_str}")
                    except Exception as e:
                        print(f"❌ Ошибка при получении даты: {e}")

                    message_date = datetime.fromisoformat(date_str).replace(tzinfo=None)

                    if message_date < from_date:
                        reached_from_date = True
                        break
                except Exception:
                    continue
            scroll_attempts += 1

        logger.info(f"📌 Достигли даты: {from_date}")
        last_height = driver.execute_script("return document.body.scrollHeight")

        while not reached_to_date:
            message_elements = driver.find_elements(By.CLASS_NAME, 'tgme_widget_message_wrap')
            for message_element in message_elements:
                try:
                    time_element = message_element.find_element(By.TAG_NAME, 'time')
                    date_str = time_element.get_attribute('datetime')
                    message_date = datetime.fromisoformat(date_str).replace(tzinfo=None)
                    if from_date <= message_date <= to_date:
                        text_elements = message_element.find_elements(By.CLASS_NAME, 'tgme_widget_message_text')
                        text = text_elements[0].text.strip() if text_elements else "(без текста)"
                        data_elements = message_element.find_elements(By.CLASS_NAME, "tgme_widget_message_date")
                        try:
                            data_post_element = message_element.find_element(By.CSS_SELECTOR, '[data-post]')
                            data_post = data_post_element.get_attribute('data-post')

                            if data_post:
                                post_id = data_post.split('/')[-1]  # Берём последний элемент после "/"
                                post_link = f"https://t.me/{channel_name}/{post_id}"
                            else:
                                post_link = "(нет ссылки)"
                        except Exception:
                            post_link = "(ошибка получения ссылки)"
                        if text not in unique_texts:
                            unique_texts.add(text)
                            messages.append({
                                'date': message_date.strftime('%Y-%m-%d %H:%M:%S'),
                                'text': text,
                                'link': post_link
                            })
                    if message_date > to_date:
                        reached_to_date = True
                        break
                except Exception:
                    continue
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break

            last_height = new_height
            scroll_attempts += 1
            if scroll_attempts > 30:
                break

        driver.quit()
        return messages

    except Exception as e:
        logger.error(f"❌ Ошибка парсинга {url}: {e}")
        return []



# channel_url = convert_url("https://t.me/xor_journal")
# channel_name = channel_url.split('/')[-1]
# messages = get_messages_from_channel(channel_url, datetime.strptime("2025-03-27", '%Y-%m-%d'), datetime.strptime("2025-03-28", '%Y-%m-%d'))

# digest = generate_digest(messages, topic="Программирование")


