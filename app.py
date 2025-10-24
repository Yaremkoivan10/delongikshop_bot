# Імпортуємо необхідні бібліотеки
from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import json
import uuid
import csv
import os
from io import StringIO
import random
import hashlib
import datetime
from threading import Thread
import telebot
from telebot import types
import logging
import sys
import time
from collections import defaultdict, Counter
import re
import requests
import zipfile
import shutil

# -----------------
# Налаштування
# -----------------
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# --- Назви файлів ---
DATA_FILE = 'data.json'
CLIENTS_FILE = 'clients.json'
CHATBOT_KNOWLEDGE_FILE = 'chatbot_knowledge.json'
PAYMENTS_FILE = 'pay.json'
# Нові файли для інтеграції
SUPPORT_TICKETS_FILE = 'support_tickets.json'
USERS_FILE = 'users.json'
SYSTEM_LOG_FILE = 'system_log.json'
BACKUP_DIR = 'backups'

# --- Telegram Bot ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8304901511:AAFmmhpw0qwtLq14NeOpM5LVEgkQIZcZGvk")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1251880919")
ADMIN_IDS = [int(TELEGRAM_CHAT_ID)] if TELEGRAM_CHAT_ID.isdigit() else []

if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or not ADMIN_IDS:
    logging.warning("Токен Telegram-бота або ID чату не налаштовано. Функції бота будуть недоступні.")
    bot = None
else:
    bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode="HTML")

# --- ПОЧАТОК БЛОКУ ЛОКАЛІЗАЦІЇ ---
LANGUAGES = {
    'uk': {
        "welcome": "👋 Вітаю у нашому магазині!\nДля початку, давайте зареєструємось. Введіть ваше ім'я та прізвище:",
        "welcome_back": "Вітаю, {name}! 👋",
        "register_phone": "Чудово! Тепер введіть ваш номер телефону:",
        "register_success": "Дякую, {name}! Реєстрація завершена. Тепер ви можете користуватися всіма функціями магазину.",
        "main_menu": "Головне меню:",
        "btn_catalog": "🛍 Каталог",
        "btn_purchases": "🔑 Мої покупки",
        "btn_profile": "👤 Мій профіль",
        "btn_reviews": "✍️ Відгуки",
        "btn_promotions": "📢 Акції",
        "btn_support": "💬 Підтримка",
        "btn_about": "ℹ️ Про магазин",
        "btn_settings": "⚙️ Налаштування",
        "btn_wishlist": "❤️ Улюблене",
        "btn_bundles": "🎁 Колекції",
        "btn_news": "📰 Новини",
        "btn_invite": "🤝 Запросити друга",
        "btn_cart": "🛒 Кошик",
        "btn_deal_of_the_day": "🔥 Товар дня",
        "settings_menu": "<b>⚙️ Налаштування</b>\n\nОберіть, що хочете змінити:",
        "btn_change_name": "Змінити ім'я та прізвище",
        "btn_change_phone": "Змінити телефон",
        "btn_language": "🌐 Мова",
        "language_menu": "Оберіть мову:",
        "lang_set_success": "✅ Мову успішно змінено!",
        "ask_new_name": "Введіть нове ім'я та прізвище:",
        "ask_new_phone": "Введіть новий номер телефону:",
        "name_changed": "✅ Ваше ім'я було успішно змінено!",
        "phone_changed": "✅ Ваш номер телефону було успішно змінено!",
        "catalog_title": "🗂️ <b>Оберіть категорію:</b>",
        "all_products": "Всі товари",
        "category_products": "<b>Товари в категорії «{category_name}» (стор. {page}):</b>",
        "all_products_paginated": "<b>Весь каталог товарів (стор. {page}):</b>",
        "no_products_in_category": "\n\nНа жаль, тут ще немає товарів.",
        "btn_to_categories": "⤴️ До категорій",
        "btn_prev_page": "⬅️ Назад",
        "btn_next_page": "Вперед ➡️",
        "wishlist_title": "<b>❤️ Ваші улюблені товари:</b>",
        "wishlist_empty": "Ваш список улюбленого порожній. Ви можете додати товари з каталогу.",
        "added_to_wishlist": "✅ Додано до улюбленого!",
        "removed_from_wishlist": "💔 Видалено з улюбленого.",
        "btn_add_to_wishlist": "❤️ Додати в улюблене",
        "btn_remove_from_wishlist": "💔 Видалити з улюбленого",
        "bundles_title": "<b>🎁 Доступні колекції:</b>",
        "bundles_empty": "Наразі немає доступних колекцій.",
        "bundle_details": "<b>Колекція «{name}»</b>\n\n{description}\n\n<b>Склад:</b>\n{products}\n\n<s>Загальна ціна: {total_price} грн</s>\n<b>Ціна зі знижкою: {discount_price} грн!</b>",
        "buy_bundle": "Купити колекцію за {price} грн",
        "bundle_purchase_success": "✅ Ви успішно придбали колекцію «{name}»!\n\nОсь ваші товари:",
        "news_title": "<b>📰 Останні новини</b>\n\n",
        "no_news": "Наразі новин немає.",
        "referral_text": "<b>🤝 Ваше реферальне посилання:</b>\n\nПоділіться цим посиланням з друзями. Коли новий користувач зареєструється за ним, ви отримаєте <b>{bonus} Delon-гіків</b> на свій бонусний рахунок!\n\n<code>{link}</code>",
        "referral_welcome": "\n\n🎉 Вітаємо! Ви зареєструвалися за запрошенням і ваш друг отримав бонус!",
        "user_banned": "Вибачте, ваш акаунт заблоковано. Зверніться до підтримки.",
        "btn_end_chat": "💬 Завершити діалог",
        "support_start": "Ви увійшли в режим підтримки. Усі ваші повідомлення будуть перенаправлені оператору. Натисніть кнопку нижче, щоб вийти.",
        "support_end": "Ви вийшли з режиму підтримки. Головне меню знову доступне.",
        "ask_use_bonus": "У вас є {points} Delon-гіків. Хочете використати їх для отримання знижки?",
        "btn_yes": "Так",
        "btn_no": "Ні",
        "bonus_applied": "✅ Бонуси застосовано! Нова сума до сплати: {new_price} грн. Залишок бонусів: {remaining_points}.",
        "cart_title": "🛒 <b>Ваш кошик</b>",
        "cart_empty": "Ваш кошик порожній.",
        "added_to_cart": "✅ Додано в кошик!",
        "btn_clear_cart": "🗑 Очистити кошик",
        "btn_checkout": "✅ Оформити замовлення",
        "total_price": "<b>Загальна сума:</b>",
        "btn_add_to_cart": "➕ Додати в кошик",
        "btn_buy_now": "⚡️ Купити зараз",
        "wishlist_notification": "🔔 <b>Гарні новини!</b>\nТовар з вашого списку бажань <b>«{product_name}»</b> тепер зі знижкою! 🔥",
        "deal_of_the_day_title": "🔥 <b>Товар дня!</b> 🔥\n\nТільки сьогодні спеціальна пропозиція:",
        "no_deal_of_the_day": "На жаль, сьогодні спеціальних пропозицій немає. Завітайте пізніше!",
        "profile_rank": "<b>Ранг:</b> {rank_name} ({bonus_percent}%)",
        "rank_up_notification": "🎉 <b>Вітаємо!</b>\n\nВи досягли нового рангу: <b>{rank_name}</b>! Тепер ваш кешбек з покупок складає <b>{bonus_percent}%</b>. Дякуємо, що ви з нами!",
        "personal_promocode_notification": "🎁 <b>Особистий подарунок для вас!</b>\n\nМи згенерували для вас персональний промокод на знижку <b>{discount}%</b>:\n\n<code>{code}</code>\n\nВін дійсний для одного використання. Вдалої покупки!"
    },
    'ru': {
        # ... (аналогічні переклади для інших мов)
    },
    'en': {
        # ... (аналогічні переклади для інших мов)
    }
}

def get_text(key, user_id):
    """Отримує текст для вказаного ключа на мові користувача."""
    user_id = str(user_id)
    lang = clients_db.get(user_id, {}).get('lang', 'uk')
    return LANGUAGES.get(lang, LANGUAGES['uk']).get(key, f"_{key}_")

# --- КІНЕЦЬ БЛОКУ ЛОКАЛІЗАЦІЇ ---

# --- Допоміжні функції для роботи з файлами ---
def load_json_file(filename, default_value=[]):
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        return default_value
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return default_value

def save_json_file(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_clients():
    """Завантажує дані клієнтів з JSON-файлу або створює новий."""
    return load_json_file(CLIENTS_FILE, {})

def save_clients(clients_data):
    """Зберігає дані клієнтів в JSON-файл."""
    save_json_file(CLIENTS_FILE, clients_data)

def load_data():
    """Завантажує дані з JSON-файлу або створює новий, якщо він відсутній."""
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        logging.warning(f"Файл {DATA_FILE} не знайдено або він порожній. Створюється нова структура.")
        default_data = {
            "products": [], "users": [], "orders": [], "discounts": [], "reviews": [],
            "categories": [], "bundles": [], "news": [], "promocodes": [],
            "bonus_settings": {"referral_bonus": 20, "purchase_bonus_percent": 5},
            "shop_info": {"name": "DelongikShop", "description": "Найкращі товари тут."},
            "loyalty_levels": [
                {"name": "Bronze", "threshold": 0, "bonus_percent": 5},
                {"name": "Silver", "threshold": 5000, "bonus_percent": 7},
                {"name": "Gold", "threshold": 15000, "bonus_percent": 10}
            ],
            "deal_of_the_day": {}
        }
        save_data(default_data)
        return default_data
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Додаємо нові ключі, якщо їх немає
            for key in ["products", "users", "orders", "discounts", "reviews", "shop_info", "categories", "bundles", "news", "promocodes", "bonus_settings", "loyalty_levels", "deal_of_the_day"]:
                if key not in data:
                    if key == "shop_info" or key == "deal_of_the_day": data[key] = {}
                    elif key == "bonus_settings": data[key] = {"referral_bonus": 20, "purchase_bonus_percent": 5}
                    elif key == "loyalty_levels": data[key] = [
                        {"name": "Bronze", "threshold": 0, "bonus_percent": 5},
                        {"name": "Silver", "threshold": 5000, "bonus_percent": 7},
                        {"name": "Gold", "threshold": 15000, "bonus_percent": 10}
                    ]
                    else: data[key] = []
            logging.info(f"Дані успішно завантажено з {DATA_FILE}.")
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        logging.error(f"Помилка читання {DATA_FILE}. Файл може бути пошкоджено.")
        sys.exit(f"Критична помилка: неможливо прочитати файл даних {DATA_FILE}.")

def save_data(data):
    """Зберігає дані в JSON-файл."""
    save_json_file(DATA_FILE, data)

def load_chatbot_knowledge():
    """Завантажує базу знань чат-бота з файлу або ініціалізує нову."""
    return load_json_file(CHATBOT_KNOWLEDGE_FILE, [])

def save_chatbot_knowledge(knowledge):
    """Зберігає базу знань чат-бота в файл."""
    save_json_file(CHATBOT_KNOWLEDGE_FILE, knowledge)

def load_payment_details():
    """Завантажує платіжні реквізити."""
    return load_json_file(PAYMENTS_FILE, {})

def save_payment_details(details):
    """Зберігає платіжні реквізити."""
    save_json_file(PAYMENTS_FILE, details)

# --- Завантаження початкових даних ---
db = load_data()
clients_db = load_clients()
chatbot_knowledge = load_chatbot_knowledge()
payment_details = load_payment_details()
support_tickets = load_json_file(SUPPORT_TICKETS_FILE, [])
panel_users = load_json_file(USERS_FILE, [])
system_logs = load_json_file(SYSTEM_LOG_FILE, [])

# --- Функція логування дій ---
def log_action(action, details):
    global system_logs
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "action": action,
        "details": details
    }
    system_logs.insert(0, log_entry)
    system_logs = system_logs[:200]
    save_json_file(SYSTEM_LOG_FILE, system_logs)

# --- Інші допоміжні функції ---
REGIONS = {
    "Автономна Республіка Крим": ["Сімферополь", "Керч", "Євпаторія", "Ялта", "Феодосія", "Джанкой"],
    "Вінницька область": ["Вінниця", "Жмеринка", "Могилів-Подільський", "Козятин", "Хмільник", "Ладижин"],
    "Волинська область": ["Луцьк", "Ковель", "Нововолинськ", "Володимир", "Камінь-Каширський", "Ківерці"],
    "Дніпропетровська область": ["Дніпро", "Кривий Ріг", "Кам'янське", "Нікополь", "Павлоград", "Новомосковськ"],
    "Донецька область": ["Краматорськ", "Маріуполь", "Слов'янськ", "Покровськ", "Костянтинівка", "Бахмут"],
    "Житомирська область": ["Житомир", "Бердичів", "Коростень", "Новоград-Волинський", "Малин", "Коростишів"],
    "Закарпатська область": ["Ужгород", "Мукачево", "Хуст", "Виноградів", "Берегове", "Свалява"],
    "Запорізька область": ["Запоріжжя", "Мелітополь", "Бердянськ", "Енергодар", "Токмак", "Пологи"],
    "Івано-Франківська область": ["Івано-Франківськ", "Калуш", "Коломия", "Надвірна", "Долина", "Бурштин"],
    "Київська область": ["Київ", "Біла Церква", "Бровари", "Бориспіль", "Фастів", "Ірпінь", "Вишгород"],
    "Кіровоградська область": ["Кропивницький", "Олександрія", "Світловодськ", "Знам'янка", "Долинська", "Новоукраїнка"],
    "Луганська область": ["Сєвєродонецьк", "Лисичанськ", "Алчевськ", "Хрустальний", "Старобільськ", "Рубіжне"],
    "Львівська область": ["Львів", "Дрогобич", "Червоноград", "Стрий", "Самбір", "Борислав"],
    "Миколаївська область": ["Миколаїв", "Первомайськ", "Южноукраїнськ", "Вознесенськ", "Новий Буг", "Очаків"],
    "Одеська область": ["Одеса", "Чорноморськ", "Ізмаїл", "Подільськ", "Білгород-Дністровський", "Южне"],
    "Полтавська область": ["Полтава", "Кременчук", "Горішні Плавні", "Лубни", "Миргород", "Гадяч"],
    "Рівненська область": ["Рівне", "Вараш", "Дубно", "Сарни", "Костопіль", "Березне"],
    "Сумська область": ["Суми", "Конотоп", "Шостка", "Охтирка", "Ромни", "Глухів"],
    "Тернопільська область": ["Тернопіль", "Чортків", "Кременець", "Бережани", "Заліщики", "Монастириська"],
    "Харківська область": ["Харків", "Ізюм", "Лозова", "Куп'янськ", "Чугуїв", "Первомайський"],
    "Херсонська область": ["Херсон", "Нова Каховка", "Каховка", "Генічеськ", "Скадовськ", "Олешки"],
    "Хмельницька область": ["Хмельницький", "Кам'янець-Подільський", "Шепетіка", "Нетішин", "Славута"],
    "Черкаська область": ["Черкаси", "Умань", "Сміла", "Золотоноша", "Канів", "Корсунь-Шевченківський"],
    "Чернівецька область": ["Чернівці", "Сторожинець", "Новоселиця", "Хотин", "Заставна"],
    "Чернігівська область": ["Чернігів", "Ніжин", "Прилуки", "Бахмач", "Корюківка", "Мена"],
    "Місто Київ": ["Київ"]
}
ORDER_STATE = {}

def strip_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def get_product_by_id(product_id):
    return next((p for p in db['products'] if p.get('id') == product_id), None)

def apply_discounts(products, discounts):
    products_copy = [p.copy() for p in products]
    for product in products_copy:
        product['discount_percent'] = 0
        product['discounted_price'] = product['price']
        for discount in discounts:
            if discount['target'] == 'all' or (discount['target'] == 'specific' and product.get('id') in discount.get('product_ids', [])):
                discount_percent = discount['percentage']
                product['discount_percent'] = discount_percent
                product['discounted_price'] = round(product['price'] * (1 - discount_percent / 100))
    return products_copy

def cleanup_old_news():
    global db
    if 'news' not in db or not db['news']:
        return
    seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    valid_news = [item for item in db['news'] if 'date' in item and item['date'] and datetime.datetime.fromisoformat(item['date']) > seven_days_ago]
    if len(valid_news) < len(db['news']):
        logging.info(f"Видалено {len(db['news']) - len(valid_news)} старих новин.")
        db['news'] = valid_news
        save_data(db)

cleanup_old_news()

def send_admin_notification(message_text):
    """Відправляє повідомлення всім адміністраторам."""
    if not bot:
        logging.warning("Спроба відправити сповіщення, але бот не ініціалізовано.")
        return
    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(admin_id, message_text, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Не вдалося відправити сповіщення адміністратору {admin_id}: {e}")

def notify_users_about_discount(discount):
    """Сповіщає користувачів про нову знижку на товари з їхнього списку бажань."""
    if discount.get('target') != 'specific':
        return # Наразі сповіщаємо тільки про знижки на конкретні товари

    product_ids = discount.get('product_ids', [])
    for user_id, user_data in clients_db.items():
        wishlist = user_data.get('wishlist', [])
        for product_id in product_ids:
            if product_id in wishlist:
                product = get_product_by_id(product_id)
                if product:
                    try:
                        bot.send_message(
                            user_id,
                            get_text("wishlist_notification", user_id).format(product_name=product['name'])
                        )
                        # Щоб не спамити, відправляємо одне повідомлення на користувача
                        break 
                    except Exception as e:
                        logging.error(f"Не вдалося відправити сповіщення про знижку користувачу {user_id}: {e}")

# -----------------
# Flask API
# -----------------

@app.route("/")
def index_page():
    return send_from_directory('.', 'admin.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if not bot:
        return jsonify({"message": "Telegram Bot не налаштовано"}), 500
    if 'file' not in request.files:
        return jsonify({"message": "Файл не знайдено"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "Файл не вибрано"}), 400
    try:
        file_type = file.content_type
        if 'image' in file_type:
            msg = bot.send_photo(TELEGRAM_CHAT_ID, file)
            file_id = msg.photo[-1].file_id
            file_type_out = 'photo'
        else:
            msg = bot.send_document(TELEGRAM_CHAT_ID, file)
            file_id = msg.document.file_id
            file_type_out = 'document'
        bot.delete_message(TELEGRAM_CHAT_ID, msg.message_id)
        return jsonify({"file_id": file_id, "file_type": file_type_out}), 200
    except Exception as e:
        logging.error(f"Помилка завантаження файлу в Telegram: {e}")
        return jsonify({"message": "Не вдалося завантажити файл"}), 500

# --- Головна панель та Аналітика ---
@app.route("/api/admin/stats", methods=['GET'])
def get_admin_stats():
    total_revenue = sum(o.get('totalPrice', 0) for o in db['orders'] if o.get('status') == 'Виконано')
    products_no_content = sum(1 for p in db['products'] if p.get('product_type') == 'link' and not p.get('content', '').strip())
    total_referrals = sum(c.get('referrals_count', 0) for c in clients_db.values())
    stats = {
        "total_revenue": total_revenue,
        "total_orders": len(db['orders']),
        "total_clients": len(clients_db),
        "total_referrals": total_referrals,
        "pending_reviews": sum(1 for r in db['reviews'] if not r.get('approved')),
        "products_no_content": products_no_content,
    }
    return jsonify(stats)

@app.route("/api/admin/analytics", methods=['GET'])
def get_analytics_data():
    orders = db.get('orders', [])
    reviews = db.get('reviews', [])
    revenue_by_day = defaultdict(float)
    today = datetime.date.today()
    for i in range(7):
        day = today - datetime.timedelta(days=i)
        revenue_by_day[day.strftime('%Y-%m-%d')] = 0
    for order in orders:
        if order.get('status') == 'Виконано' and 'date' in order:
            order_date = datetime.datetime.fromisoformat(order['date']).date()
            if (today - order_date).days < 7:
                revenue_by_day[order_date.strftime('%Y-%m-%d')] += order.get('totalPrice', 0)
    sorted_revenue = sorted(revenue_by_day.items())
    revenue_chart_data = {
        "labels": [datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%d.%m') for date, _ in sorted_revenue],
        "data": [amount for _, amount in sorted_revenue]
    }
    product_sales = Counter()
    for order in orders:
        if order.get('status') == 'Виконано':
            for item in order.get('items', []):
                product_sales[item.get('product_name', 'Невідомий товар')] += 1
    top_products = [{"name": name, "sales": count} for name, count in product_sales.most_common(5)]
    completed_orders = [o for o in orders if o.get('status') == 'Виконано']
    total_revenue = sum(o.get('totalPrice', 0) for o in completed_orders)
    average_check = (total_revenue / len(completed_orders)) if completed_orders else 0
    review_stats = {"approved": sum(1 for r in reviews if r.get('approved')), "total": len(reviews)}
    registrations_by_day = defaultdict(int)
    for i in range(7):
        day = today - datetime.timedelta(days=i)
        registrations_by_day[day.strftime('%Y-%m-%d')] = 0
    for client_id, client_data in clients_db.items():
        reg_date_str = client_data.get('registration_date')
        if reg_date_str:
            reg_date = datetime.datetime.fromisoformat(reg_date_str).date()
            if (today - reg_date).days < 7:
                 registrations_by_day[reg_date.strftime('%Y-%m-%d')] += 1
    sorted_registrations = sorted(registrations_by_day.items())
    registrations_chart_data = {
        "labels": [datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%d.%m') for date, _ in sorted_registrations],
        "data": [count for _, count in sorted_registrations]
    }
    analytics = {
        "revenue_chart": revenue_chart_data,
        "registrations_chart": registrations_chart_data,
        "top_products": top_products,
        "kpi": {"average_check": round(average_check, 2), "review_stats": review_stats}
    }
    return jsonify(analytics)

# --- Клієнти (CRM) ---
@app.route("/api/admin/clients", methods=['GET'])
def get_all_clients():
    client_list = [{**data, 'user_id': uid} for uid, data in clients_db.items()]
    return jsonify(client_list)

@app.route("/api/admin/clients/<client_id>/ban", methods=['POST'])
def ban_client(client_id):
    if client_id in clients_db:
        data = request.json
        is_banned = data.get('ban', False)
        clients_db[client_id]['is_banned'] = is_banned
        save_clients(clients_db)
        action = "заблоковано" if is_banned else "розблоковано"
        log_action("Client Status Change", f"Client {client_id} was {action}.")
        return jsonify({"message": f"Клієнта успішно {action}"}), 200
    return jsonify({"message": "Клієнта не знайдено"}), 404

@app.route("/api/admin/clients/<client_id>/details", methods=['GET'])
def get_client_details(client_id):
    client = clients_db.get(client_id)
    if not client:
        return jsonify({"message": "Клієнта не знайдено"}), 404
    client['user_id'] = client_id
    client_orders = [o for o in db['orders'] if str(o.get('telegram_id')) == str(client_id)]
    ltv = sum(o.get('totalPrice', 0) for o in client_orders if o.get('status') == 'Виконано')
    return jsonify({"client": client, "orders": client_orders, "ltv": ltv})

@app.route("/api/admin/clients/<client_id>/notes", methods=['POST'])
def add_client_note(client_id):
    if client_id in clients_db:
        if 'notes' not in clients_db[client_id]:
            clients_db[client_id]['notes'] = []
        note = {
            "date": datetime.datetime.now().isoformat(),
            "text": request.json.get('text'),
            "author": "Admin"
        }
        clients_db[client_id]['notes'].insert(0, note)
        save_clients(clients_db)
        log_action("Client Note Added", f"Note added for client {client_id}.")
        return jsonify(clients_db[client_id]), 200
    return jsonify({"message": "Клієнта не знайдено"}), 404

# --- Підтримка (Тікети) ---
@app.route("/api/support-tickets", methods=['GET'])
def get_tickets():
    return jsonify(support_tickets)

@app.route("/api/support-tickets/<ticket_id>", methods=['GET'])
def get_ticket(ticket_id):
    ticket = next((t for t in support_tickets if t['id'] == ticket_id), None)
    return jsonify(ticket) if ticket else (jsonify({"message": "Тікет не знайдено"}), 404)

@app.route("/api/support-tickets/<ticket_id>/reply", methods=['POST'])
def reply_to_ticket(ticket_id):
    ticket = next((t for t in support_tickets if t['id'] == ticket_id), None)
    if not ticket:
        return jsonify({"message": "Тікет не знайдено"}), 404
    data = request.json
    ticket['messages'].append({
        "sender": "admin",
        "text": data.get('message'),
        "timestamp": datetime.datetime.now().isoformat()
    })
    ticket['status'] = data.get('status', ticket['status'])
    ticket['last_updated'] = datetime.datetime.now().isoformat()
    save_json_file(SUPPORT_TICKETS_FILE, support_tickets)
    log_action("Support Ticket Reply", f"Replied to ticket {ticket_id}.")
    if bot and ticket.get('client_id'):
        try:
            bot.send_message(ticket['client_id'], f"Відповідь на ваше звернення #{ticket_id[:6]}:\n\n{data.get('message')}")
        except Exception as e:
            logging.error(f"Не вдалося відправити відповідь на тікет {ticket_id} в Telegram: {e}")
    return jsonify(ticket)

# --- Товари, Категорії, Колекції ---
@app.route("/api/products", methods=['GET', 'POST'])
def handle_products():
    if request.method == 'GET':
        discounts = db.get("discounts", [])
        products_with_discounts = apply_discounts(db["products"], discounts)
        return jsonify(products_with_discounts)
    if request.method == 'POST':
        data = request.json
        data['id'] = str(uuid.uuid4())
        data.setdefault('product_type', 'link')
        data.setdefault('content', '')
        data.setdefault('category_id', '')
        db['products'].insert(0, data)
        save_data(db)
        log_action("Product Created", f"Product '{data['name']}' created.")
        return jsonify(data), 201

@app.route("/api/products/<product_id>", methods=['GET', 'PUT', 'DELETE'])
def handle_product(product_id):
    product = next((p for p in db['products'] if p.get('id') == product_id), None)
    if not product:
        return jsonify({"message": "Товар не знайдено"}), 404
    if request.method == 'GET':
        discounts = db.get("discounts", [])
        product_with_discount = apply_discounts([product], discounts)[0]
        return jsonify(product_with_discount)
    if request.method == 'PUT':
        data = request.json
        product.update(data)
        save_data(db)
        log_action("Product Updated", f"Product '{product['name']}' ({product_id}) updated.")
        return jsonify(product)
    if request.method == 'DELETE':
        product_name = product.get('name', 'N/A')
        db['products'] = [p for p in db['products'] if p.get('id') != product_id]
        save_data(db)
        log_action("Product Deleted", f"Product '{product_name}' ({product_id}) deleted.")
        return jsonify({"message": "Товар видалено"})

@app.route("/api/products/import", methods=['POST'])
def import_products():
    if 'file' not in request.files:
        return jsonify({"message": "Файл не знайдено"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "Файл не вибрано"}), 400
    new_products_count = 0
    try:
        stream = StringIO(file.stream.read().decode("utf-8"))
        csv_reader = csv.DictReader(stream)
        products_to_add = []
        for i, row in enumerate(csv_reader):
            try:
                product_name = row.get("Назва_позиції_укр", "").strip()
                product_price_str = row.get("Ціна", "0").replace(',', '.')
                product_description = row.get("Опис_укр", "").strip()
                image_url = row.get("Посилання_зображення", "").strip()
                product_description = strip_html_tags(product_description).strip()
                try:
                    product_price = int(float(product_price_str))
                except (ValueError, TypeError):
                    product_price = 0
                if product_name and product_price > 0:
                    products_to_add.append({
                        "id": str(uuid.uuid4()),
                        "name": product_name,
                        "price": product_price,
                        "description": product_description,
                        "image": image_url if image_url else "https://placehold.co/400x300/4a5568/ffffff?text=Product",
                        "product_type": "link",
                        "content": "",
                        "category_id": ""
                    })
            except Exception as row_error:
                logging.error(f"Помилка обробки рядка {i+1} у CSV: {row_error}")
                continue
        db["products"].extend(products_to_add)
        save_data(db)
        new_products_count = len(products_to_add)
    except Exception as e:
        logging.error(f"Помилка імпорту файлу: {e}")
        return jsonify({"message": f"Помилка обробки файлу: {e}"}), 500
    return jsonify({"message": f"Успішно імпортовано {new_products_count} товарів.", "count": new_products_count})

@app.route("/api/products/clear", methods=['DELETE'])
def clear_products():
    db["products"] = []
    save_data(db)
    return jsonify({"message": "Усі товари успішно видалено"})

@app.route("/api/categories", methods=['GET', 'POST'])
def handle_categories():
    if request.method == 'GET':
        return jsonify(db.get("categories", []))
    if request.method == 'POST':
        data = request.json
        name = data.get('name', '').strip()
        if not name:
            return jsonify({"message": "Назва категорії не може бути порожньою"}), 400
        new_category = {"id": str(uuid.uuid4()), "name": name}
        db["categories"].append(new_category)
        save_data(db)
        return jsonify(new_category), 201

@app.route("/api/categories/<category_id>", methods=['DELETE'])
def delete_category(category_id):
    db["categories"] = [cat for cat in db["categories"] if cat.get('id') != category_id]
    for product in db["products"]:
        if product.get('category_id') == category_id:
            product['category_id'] = ""
    save_data(db)
    return jsonify({"message": "Категорію видалено"}), 200

@app.route("/api/bundles", methods=['GET', 'POST'])
def handle_bundles():
    if request.method == 'GET':
        return jsonify(db.get("bundles", []))
    if request.method == 'POST':
        data = request.json
        new_bundle = {
            "id": str(uuid.uuid4()),
            "name": data.get('name'),
            "description": data.get('description'),
            "product_ids": data.get('product_ids', []),
            "discount_percentage": data.get('discount_percentage', 0)
        }
        db["bundles"].append(new_bundle)
        save_data(db)
        return jsonify(new_bundle), 201

@app.route("/api/bundles/<bundle_id>", methods=['PUT', 'DELETE'])
def handle_specific_bundle(bundle_id):
    bundle = next((b for b in db.get("bundles", []) if b.get('id') == bundle_id), None)
    if not bundle:
        return jsonify({"message": "Колекцію не знайдено"}), 404
    if request.method == 'PUT':
        data = request.json
        bundle.update(data)
        save_data(db)
        return jsonify(bundle)
    if request.method == 'DELETE':
        db["bundles"] = [b for b in db["bundles"] if b.get('id') != bundle_id]
        save_data(db)
        return jsonify({"message": "Колекцію видалено"})

# --- Відгуки ---
@app.route("/api/reviews", methods=['GET', 'POST'])
def handle_reviews():
    if request.method == 'GET':
        return jsonify([r for r in db.get('reviews', []) if r.get('approved', False)])
    if request.method == 'POST':
        data = request.json
        review_id = str(uuid.uuid4())
        rating = data.get('rating')
        approved = rating is not None and rating >= 3 # Змінено на >=3 для автоматичного схвалення
        new_review = {
            "id": review_id,
            "product_id": data.get('product_id'),
            "user_id": data.get('user_id'),
            "username": data.get('username'),
            "rating": rating,
            "comment": data.get('comment'),
            "date": datetime.datetime.now().isoformat(),
            "approved": approved
        }
        db["reviews"].append(new_review)
        save_data(db)
        
        # Сповіщення адміністратору
        admin_message = ""
        if not approved:
            admin_message = (f"<b>❗️ Новий відгук на модерацію!</b>\n\n"
                           f"<b>Товар:</b> {data.get('product_name', 'N/A')}\n"
                           f"<b>Рейтинг:</b> {'⭐' * rating}\n"
                           f"<b>Відгук:</b> {data.get('comment', 'N/A')}\n\n"
                           f"<i>Перегляньте в адмін-панелі.</i>")
        elif rating <= 2: # Сповіщення про низьку оцінку, навіть якщо схвалено
             admin_message = (f"<b>📉 Отримано негативний відгук!</b>\n\n"
                           f"<b>Товар:</b> {data.get('product_name', 'N/A')}\n"
                           f"<b>Рейтинг:</b> {'⭐' * rating}\n"
                           f"<b>Відгук:</b> {data.get('comment', 'N/A')}")

        if admin_message:
            send_admin_notification(admin_message)

        return jsonify({"message": "Відгук успішно додано!", "reviewId": review_id, "approved": approved}), 201

@app.route("/api/admin/reviews", methods=['GET'])
def get_all_reviews_admin():
    reviews_list = db.get('reviews', [])
    for review in reviews_list:
        product = get_product_by_id(review.get('product_id'))
        review['product_name'] = product['name'] if product else "Видалений товар"
        user = clients_db.get(str(review.get('user_id')))
        review['user_name'] = user.get('name', 'Анонім') if user else 'Анонім'
    return jsonify(reviews_list)

@app.route("/api/admin/reviews/<review_id>", methods=['PUT', 'DELETE'])
def handle_specific_review_admin(review_id):
    review = next((r for r in db['reviews'] if r['id'] == review_id), None)
    if not review:
        return jsonify({"message": "Відгук не знайдено"}), 404
    if request.method == 'PUT':
        data = request.json
        review['approved'] = data.get('approved', review['approved'])
        save_data(db)
        return jsonify(review)
    if request.method == 'DELETE':
        db['reviews'] = [r for r in db['reviews'] if r['id'] != review_id]
        save_data(db)
        return jsonify({"message": "Відгук видалено"})

# --- Замовлення ---
@app.route("/api/orders", methods=['GET'])
def get_orders():
    orders = db.get("orders", [])
    for order in orders:
        user_id = order.get('telegram_id')
        user_info = clients_db.get(str(user_id))
        order['user_name'] = user_info.get('name', 'N/A') if user_info else 'N/A'
        order['user_id'] = user_id
    return jsonify(orders)

@app.route("/api/orders/<order_id>", methods=['PUT', 'DELETE'])
def handle_specific_order(order_id):
    order = next((o for o in db["orders"] if o.get('orderId') == order_id or o.get('id') == order_id), None)
    if not order:
        return jsonify({"message": "Замовлення не знайдено"}), 404
    if request.method == 'PUT':
        updated_data = request.json
        order['status'] = updated_data.get('status', order['status'])
        save_data(db)
        return jsonify(order)
    if request.method == 'DELETE':
        db["orders"] = [o for o in db["orders"] if o.get('orderId', o.get('id')) != order_id]
        save_data(db)
        return jsonify({"message": "Замовлення видалено"})

# --- Новини, Розсилка та інші API з оригінального файлу ---
@app.route("/api/news", methods=['GET', 'POST'])
def handle_news():
    if request.method == 'GET':
        news_list = db.get('news', [])
        sorted_news = sorted(news_list, key=lambda x: x.get('created_at', '1970-01-01'), reverse=True)
        return jsonify(sorted_news)
    if request.method == 'POST':
        data = request.json
        new_item = {
            "id": str(uuid.uuid4()),
            "text": data.get('text'),
            "created_at": datetime.datetime.now().isoformat(),
            "photo_id": data.get("photo_id"),
            "document_id": data.get("document_id")
        }
        db['news'].append(new_item)
        save_data(db)
        return jsonify(new_item), 201

@app.route("/api/news/<news_id>", methods=['GET', 'PUT', 'DELETE'])
def handle_specific_news(news_id):
    news_item = next((n for n in db['news'] if n['id'] == news_id), None)
    if not news_item:
        return jsonify({"message": "Новину не знайдено"}), 404
    if request.method == 'GET':
        return jsonify(news_item)
    if request.method == 'PUT':
        data = request.json
        news_item['text'] = data.get('text', news_item['text'])
        news_item['photo_id'] = data.get('photo_id', news_item.get('photo_id'))
        news_item['document_id'] = data.get('document_id', news_item.get('document_id'))
        save_data(db)
        return jsonify(news_item)
    if request.method == 'DELETE':
        db['news'] = [n for n in db['news'] if n['id'] != news_id]
        save_data(db)
        return jsonify({"message": "Новину видалено"})

@app.route("/api/admin/broadcast", methods=['POST'])
def handle_broadcast():
    data = request.json
    message = data.get('message')
    photo_id = data.get('photo_id')
    document_id = data.get('document_id')
    if not message and not photo_id and not document_id:
        return jsonify({"message": "Повідомлення або файл не можуть бути порожніми"}), 400
    broadcast_thread = Thread(target=send_broadcast_message, args=(message, TELEGRAM_CHAT_ID, photo_id, document_id))
    broadcast_thread.start()
    return jsonify({"message": "Розсилку розпочато..."})
    
# --- Інші API ---
@app.route("/api/shop-info", methods=['GET', 'PUT'])
def handle_shop_info():
    if request.method == 'GET':
        return jsonify(db.get("shop_info", {"name": "Shop", "description": ""}))
    if request.method == 'PUT':
        db["shop_info"] = request.json
        save_data(db)
        return jsonify(db["shop_info"])

@app.route("/api/regions", methods=['GET'])
def get_regions():
    return jsonify(REGIONS)

@app.route("/api/chatbot-knowledge", methods=['GET', 'POST'])
def handle_chatbot_knowledge():
    global chatbot_knowledge
    if request.method == 'GET':
        return jsonify(chatbot_knowledge)
    if request.method == 'POST':
        data = request.json
        if not data.get('keywords') or not data.get('response'):
            return jsonify({"message": "Ключові слова та відповідь обов'язкові"}), 400
        new_entry = {"id": str(uuid.uuid4()), **data}
        chatbot_knowledge.append(new_entry)
        save_chatbot_knowledge(chatbot_knowledge)
        return jsonify(new_entry), 201

@app.route("/api/chatbot-knowledge/<knowledge_id>", methods=['DELETE'])
def delete_chatbot_knowledge(knowledge_id):
    global chatbot_knowledge
    chatbot_knowledge = [item for item in chatbot_knowledge if item.get('id') != knowledge_id]
    save_chatbot_knowledge(chatbot_knowledge)
    return jsonify({"message": "Запис видалено"})
    
# --- МАРКЕТИНГ: Знижки, Промокоди, Бонуси ---
@app.route("/api/discounts", methods=['GET', 'POST'])
def handle_discounts():
    if request.method == 'GET':
        return jsonify(db.get('discounts', []))
    if request.method == 'POST':
        new_discount = request.json
        new_discount['id'] = str(uuid.uuid4())
        db['discounts'].append(new_discount)
        save_data(db)
        # Запускаємо сповіщення для користувачів
        thread = Thread(target=notify_users_about_discount, args=(new_discount,))
        thread.start()
        return jsonify(new_discount), 201

@app.route("/api/discounts/<discount_id>", methods=['DELETE'])
def delete_discount(discount_id):
    db['discounts'] = [d for d in db['discounts'] if d.get('id') != discount_id]
    save_data(db)
    return jsonify({"message": "Акцію видалено"})

@app.route("/api/promocodes", methods=['GET', 'POST'])
def handle_promocodes():
    if request.method == 'GET':
        return jsonify(db.get('promocodes', []))
    if request.method == 'POST':
        data = request.json
        new_code = {
            "id": str(uuid.uuid4()),
            "code": data.get('code').upper(),
            "discount_percentage": data.get('discount_percentage'),
            "uses_left": data.get('total_uses')
        }
        db['promocodes'].append(new_code)
        save_data(db)
        return jsonify(new_code), 201

@app.route("/api/promocodes/<code>", methods=['DELETE'])
def delete_promocode(code):
    initial_len = len(db.get('promocodes', []))
    db['promocodes'] = [p for p in db.get('promocodes', []) if p.get('code', '').upper() != code.upper()]
    if len(db['promocodes']) < initial_len:
        save_data(db)
        return jsonify({"message": "Промокод видалено"})
    return jsonify({"message": "Промокод не знайдено"}), 404

@app.route("/api/admin/bonus-settings", methods=['GET', 'PUT'])
def handle_bonus_settings():
    if request.method == 'GET':
        return jsonify(db.get('bonus_settings', {}))
    if request.method == 'PUT':
        data = request.json
        db['bonus_settings']['referral_bonus'] = data.get('referral_bonus')
        db['bonus_settings']['purchase_bonus_percentage'] = data.get('purchase_bonus_percentage')
        save_data(db)
        return jsonify(db['bonus_settings'])

# --- НОВІ API ДЛЯ МАРКЕТИНГУ ---
@app.route("/api/admin/loyalty-levels", methods=['GET', 'PUT'])
def handle_loyalty_levels():
    if request.method == 'GET':
        return jsonify(db.get('loyalty_levels', []))
    if request.method == 'PUT':
        db['loyalty_levels'] = request.json
        save_data(db)
        log_action("Loyalty Levels Updated", "Admin updated the loyalty level settings.")
        return jsonify(db['loyalty_levels'])

@app.route("/api/admin/deal-of-the-day", methods=['GET', 'POST'])
def handle_deal_of_the_day():
    if request.method == 'GET':
        return jsonify(db.get('deal_of_the_day', {}))
    if request.method == 'POST':
        data = request.json
        db['deal_of_the_day'] = {
            "product_id": data.get("product_id"),
            "discount_percentage": data.get("discount_percentage"),
            "end_date": data.get("end_date")
        }
        save_data(db)
        log_action("Deal of the Day Set", f"Product {data.get('product_id')} set as deal of the day.")
        return jsonify(db['deal_of_the_day'])

@app.route("/api/admin/clients/<client_id>/generate-promocode", methods=['POST'])
def generate_personal_promocode(client_id):
    if client_id not in clients_db:
        return jsonify({"message": "Клієнта не знайдено"}), 404
    
    data = request.json
    discount = data.get('discount_percentage', 10)
    
    # Генеруємо унікальний код
    while True:
        code = f"P-{random.randint(1000, 9999)}"
        if not any(p['code'] == code for p in db.get('promocodes', [])):
            break
            
    new_code = {
        "id": str(uuid.uuid4()),
        "code": code,
        "discount_percentage": discount,
        "uses_left": 1,
        "user_id": client_id # Прив'язка до конкретного користувача
    }
    db['promocodes'].append(new_code)
    save_data(db)
    log_action("Personal Promocode Generated", f"Code {code} for client {client_id}.")
    
    # Відправляємо код користувачу
    try:
        bot.send_message(
            client_id, 
            get_text("personal_promocode_notification", client_id).format(
                discount=discount, 
                code=code
            )
        )
    except Exception as e:
        logging.error(f"Не вдалося відправити персональний промокод клієнту {client_id}: {e}")

    return jsonify(new_code), 201
# --- КІНЕЦЬ НОВИХ API ---

# --- ФІНАНСИ ---
@app.route("/api/finances/transactions", methods=['GET'])
def get_transactions():
    completed_orders = [o for o in db.get('orders', []) if o.get('status') == 'Виконано']
    transactions = []
    for order in completed_orders:
        transactions.append({
            "date": order.get('date'),
            "order_id": order.get('orderId', 'N/A'),
            "amount": order.get('totalPrice', 0)
        })
    transactions.sort(key=lambda x: x.get('date', ''), reverse=True)
    return jsonify(transactions)

@app.route("/api/finances/payment-methods", methods=['GET'])
def get_payment_methods():
    methods = [{"id": key, **value} for key, value in payment_details.items()]
    return jsonify(methods)

@app.route("/api/finances/payment-methods", methods=['POST'])
def add_payment_method():
    global payment_details
    data = request.json
    method_id = data.get('account_name', '').lower().replace(' ', '_') + f"_{random.randint(100, 999)}"
    if method_id in payment_details:
        return jsonify({"message": "Спосіб оплати з таким ID вже існує"}), 409
    
    payment_details[method_id] = {
        "account_name": data.get("account_name"),
        "account_number": data.get("account_number"),
        "payment_link": data.get("payment_link"),
        "instructions": data.get("instructions")
    }
    save_payment_details(payment_details)
    log_action("Payment Method Added", f"Method '{data.get('account_name')}' was added.")
    return jsonify({"id": method_id, **payment_details[method_id]}), 201

@app.route("/api/finances/payment-methods/<method_id>", methods=['PUT'])
def update_payment_method(method_id):
    global payment_details
    if method_id not in payment_details:
        return jsonify({"message": "Спосіб оплати не знайдено"}), 404
    
    data = request.json
    payment_details[method_id] = {
        "account_name": data.get("account_name"),
        "account_number": data.get("account_number"),
        "payment_link": data.get("payment_link"),
        "instructions": data.get("instructions")
    }
    save_payment_details(payment_details)
    log_action("Payment Method Updated", f"Method '{data.get('account_name')}' ({method_id}) was updated.")
    return jsonify({"id": method_id, **payment_details[method_id]})

@app.route("/api/finances/payment-methods/<method_id>", methods=['DELETE'])
def delete_payment_method(method_id):
    global payment_details
    if method_id in payment_details:
        deleted_name = payment_details[method_id].get('account_name', method_id)
        del payment_details[method_id]
        save_payment_details(payment_details)
        log_action("Payment Method Deleted", f"Method '{deleted_name}' ({method_id}) was deleted.")
        return jsonify({"message": "Спосіб оплати видалено"})
    return jsonify({"message": "Спосіб оплати не знайдено"}), 404

# --- Користувачі панелі ---
@app.route("/api/users", methods=['GET', 'POST'])
def handle_users():
    global panel_users
    if request.method == 'GET':
        return jsonify(panel_users)
    if request.method == 'POST':
        data = request.json
        if not data.get('login') or not data.get('password'):
            return jsonify({"message": "Логін та пароль обов'язкові"}), 400
        new_user = {
            "id": str(uuid.uuid4()),
            "login": data['login'],
            "password_hash": hashlib.sha256(data['password'].encode()).hexdigest(),
            "role": data.get('role', 'manager'),
            "created_at": datetime.datetime.now().isoformat()
        }
        panel_users.append(new_user)
        save_json_file(USERS_FILE, panel_users)
        log_action("User Created", f"Panel user '{new_user['login']}' created with role '{new_user['role']}'.")
        return jsonify(new_user), 201

@app.route("/api/users/<user_id>", methods=['DELETE'])
def delete_user(user_id):
    global panel_users
    user_to_delete = next((u for u in panel_users if u['id'] == user_id), None)
    if not user_to_delete:
        return jsonify({"message": "Користувача не знайдено"}), 404
    panel_users = [u for u in panel_users if u['id'] != user_id]
    save_json_file(USERS_FILE, panel_users)
    log_action("User Deleted", f"Panel user '{user_to_delete['login']}' deleted.")
    return jsonify({"message": "Користувача видалено"})

# --- Налаштування (Резервне копіювання та Логи) ---
@app.route("/api/settings/backup", methods=['POST'])
def create_backup():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = os.path.join(BACKUP_DIR, f"backup_{timestamp}.zip")
    files_to_backup = [
        DATA_FILE, CLIENTS_FILE, CHATBOT_KNOWLEDGE_FILE, 
        PAYMENTS_FILE, SUPPORT_TICKETS_FILE, USERS_FILE, SYSTEM_LOG_FILE
    ]
    try:
        with zipfile.ZipFile(backup_filename, 'w') as zipf:
            for file in files_to_backup:
                if os.path.exists(file):
                    zipf.write(file, os.path.basename(file))
        log_action("Backup Created", f"Backup file '{os.path.basename(backup_filename)}' created.")
        return jsonify({"message": "Резервну копію успішно створено!", "filename": os.path.basename(backup_filename)})
    except Exception as e:
        logging.error(f"Помилка створення резервної копії: {e}")
        return jsonify({"message": "Помилка створення резервної копії"}), 500

@app.route("/api/settings/backups", methods=['GET'])
def get_backups():
    if not os.path.exists(BACKUP_DIR):
        return jsonify([])
    files = sorted(os.listdir(BACKUP_DIR), reverse=True)
    return jsonify(files)

@app.route("/api/settings/backups/<filename>", methods=['GET'])
def download_backup(filename):
    filepath = os.path.join(BACKUP_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({"message": "Файл не знайдено"}), 404

@app.route("/api/settings/logs", methods=['GET'])
def get_system_logs():
    return jsonify(system_logs)

# -----------------
# File Manager API
# -----------------
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
ALLOWED_EXTENSIONS = ['.json', '.py', '.html', '.js', '.css', '.txt']

def is_safe_path(path):
    """Перевіряє, чи шлях є безпечним і знаходиться в межах кореневої директорії."""
    # Нормалізуємо шлях, щоб уникнути таких речей, як 'folder/../folder'
    path = os.path.normpath(path)
    # Створюємо абсолютний шлях від кореневої директорії проекту
    abs_path = os.path.abspath(os.path.join(ROOT_DIR, path))
    # Перевіряємо, чи отриманий шлях починається з шляху до кореневої директорії
    return abs_path.startswith(ROOT_DIR)

@app.route('/api/files', methods=['GET'])
def list_files():
    """Отримує список файлів та папок за вказаним шляхом."""
    req_path = request.args.get('path', '')
    if not is_safe_path(req_path):
        return jsonify({"message": "Доступ заборонено"}), 403

    abs_path = os.path.join(ROOT_DIR, req_path)
    if not os.path.exists(abs_path) or not os.path.isdir(abs_path):
        return jsonify({"message": "Шлях не знайдено"}), 404

    items = []
    try:
        for item in os.listdir(abs_path):
            item_path = os.path.join(abs_path, item)
            rel_path = os.path.join(req_path, item).replace("\\", "/") # Нормалізуємо для веб
            if os.path.isdir(item_path):
                items.append({"name": item, "type": "directory", "path": rel_path})
            else:
                items.append({"name": item, "type": "file", "path": rel_path})
    except OSError:
        return jsonify({"message": "Не вдалося прочитати директорію"}), 500
    
    # Сортуємо: спочатку папки, потім файли
    items.sort(key=lambda x: (x['type'] != 'directory', x['name'].lower()))
    return jsonify(items)

@app.route('/api/file-content', methods=['GET', 'POST'])
def handle_file_content():
    """Читає або записує вміст файлу."""
    if request.method == 'GET':
        file_path = request.args.get('path', '')
        if not is_safe_path(file_path):
            return jsonify({"message": "Доступ заборонено"}), 403
        
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in ALLOWED_EXTENSIONS:
            return jsonify({"message": f"Редагування файлів типу '{ext}' заборонено"}), 403

        abs_path = os.path.join(ROOT_DIR, file_path)
        if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
            return jsonify({"message": "Файл не знайдено"}), 404
        
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({"path": file_path, "content": content})
        except Exception as e:
            return jsonify({"message": f"Помилка читання файлу: {e}"}), 500

    if request.method == 'POST':
        data = request.json
        file_path = data.get('path')
        content = data.get('content')

        if not file_path or not is_safe_path(file_path):
            return jsonify({"message": "Доступ заборонено або невірний шлях"}), 403
            
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in ALLOWED_EXTENSIONS:
            return jsonify({"message": f"Збереження файлів типу '{ext}' заборонено"}), 403

        abs_path = os.path.join(ROOT_DIR, file_path)
        try:
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
            log_action("File Edited", f"File '{file_path}' was edited.")
            return jsonify({"message": f"Файл '{file_path}' успішно збережено"})
        except Exception as e:
            return jsonify({"message": f"Помилка збереження файлу: {e}"}), 500

@app.route('/api/files', methods=['POST', 'DELETE'])
def manage_files():
    """Створює або видаляє файли/папки."""
    data = request.json
    path = data.get('path')

    if not path or not is_safe_path(path):
        return jsonify({"message": "Доступ заборонено або невірний шлях"}), 403
    
    abs_path = os.path.join(ROOT_DIR, path)

    if request.method == 'POST': # Створення
        item_type = data.get('type', 'file')
        if os.path.exists(abs_path):
            return jsonify({"message": "Файл або папка з таким іменем вже існує"}), 409
        
        try:
            if item_type == 'directory':
                os.makedirs(abs_path)
                log_action("Directory Created", f"Directory '{path}' created.")
                return jsonify({"message": f"Папку '{path}' створено"})
            else:
                _, ext = os.path.splitext(path)
                if ext.lower() not in ALLOWED_EXTENSIONS:
                     return jsonify({"message": f"Створення файлів типу '{ext}' заборонено"}), 403
                with open(abs_path, 'w', encoding='utf-8') as f:
                    f.write('') # Створюємо порожній файл
                log_action("File Created", f"File '{path}' created.")
                return jsonify({"message": f"Файл '{path}' створено"})
        except Exception as e:
            return jsonify({"message": f"Помилка створення: {e}"}), 500

    if request.method == 'DELETE':
        if not os.path.exists(abs_path):
            return jsonify({"message": "Файл або папку не знайдено"}), 404
        
        try:
            if os.path.isdir(abs_path):
                shutil.rmtree(abs_path) # Видаляє папку та весь її вміст
                log_action("Directory Deleted", f"Directory '{path}' deleted.")
                return jsonify({"message": f"Папку '{path}' видалено"})
            else:
                os.remove(abs_path)
                log_action("File Deleted", f"File '{path}' deleted.")
                return jsonify({"message": f"Файл '{path}' видалено"})
        except Exception as e:
            return jsonify({"message": f"Помилка видалення: {e}"}), 500

# -----------------
# Telegram Bot Handlers
# -----------------
STATUS_MAP = {"Нове": "new", "Обробляється": "proc", "Відправлено": "sent", "Виконано": "done"}
REVERSE_STATUS_MAP = {v: k for k, v in STATUS_MAP.items()}

def is_banned(user_id):
    user = clients_db.get(str(user_id))
    return user and user.get('is_banned', False)

def check_ban(func):
    def wrapper(message_or_call):
        user_id = message_or_call.from_user.id
        if is_banned(user_id):
            try:
                bot.send_message(user_id, get_text("user_banned", user_id))
            except:
                bot.answer_callback_query(message_or_call.id, get_text("user_banned", user_id), show_alert=True)
            return
        return func(message_or_call)
    return wrapper

def get_categories_markup(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    categories = db.get("categories", [])
    if categories:
        buttons = [types.InlineKeyboardButton(cat['name'], callback_data=f"cat_{cat['id']}_0_default") for cat in categories]
        markup.add(*buttons)
    markup.add(types.InlineKeyboardButton(get_text("all_products", user_id), callback_data="cat_all_0_default"))
    return markup

def get_products_markup(user_id, category_id='all', page=0, sort_by='default'):
    items_per_page = 5
    discounts = db.get('discounts', [])
    if category_id != 'all':
        products_to_show = [p for p in db.get('products', []) if p.get('category_id') == category_id]
        category = next((c for c in db.get('categories', []) if c.get('id') == category_id), None)
        category_name = category['name'] if category else "..."
        text = get_text("category_products", user_id).format(category_name=category_name, page=page + 1)
    else:
        products_to_show = db.get('products', [])
        text = get_text("all_products_paginated", user_id).format(page=page + 1)
    
    products_with_discounts = apply_discounts(products_to_show, discounts)

    # Сортування
    if sort_by == 'price_asc':
        products_with_discounts.sort(key=lambda p: p['discounted_price'])
    elif sort_by == 'price_desc':
        products_with_discounts.sort(key=lambda p: p['discounted_price'], reverse=True)

    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Кнопки сортування
    sort_buttons = [
        types.InlineKeyboardButton("▲ Ціна", callback_data=f"cat_{category_id}_{page}_price_asc"),
        types.InlineKeyboardButton("▼ Ціна", callback_data=f"cat_{category_id}_{page}_price_desc")
    ]
    markup.add(*sort_buttons)

    if not products_with_discounts:
        text += get_text("no_products_in_category", user_id)
        markup.add(types.InlineKeyboardButton(get_text("btn_to_categories", user_id), callback_data="back_to_categories"))
        return text, markup

    start = page * items_per_page
    end = start + items_per_page
    products_on_page = products_with_discounts[start:end]
    
    for product in products_on_page:
        if product['discounted_price'] < product['price']:
            button_text = f"{product['name']} - {product['discounted_price']} грн (<s>{product['price']}</s>)"
        else:
            button_text = f"{product['name']} - {product['price']} грн"
        markup.add(types.InlineKeyboardButton(button_text, callback_data=f"show_product_{product['id']}"))
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton(get_text("btn_prev_page", user_id), callback_data=f"cat_{category_id}_{page - 1}_{sort_by}"))
    if end < len(products_with_discounts):
        nav_buttons.append(types.InlineKeyboardButton(get_text("btn_next_page", user_id), callback_data=f"cat_{category_id}_{page + 1}_{sort_by}"))
    if nav_buttons:
        markup.row(*nav_buttons)
    
    markup.add(types.InlineKeyboardButton(get_text("btn_to_categories", user_id), callback_data="back_to_categories"))
    return text, markup

@bot.callback_query_handler(func=lambda call: call.data.startswith('cat_') or call.data == 'back_to_categories')
@check_ban
def handle_catalog_navigation(call):
    try:
        user_id = call.from_user.id
        if call.data == 'back_to_categories':
            text = get_text("catalog_title", user_id)
            markup = get_categories_markup(user_id)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=markup)
            bot.answer_callback_query(call.id)
            return
        
        parts = call.data.split('_')
        category_id = parts[1]
        page = int(parts[2])
        sort_by = parts[3] if len(parts) > 3 else 'default'

        text, markup = get_products_markup(user_id, category_id, page, sort_by)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=markup)
        bot.answer_callback_query(call.id)
    except Exception as e:
        logging.error(f"Помилка в навігації по каталогу: {e}")
        bot.answer_callback_query(call.id, "Сталася помилка, спробуйте ще раз.", show_alert=True)

def show_main_menu(chat_id):
    user_id = chat_id
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        types.KeyboardButton(get_text("btn_catalog", user_id)), 
        types.KeyboardButton(get_text("btn_cart", user_id)),
        types.KeyboardButton(get_text("btn_deal_of_the_day", user_id)),
        types.KeyboardButton(get_text("btn_purchases", user_id)),
        types.KeyboardButton(get_text("btn_profile", user_id)), 
        types.KeyboardButton(get_text("btn_reviews", user_id)),
        types.KeyboardButton(get_text("btn_promotions", user_id)), 
        types.KeyboardButton(get_text("btn_support", user_id)),
        types.KeyboardButton(get_text("btn_about", user_id)),
        types.KeyboardButton(get_text("btn_settings", user_id)),
        types.KeyboardButton(get_text("btn_wishlist", user_id)),
        types.KeyboardButton(get_text("btn_bundles", user_id)),
        types.KeyboardButton(get_text("btn_news", user_id)),
    ]
    markup.add(*buttons)
    bot.send_message(chat_id, get_text("main_menu", user_id), reply_markup=markup)

@bot.message_handler(commands=['start', 'help'])
@check_ban
def start_command(message):
    user_id = str(message.from_user.id)
    args = message.text.split()
    referrer_id = None
    if len(args) > 1:
        referrer_id = args[1]
    if user_id in clients_db:
        bot.send_message(message.chat.id, get_text("welcome_back", user_id).format(name=clients_db[user_id]['name']))
        show_main_menu(message.chat.id)
    else:
        ORDER_STATE[message.from_user.id] = {'step': 'register_name'}
        if referrer_id and referrer_id in clients_db:
            ORDER_STATE[message.from_user.id]['referred_by'] = referrer_id
        bot.send_message(message.chat.id, get_text("welcome", user_id))

@bot.callback_query_handler(func=lambda call: call.data.startswith('show_product_'))
@check_ban
def handle_product_details(call):
    try:
        user_id = str(call.from_user.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        product_id = call.data.split('show_product_')[1]
        product = get_product_by_id(product_id)
        if product:
            discounts = db.get('discounts', [])
            discounted_product = apply_discounts([product], discounts)[0]
            markup = types.InlineKeyboardMarkup(row_width=2)
            wishlist = clients_db.get(user_id, {}).get('wishlist', [])
            
            if product_id in wishlist:
                wishlist_btn = types.InlineKeyboardButton(get_text("btn_remove_from_wishlist", user_id), callback_data=f"toggle_wishlist_{product_id}")
            else:
                wishlist_btn = types.InlineKeyboardButton(get_text("btn_add_to_wishlist", user_id), callback_data=f"toggle_wishlist_{product_id}")
            
            cart_btn = types.InlineKeyboardButton(get_text("btn_add_to_cart", user_id), callback_data=f"add_to_cart_{product['id']}")
            buy_now_btn = types.InlineKeyboardButton(get_text("btn_buy_now", user_id), callback_data=f"buy_now_{product['id']}")
            markup.add(wishlist_btn, cart_btn)
            markup.row(buy_now_btn)
            
            clean_description = strip_html_tags(product.get('description', ''))
            price_text = ""
            if discounted_product['discounted_price'] < discounted_product['price']:
                price_text = f"Ціна: <b>{discounted_product['discounted_price']} грн</b> <s>{discounted_product['price']} грн</s>"
            else:
                price_text = f"Ціна: {product['price']} грн"
            message_text = f"<b>{product['name']}</b>\n\n{price_text}\n\n{clean_description}"
            try:
                bot.send_photo(call.message.chat.id, product['image'], caption=message_text, reply_markup=markup, parse_mode="HTML")
            except telebot.apihelper.ApiTelegramException as e:
                logging.warning(f"Помилка відправки фото для товару {product['name']}: {e}. Відправляю текстове повідомлення.")
                bot.send_message(call.message.chat.id, message_text, reply_markup=markup, parse_mode="HTML")
            bot.answer_callback_query(call.id)
        else:
            bot.send_message(call.message.chat.id, "Товар не знайдено.")
            bot.answer_callback_query(call.id, text="Товар не знайдено.")
    except Exception as e:
        logging.error(f"Помилка в handle_product_details: {e}")
        bot.send_message(call.message.chat.id, "Виникла помилка під час завантаження деталей товару.")
        bot.answer_callback_query(call.id, text="Помилка")

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_now_'))
@check_ban
def handle_buy_now(call):
    try:
        user_id = str(call.from_user.id)
        if user_id not in clients_db:
            bot.answer_callback_query(call.id, "Будь ласка, спочатку зареєструйтесь, ввівши /start", show_alert=True)
            return

        product_id = call.data.split('buy_now_')[1]
        product = get_product_by_id(product_id)
        if not product:
            bot.answer_callback_query(call.id, "Товар не знайдено.", show_alert=True)
            return

        discounts = db.get('discounts', [])
        discounted_product = apply_discounts([product], discounts)[0]
        price_to_use = discounted_product['discounted_price']

        order_items = [{"product_id": product_id, "product_name": product['name'], "price": price_to_use, "quantity": 1}]
        total_price = price_to_use
        order_name = product['name']

        ORDER_STATE[call.from_user.id] = {
            'step': 'waiting_for_promocode',
            'order_details': {
                "items": order_items,
                "totalPrice": total_price,
                "is_bundle": False,
                "order_name": order_name
            }
        }
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Пропустити", callback_data="skip_promocode"))
        bot.send_message(call.from_user.id, "У вас є промокод? Якщо так, надішліть його. Якщо ні - натисніть 'Пропустити'.", reply_markup=markup)
        bot.answer_callback_query(call.id)
    except Exception as e:
        logging.error(f"Помилка в handle_buy_now: {e}")
        bot.send_message(call.from_user.id, "Виникла помилка при обробці покупки.")
        bot.answer_callback_query(call.id, text="Помилка")

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
@check_ban
def handle_buy_query(call):
    try:
        user_id = str(call.from_user.id)
        if user_id not in clients_db:
            bot.answer_callback_query(call.id, "Будь ласка, спочатку зареєструйтесь, ввівши /start", show_alert=True)
            return
        
        order_items = []
        total_price = 0
        order_name = ""
        is_bundle = False
        discounts = db.get('discounts', [])
        
        # Визначаємо, чи це покупка з кошика, чи окремого бандла
        if call.data == 'buy_cart':
            cart = clients_db.get(user_id, {}).get('cart', [])
            if not cart:
                bot.answer_callback_query(call.id, "Ваш кошик порожній.", show_alert=True)
                return
            
            product_counts = Counter(cart)
            order_name_parts = []
            for pid, count in product_counts.items():
                product = get_product_by_id(pid)
                if product:
                    discounted_product = apply_discounts([product], discounts)[0]
                    price_to_use = discounted_product['discounted_price']
                    order_items.append({"product_id": pid, "product_name": product['name'], "price": price_to_use, "quantity": count})
                    total_price += price_to_use * count
                    order_name_parts.append(f"{product['name']} x{count}")
            order_name = ", ".join(order_name_parts)

        else: # Логіка для покупки бандла
            parts = call.data.split('_')
            if len(parts) == 3 and parts[1] == 'bundle':
                item_id = parts[2]
                bundle = next((b for b in db.get('bundles', []) if b['id'] == item_id), None)
                if not bundle:
                    bot.answer_callback_query(call.id, "Колекцію не знайдено.", show_alert=True)
                    return
                is_bundle = True
                order_name = f"Колекція «{bundle['name']}»"
                total_price_before_bundle_discount = 0
                for pid in bundle['product_ids']:
                    product = get_product_by_id(pid)
                    if product:
                        discounted_product = apply_discounts([product], discounts)[0]
                        price_to_use = discounted_product['discounted_price']
                        order_items.append({"product_id": pid, "product_name": product['name'], "price": price_to_use, "quantity": 1})
                        total_price_before_bundle_discount += price_to_use
                if not order_items:
                    bot.answer_callback_query(call.id, "Товари з цієї колекції не знайдено.", show_alert=True)
                    return
                total_price = round(total_price_before_bundle_discount * (1 - bundle['discount_percentage'] / 100))
            else:
                logging.error(f"Неправильний формат callback-даних для покупки: {call.data}")
                bot.answer_callback_query(call.id, "Помилка: невірний запит на покупку.", show_alert=True)
                return

        ORDER_STATE[call.from_user.id] = {
            'step': 'waiting_for_promocode',
            'order_details': {
                "items": order_items,
                "totalPrice": total_price,
                "is_bundle": is_bundle,
                "order_name": order_name
            }
        }
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Пропустити", callback_data="skip_promocode"))
        bot.send_message(call.from_user.id, "У вас є промокод? Якщо так, надішліть його. Якщо ні - натисніть 'Пропустити'.", reply_markup=markup)
        bot.answer_callback_query(call.id)
    except Exception as e:
        logging.error(f"Помилка в handle_buy_query: {e}")
        bot.send_message(call.from_user.id, "Виникла помилка при обробці покупки.")
        bot.answer_callback_query(call.id, text="Помилка")

def ask_about_bonuses(user_id, order_details):
    """Запитує користувача, чи хоче він використати бонуси."""
    str_user_id = str(user_id)
    user_points = clients_db.get(str_user_id, {}).get('loyalty_points', 0)

    if user_points > 0 and order_details['totalPrice'] > 0:
        ORDER_STATE[user_id] = {
            'step': 'waiting_for_bonus_decision',
            'order_details': order_details
        }
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(get_text("btn_yes", user_id), callback_data="use_bonus_yes"),
            types.InlineKeyboardButton(get_text("btn_no", user_id), callback_data="use_bonus_no")
        )
        bot.send_message(user_id, get_text("ask_use_bonus", user_id).format(points=user_points), reply_markup=markup)
    else:
        # Якщо бонусів немає або сума 0, одразу переходимо до фіналізації
        finalize_order(user_id, order_details)

def finalize_order(user_id, order_details):
    """Створює замовлення та пропонує оплату."""
    client_info = clients_db[str(user_id)]
    order_id = str(uuid.uuid4())
    order = {
        "orderId": order_id, 
        "customer_name": f"{client_info.get('name', '')} {client_info.get('surname', '')}".strip(),
        "customer_phone": client_info.get('phone', 'Не вказано'), 
        "date": datetime.datetime.now().isoformat(),
        "status": "Очікує оплати", 
        "telegram_id": user_id,
        **order_details
    }
    db['orders'].append(order)
    save_data(db)

    # Сповіщення для адміна
    admin_message = (f"📦 <b>Нове замовлення №{order_id[:8]}</b>\n\n"
                     f"<b>Клієнт:</b> {order['customer_name']}\n"
                     f"<b>Товари:</b>\n{order['order_name']}\n"
                     f"<b>Сума:</b> {order['totalPrice']} грн")
    send_admin_notification(admin_message)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, details in payment_details.items():
        btn_text = f"Оплатити через {details['account_name']}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"pay_{key}_{order_id}"))
    
    bot.send_message(user_id, f"<b>Замовлення №{order_id[:8]}</b> ({order['order_name']}) успішно створено.\n"
                             f"Сума до сплати: <b>{order['totalPrice']} грн</b>.\n\n"
                             f"Оберіть спосіб оплати:", reply_markup=markup)
    # Очищуємо кошик після успішного оформлення
    clients_db[str(user_id)]['cart'] = []
    save_clients(clients_db)

    if user_id in ORDER_STATE:
        del ORDER_STATE[user_id]

@bot.callback_query_handler(func=lambda call: call.data.startswith('use_bonus_'))
@check_ban
def handle_bonus_decision(call):
    user_id = call.from_user.id
    str_user_id = str(user_id)
    state = ORDER_STATE.get(user_id)

    if not state or state.get('step') != 'waiting_for_bonus_decision':
        bot.answer_callback_query(call.id)
        return

    order_details = state['order_details']
    bot.delete_message(call.message.chat.id, call.message.message_id)

    if call.data == 'use_bonus_yes':
        user_points = clients_db.get(str_user_id, {}).get('loyalty_points', 0)
        price = order_details['totalPrice']
        
        points_to_use = min(user_points, price)
        
        order_details['totalPrice'] -= points_to_use
        clients_db[str_user_id]['loyalty_points'] -= points_to_use
        save_clients(clients_db)
        
        bot.send_message(user_id, get_text("bonus_applied", user_id).format(
            new_price=order_details['totalPrice'],
            remaining_points=clients_db[str_user_id]['loyalty_points']
        ))

    finalize_order(user_id, order_details)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == 'skip_promocode')
@check_ban
def handle_skip_promocode(call):
    user_id = call.from_user.id
    state = ORDER_STATE.get(user_id)
    if state and state.get('step') == 'waiting_for_promocode':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        ask_about_bonuses(user_id, state['order_details'])
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
@check_ban
def handle_payment_query(call):
    try:
        _, data = call.data.split('_', 1)
        payment_type, order_id = data.rsplit('_', 1)
        details = payment_details.get(payment_type)
        order = next((o for o in db['orders'] if o['orderId'] == order_id), None)
        if details and order:
            order['status'] = f"Очікує підтвердження оплати ({details['account_name']})"
            save_data(db)
            message_text = f"<b>{details['account_name']}</b>\n\n" \
                           f"Сума до оплати: {order['totalPrice']} грн.\n\n"
            if 'payment_link' in details and details['payment_link']:
                message_text += f"Посилання для оплати: {details['payment_link']}\n\n"
            elif 'account_number' in details and details['account_number']:
                message_text += f"Реквізити: <code>{details['account_number']}</code>\n\n"
            message_text += f"<i>{details['instructions']}</i>"
            bot.send_message(call.from_user.id, message_text, parse_mode="HTML")
            bot.send_message(call.from_user.id, "Будь ласка, надішліть фото або скріншот чека про оплату.")
            ORDER_STATE[call.from_user.id] = {'order_id': order_id, 'step': 'waiting_for_receipt'}
            bot.answer_callback_query(call.id)
        else:
            bot.answer_callback_query(call.id, "Помилка: Не вдалося знайти деталі платежу або замовлення.")
    except Exception as e:
        logging.error(f"Помилка в handle_payment_query: {e}")
        bot.answer_callback_query(call.id, "Виникла помилка під час обробки запиту.")

@bot.message_handler(content_types=['photo', 'document'], func=lambda message: message.from_user.id in ORDER_STATE and ORDER_STATE[message.from_user.id].get('step') == 'waiting_for_receipt')
@check_ban
def handle_receipt(message):
    user_id = message.from_user.id
    order_id = ORDER_STATE[user_id]['order_id']
    order = next((o for o in db['orders'] if o['orderId'] == order_id), None)
    if order:
        markup = types.InlineKeyboardMarkup()
        confirm_button = types.InlineKeyboardButton("✅ Підтвердити оплату", callback_data=f"confirm_payment_{order_id}")
        decline_button = types.InlineKeyboardButton("❌ Відхилити", callback_data=f"decline_payment_{order_id}")
        markup.add(confirm_button, decline_button)
        caption = (
            f"<b>НОВИЙ ЧЕК</b>\n\n"
            f"Замовлення №{order_id[:8]}\n"
            f"Клієнт: {order['customer_name']}\n"
            f"Телефон: {order['customer_phone']}\n"
            f"Сума: {order['totalPrice']} грн\n"
            f"Товар: {order['order_name']}"
        )
        if message.content_type == 'photo':
            bot.send_photo(TELEGRAM_CHAT_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup, parse_mode="HTML")
        elif message.content_type == 'document':
            bot.send_document(TELEGRAM_CHAT_ID, message.document.file_id, caption=caption, reply_markup=markup, parse_mode="HTML")
        bot.send_message(user_id, "Дякую! Ваш чек відправлено на перевірку. Очікуйте підтвердження.")
        del ORDER_STATE[user_id]
    else:
        bot.send_message(user_id, "Вибачте, сталася помилка. Спробуйте створити замовлення знову.")

# --- Оновлена функція для обробки бонусів та рангів ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_payment_') or call.data.startswith('decline_payment_'))
def handle_admin_payment_confirmation(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "У вас немає прав адміністратора.")
        return
    try:
        action, _, order_id = call.data.partition('_payment_')
        order = next((o for o in db['orders'] if o['orderId'] == order_id), None)
        if not order:
            bot.answer_callback_query(call.id, "Замовлення не знайдено.")
            return
        user_telegram_id = order.get('telegram_id')
        if not user_telegram_id:
            bot.answer_callback_query(call.id, "Помилка: не знайдено Telegram ID клієнта.")
            return
        if action == 'decline':
            order['status'] = "Відхилено"
            save_data(db)
            bot.send_message(user_telegram_id, f"❌ Ваше замовлення №{order_id[:8]} було відхилено.\nЗв'яжіться з адміністратором для вирішення проблеми.")
            bot.edit_message_caption(call.message.caption + "\n\n❌ Оплату відхилено.", chat_id=call.message.chat.id, message_id=call.message.message_id)
            bot.answer_callback_query(call.id, "Оплату відхилено.")
            return
        
        final_message = ""
        if order.get('is_bundle'):
            final_message = get_text("bundle_purchase_success", user_telegram_id).format(name=order['order_name']) + "\n"
        else:
            final_message = f"✅ Ваше замовлення №{order_id[:8]} підтверджено!\n"
        
        for item in order['items']:
            product = get_product_by_id(item.get('product_id'))
            if not product:
                continue
            content = product.get('content')
            if not content:
                bot.answer_callback_query(call.id, f"Помилка: вміст для товару '{product['name']}' не задано!", show_alert=True)
                return
            final_message += f"\n<b>{product['name']}</b>:\n<code>{content}</code>\n"
        
        bot.send_message(user_telegram_id, final_message)
        order['status'] = "Виконано"
        
        client_id = str(user_telegram_id)
        if client_id in clients_db:
            # Оновлюємо LTV
            clients_db[client_id]['ltv'] = clients_db[client_id].get('ltv', 0) + order['totalPrice']
            
            # Визначаємо поточний та новий ранг
            current_rank = get_user_rank(clients_db[client_id].get('ltv', 0) - order['totalPrice'])
            new_rank = get_user_rank(clients_db[client_id]['ltv'])
            
            # Нараховуємо бонуси згідно з новим рангом
            bonus_percent = new_rank['bonus_percent']
            bonus = round(order['totalPrice'] * (bonus_percent / 100))
            if bonus > 0:
                clients_db[client_id]['loyalty_points'] = clients_db[client_id].get('loyalty_points', 0) + bonus
                bot.send_message(user_telegram_id, f"🎉 Вам нараховано <b>{bonus} Delon-гіків</b>! Перевірити баланс можна в профілі.")
            
            # Сповіщаємо про підвищення рангу
            if new_rank['name'] != current_rank['name']:
                clients_db[client_id]['rank'] = new_rank['name']
                bot.send_message(
                    user_telegram_id, 
                    get_text("rank_up_notification", user_telegram_id).format(
                        rank_name=new_rank['name'], 
                        bonus_percent=new_rank['bonus_percent']
                    )
                )
            
            save_clients(clients_db)

        save_data(db)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✍️ Залишити відгук", callback_data=f"leave_review_{order_id}"))
        bot.send_message(user_telegram_id, "Дякуємо за покупку! Будемо вдячні за ваш відгук.", reply_markup=markup)
        bot.edit_message_caption(call.message.caption + "\n\n✅ Оплату підтверджено. Товар(и) видано.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.answer_callback_query(call.id, "Товар(и) успішно видано.")
    except Exception as e:
        logging.error(f"Помилка в handle_admin_payment_confirmation: {e}")
        bot.answer_callback_query(call.id, "Виникла помилка.")

# --- Нова функція для визначення рангу ---
def get_user_rank(ltv):
    """Визначає ранг користувача на основі його LTV."""
    levels = sorted(db.get('loyalty_levels', []), key=lambda x: x['threshold'], reverse=True)
    for level in levels:
        if ltv >= level['threshold']:
            return level
    return {"name": "Newbie", "bonus_percent": 0} # Повертаємо дефолтний ранг, якщо щось пішло не так

@bot.callback_query_handler(func=lambda call: call.data.startswith('leave_review_'))
@check_ban
def handle_leave_review_query(call):
    try:
        order_id = call.data.split('leave_review_')[1]
        order = next((o for o in db.get('orders', []) if o.get('orderId') == order_id), None)
        if not order:
            bot.answer_callback_query(call.id, "Замовлення не знайдено.", show_alert=True)
            return
        ORDER_STATE[call.from_user.id] = {'step': 'waiting_for_rating', 'order_id': order_id}
        bot.send_message(call.from_user.id, "Будь ласка, оцініть вашу покупку від 1 до 5 ⭐")
        bot.answer_callback_query(call.id)
    except Exception as e:
        logging.error(f"Помилка в handle_leave_review_query: {e}")
        bot.answer_callback_query(call.id, "Сталася помилка.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('reget_product_'))
@check_ban
def handle_reget_product(call):
    try:
        order_id = call.data.split('reget_product_')[1]
        order = next((o for o in db.get('orders', []) if o.get('orderId') == order_id), None)
        if not order:
            bot.answer_callback_query(call.id, "Замовлення не знайдено.", show_alert=True)
            return
        
        final_message = f"Повторна видача товару(ів) із замовлення №{order_id[:8]}:\n"
        
        if not order.get('items'):
             bot.answer_callback_query(call.id, "У цьому замовленні немає товарів для повторної видачі.", show_alert=True)
             return

        for item in order['items']:
            product = get_product_by_id(item.get('product_id'))
            if not product:
                final_message += f"\n<b>{item.get('product_name', 'Невідомий товар')}</b>:\n<i>Товар більше не існує.</i>\n"
                continue

            content = product.get('content')
            if not content:
                final_message += f"\n<b>{product['name']}</b>:\n<i>Вміст товару не знайдено. Зверніться до підтримки.</i>\n"
            else:
                final_message += f"\n<b>{product['name']}</b>:\n<code>{content}</code>\n"

        bot.send_message(call.from_user.id, final_message)
        bot.answer_callback_query(call.id, "Товар(и) надіслано.")

    except Exception as e:
        logging.error(f"Помилка в handle_reget_product: {e}")
        bot.answer_callback_query(call.id, "Сталася помилка.", show_alert=True)

def handle_order_flow(message):
    user_id = message.from_user.id
    str_user_id = str(user_id)
    state = ORDER_STATE.get(user_id)
    if not state: return
    try:
        step = state.get('step')
        if step == 'register_name':
            state['name_surname'] = message.text
            state['step'] = 'register_phone'
            bot.send_message(user_id, get_text("register_phone", user_id))
        elif step == 'register_phone':
            name_parts = state['name_surname'].split()
            name = name_parts[0]
            surname = name_parts[1] if len(name_parts) > 1 else ""
            referrer_id = state.get('referred_by')
            clients_db[str_user_id] = {
                "name": name, "surname": surname, "phone": message.text, "loyalty_points": 0,
                "lang": "uk", "wishlist": [], "cart": [], "is_banned": False, "referral_code": str_user_id,
                "referred_by": referrer_id, "referrals_count": 0, "registration_date": datetime.datetime.now().isoformat(),
                "ltv": 0, "rank": "Bronze"
            }
            success_message = get_text("register_success", user_id).format(name=name)
            if referrer_id:
                try:
                    bonus = db.get('bonus_settings', {}).get('referral_bonus', 20)
                    clients_db[referrer_id]['loyalty_points'] = clients_db[referrer_id].get('loyalty_points', 0) + bonus
                    clients_db[referrer_id]['referrals_count'] = clients_db[referrer_id].get('referrals_count', 0) + 1
                    bot.send_message(referrer_id, f"🎉 Ваш друг {name} зареєструвався! Вам нараховано {bonus} Delon-гіків.")
                    success_message += get_text("referral_welcome", user_id)
                except Exception as e:
                    logging.error(f"Не вдалося нарахувати реферальний бонус для {referrer_id}: {e}")
            save_clients(clients_db)
            bot.send_message(user_id, success_message)
            show_main_menu(user_id)
            del ORDER_STATE[user_id]
        elif step == 'waiting_for_promocode':
            code = message.text.upper()
            promocode = next((p for p in db.get('promocodes', []) if p['code'] == code and p.get('uses_left', 1) > 0), None)
            
            # Перевірка персонального промокоду
            if promocode and promocode.get('user_id') and promocode.get('user_id') != str_user_id:
                promocode = None # Це не його промокод

            if promocode:
                discount = promocode['discount_percentage']
                state['order_details']['totalPrice'] = round(state['order_details']['totalPrice'] * (1 - discount / 100))
                if 'uses_left' in promocode:
                    promocode['uses_left'] -= 1
                    if promocode['uses_left'] == 0:
                        db['promocodes'] = [p for p in db['promocodes'] if p['id'] != promocode['id']]
                save_data(db)
                bot.send_message(user_id, f"✅ Промокод '{code}' застосовано! Ваша нова сума: {state['order_details']['totalPrice']} грн.")
            else:
                bot.send_message(user_id, "❌ Промокод недійсний або термін його дії закінчився.")
            # Після промокоду запитуємо про бонуси
            ask_about_bonuses(user_id, state['order_details'])
        elif step == 'waiting_for_new_name':
            name_parts = message.text.split()
            clients_db[str_user_id]['name'] = name_parts[0]
            clients_db[str_user_id]['surname'] = name_parts[1] if len(name_parts) > 1 else ""
            save_clients(clients_db)
            bot.send_message(user_id, get_text("name_changed", user_id))
            del ORDER_STATE[user_id]
        elif step == 'waiting_for_new_phone':
            clients_db[str_user_id]['phone'] = message.text
            save_clients(clients_db)
            bot.send_message(user_id, get_text("phone_changed", user_id))
            del ORDER_STATE[user_id]
        elif step == 'waiting_for_rating':
            try:
                rating = int(message.text)
                if 1 <= rating <= 5:
                    state['rating'] = rating
                    state['step'] = 'waiting_for_comment'
                    bot.send_message(user_id, "Дякуємо за оцінку! Тепер, будь ласка, напишіть ваш коментар.")
                else:
                    bot.send_message(user_id, "Будь ласка, введіть число від 1 до 5.")
            except ValueError:
                bot.send_message(user_id, "Некоректна оцінка. Будь ласка, введіть число від 1 до 5.")
        elif step == 'waiting_for_comment':
            comment = message.text
            order_id = state.get('order_id')
            rating = state.get('rating')
            order = next((o for o in db.get('orders', []) if o.get('orderId') == order_id), None)
            client_info = clients_db.get(str_user_id)
            if order and client_info:
                product_name_for_review = order.get('order_name', 'N/A')
                product_id_for_review = order['items'][0]['product_id'] if order['items'] else None
                review_data = {
                    "product_id": product_id_for_review, "product_name": product_name_for_review,
                    "user_id": user_id, "username": f"{client_info.get('name')} {client_info.get('surname')}",
                    "rating": rating, "comment": comment
                }
                try:
                    response = requests.post(f'http://127.0.0.1:5000/api/reviews', json=review_data)
                    if response.status_code == 201:
                        bot.send_message(user_id, "Дякуємо за ваш відгук! Він дуже важливий для нас.")
                    else:
                        bot.send_message(user_id, "Не вдалося зберегти ваш відгук. Спробуйте пізніше.")
                except Exception as e:
                    logging.error(f"Помилка відправки відгуку через API: {e}")
                    bot.send_message(user_id, "Сталася внутрішня помилка. Спробуйте пізніше.")
            else:
                bot.send_message(user_id, "Не вдалося знайти дані для відгуку.")
            del ORDER_STATE[user_id]
    except Exception as e:
        logging.error(f"Помилка в handle_order_flow: {e}")
        bot.send_message(message.chat.id, "Виникла помилка під час обробки вашого повідомлення.")

def show_my_purchases(message):
    try:
        user_id = str(message.from_user.id)
        user_orders = [o for o in db.get('orders', []) if str(o.get('telegram_id')) == user_id and o.get('status') == 'Виконано']
        if not user_orders:
            bot.send_message(message.chat.id, "У вас ще немає виконаних покупок.")
            return
        
        bot.send_message(message.chat.id, "<b>🔑 Ваші останні 5 покупок:</b>")
        for order in sorted(user_orders, key=lambda x: x['date'], reverse=True)[:5]:
            order_id = order.get('orderId')
            date = datetime.datetime.fromisoformat(order.get('date')).strftime('%d.%m.%Y %H:%M')
            
            items_text = ""
            for item in order.get('items', []):
                items_text += f"• {item['product_name']} (x{item.get('quantity', 1)}) - {item['price']} грн\n"

            response = (f"<b>Замовлення №{order_id[:8]} від {date}</b>\n\n"
                        f"<b>Склад:</b>\n{items_text}\n"
                        f"<b>Загальна сума: {order['totalPrice']} грн</b>")
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔄 Повторно отримати товар(и)", callback_data=f"reget_product_{order_id}"))
            bot.send_message(message.chat.id, response, reply_markup=markup)
    except Exception as e:
        logging.error(f"Помилка в 'Мої покупки': {e}")
        bot.send_message(message.chat.id, "Не вдалося завантажити історію покупок.")

def show_promotions(message):
    try:
        discounts = db.get('discounts', [])
        if not discounts:
            bot.send_message(message.chat.id, "Наразі активних акцій немає.")
            return
        response = "<b>🔥 Активні акції та знижки:</b>\n\n"
        for discount in discounts:
            percentage = discount.get('percentage', 0)
            target = discount.get('target', 'all')
            response += f"<b>- {percentage}% на:</b> "
            if target == 'all':
                response += "всі товари!\n"
            elif target == 'specific':
                product_ids = discount.get('product_ids', [])
                product_names = [p.get('name') for p in db.get('products', []) if p.get('id') in product_ids]
                if product_names:
                    response += f"{', '.join(product_names)}\n"
                else:
                    response += "окремі товари (не знайдено).\n"
        bot.send_message(message.chat.id, response)
    except Exception as e:
        logging.error(f"Помилка в 'Акції': {e}")
        bot.send_message(message.chat.id, "Не вдалося завантажити інформацію про акції.")

def show_reviews(message):
    try:
        approved_reviews = [r for r in db.get('reviews', []) if r.get('approved')]
        if not approved_reviews:
            bot.send_message(message.chat.id, "Наразі немає жодного відгуку.")
            return
        response = "<b>Останні відгуки наших клієнтів:</b>\n\n"
        for review in sorted(approved_reviews, key=lambda x: x['date'], reverse=True)[:5]:
            product_name = review.get('product_name', 'Невідомий товар')
            rating_stars = '⭐' * review.get('rating', 0)
            username = review.get('username', 'Анонім')
            comment = review.get('comment', '')
            date = datetime.datetime.fromisoformat(review.get('date')).strftime('%d.%m.%Y')
            response += f"<b>{product_name}</b>\n{rating_stars} від {username} ({date})\n<i>«{comment}»</i>\n\n"
        bot.send_message(message.chat.id, response)
    except Exception as e:
        logging.error(f"Помилка в 'Відгуки': {e}")
        bot.send_message(message.chat.id, "Не вдалося завантажити відгуки.")

def show_profile(message):
    user_id = str(message.from_user.id)
    if user_id in clients_db:
        client = clients_db[user_id]
        rank = get_user_rank(client.get('ltv', 0))
        rank_text = get_text("profile_rank", user_id).format(rank_name=rank['name'], bonus_percent=rank['bonus_percent'])
        
        response = (f"<b>👤 Ваш профіль</b>\n\n"
                    f"<b>Ім'я:</b> {client.get('name', '')} {client.get('surname', '')}\n"
                    f"<b>Телефон:</b> {client.get('phone', 'Не вказано')}\n\n"
                    f"{rank_text}\n"
                    f"<b>💰 Бонусний баланс:</b>\n{client.get('loyalty_points', 0)} Delon-гіків")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(get_text("btn_invite", user_id), callback_data="invite_friend"))
        bot.send_message(message.chat.id, response, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Не вдалося знайти ваш профіль. Спробуйте /start для реєстрації.")

@bot.callback_query_handler(func=lambda call: call.data == 'invite_friend')
@check_ban
def handle_invite_friend(call):
    user_id = call.from_user.id
    try:
        bot_username = bot.get_me().username
        referral_link = f"https://t.me/{bot_username}?start={user_id}"
        bonus = db.get('bonus_settings', {}).get('referral_bonus', 20)
        bot.send_message(user_id, get_text("referral_text", user_id).format(link=referral_link, bonus=bonus))
        bot.answer_callback_query(call.id)
    except Exception as e:
        logging.error(f"Не вдалося створити реферальне посилання: {e}")
        bot.answer_callback_query(call.id, "Помилка створення посилання.", show_alert=True)

def show_news(message):
    news = db.get('news', [])
    if not news:
        bot.send_message(message.chat.id, get_text("no_news", message.from_user.id))
        return
    bot.send_message(message.chat.id, get_text("news_title", message.from_user.id))
    for item in sorted(news, key=lambda x: x.get('created_at', '1970-01-01'), reverse=True)[:5]:
        caption = f"<i>🗓 {datetime.datetime.fromisoformat(item['created_at']).strftime('%d.%m.%Y')}</i>\n{item['text']}"
        try:
            if item.get('photo_id'):
                bot.send_photo(message.chat.id, item['photo_id'], caption=caption)
            elif item.get('document_id'):
                bot.send_document(message.chat.id, item['document_id'], caption=caption)
            else:
                bot.send_message(message.chat.id, caption)
        except Exception as e:
            logging.error(f"Не вдалося надіслати новину {item.get('id')}: {e}")
            bot.send_message(message.chat.id, caption)

def search_products(query):
    query_words = set(re.split(r'\s+', query.lower()))
    found_products = []
    for product in db.get('products', []):
        product_name_words = set(re.split(r'\s+', product.get('name', '').lower()))
        if query_words.intersection(product_name_words):
            found_products.append(product)
    return found_products

def show_settings_menu(message):
    user_id = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(get_text("btn_change_name", user_id), callback_data="setting_change_name"),
        types.InlineKeyboardButton(get_text("btn_change_phone", user_id), callback_data="setting_change_phone"),
        types.InlineKeyboardButton(get_text("btn_language", user_id), callback_data="setting_language")
    )
    bot.send_message(message.chat.id, get_text("settings_menu", user_id), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('setting_'))
@check_ban
def handle_settings_query(call):
    user_id = call.from_user.id
    action = call.data
    if action == "setting_language":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🇺🇦 Українська", callback_data="set_lang_uk"),
            types.InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru"),
            types.InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")
        )
        bot.edit_message_text(get_text("language_menu", user_id), call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif action == "setting_change_name":
        ORDER_STATE[user_id] = {'step': 'waiting_for_new_name'}
        bot.send_message(user_id, get_text("ask_new_name", user_id))
        bot.answer_callback_query(call.id)
    elif action == "setting_change_phone":
        ORDER_STATE[user_id] = {'step': 'waiting_for_new_phone'}
        bot.send_message(user_id, get_text("ask_new_phone", user_id))
        bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_lang_'))
@check_ban
def handle_set_language(call):
    user_id = str(call.from_user.id)
    lang_code = call.data.split('_')[-1]
    if user_id in clients_db:
        clients_db[user_id]['lang'] = lang_code
        save_clients(clients_db)
        bot.answer_callback_query(call.id, get_text("lang_set_success", user_id))
        show_main_menu(call.from_user.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "Error: User not found.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('toggle_wishlist_'))
@check_ban
def handle_wishlist_toggle(call):
    user_id = str(call.from_user.id)
    product_id = call.data.split('toggle_wishlist_')[1]
    if user_id not in clients_db:
        bot.answer_callback_query(call.id, "Спочатку зареєструйтесь.", show_alert=True)
        return
    if 'wishlist' not in clients_db[user_id]:
        clients_db[user_id]['wishlist'] = []
    wishlist = clients_db[user_id]['wishlist']
    if product_id in wishlist:
        wishlist.remove(product_id)
        alert_text = get_text("removed_from_wishlist", user_id)
    else:
        wishlist.append(product_id)
        alert_text = get_text("added_to_wishlist", user_id)
    save_clients(clients_db)
    bot.answer_callback_query(call.id, text=alert_text)
    product = get_product_by_id(product_id)
    if product:
        markup = types.InlineKeyboardMarkup(row_width=2)
        if product_id in clients_db[user_id]['wishlist']:
            wishlist_btn = types.InlineKeyboardButton(get_text("btn_remove_from_wishlist", user_id), callback_data=f"toggle_wishlist_{product_id}")
        else:
            wishlist_btn = types.InlineKeyboardButton(get_text("btn_add_to_wishlist", user_id), callback_data=f"toggle_wishlist_{product_id}")
        cart_btn = types.InlineKeyboardButton(get_text("btn_add_to_cart", user_id), callback_data=f"add_to_cart_{product['id']}")
        markup.add(wishlist_btn, cart_btn)
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
        except Exception as e:
            logging.error(f"Не вдалося оновити кнопку улюбленого: {e}")

def show_wishlist(message):
    user_id = str(message.from_user.id)
    wishlist_ids = clients_db.get(user_id, {}).get('wishlist', [])
    if not wishlist_ids:
        bot.send_message(message.chat.id, get_text("wishlist_empty", user_id))
        return
    bot.send_message(message.chat.id, get_text("wishlist_title", user_id))
    for product_id in wishlist_ids:
        product = get_product_by_id(product_id)
        if product:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Детальніше", callback_data=f"show_product_{product['id']}"))
            bot.send_message(message.chat.id, f"<b>{product['name']}</b>\nЦіна: {product['price']} грн", reply_markup=markup)

def show_bundles(message):
    user_id = message.from_user.id
    bundles = db.get('bundles', [])
    if not bundles:
        bot.send_message(user_id, get_text("bundles_empty", user_id))
        return
    bot.send_message(user_id, get_text("bundles_title", user_id))
    for bundle in bundles:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Детальніше", callback_data=f"bundle_{bundle['id']}"))
        bot.send_message(user_id, f"<b>{bundle['name']}</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('bundle_'))
@check_ban
def handle_bundle_details(call):
    user_id = call.from_user.id
    bundle_id = call.data.split('_')[1]
    bundle = next((b for b in db.get('bundles', []) if b['id'] == bundle_id), None)
    if not bundle:
        bot.answer_callback_query(call.id, "Колекцію не знайдено.", show_alert=True)
        return
    total_price = 0
    products_list_text = ""
    for pid in bundle['product_ids']:
        product = get_product_by_id(pid)
        if product:
            products_list_text += f"• {product['name']} ({product['price']} грн)\n"
            total_price += product['price']
    discount_price = round(total_price * (1 - bundle['discount_percentage'] / 100))
    text = get_text("bundle_details", user_id).format(
        name=bundle['name'], description=bundle.get('description', ''),
        products=products_list_text, total_price=total_price, discount_price=discount_price
    )
    markup = types.InlineKeyboardMarkup()
    buy_text = get_text("buy_bundle", user_id).format(price=discount_price)
    markup.add(types.InlineKeyboardButton(buy_text, callback_data=f"buy_bundle_{bundle_id}"))
    bot.send_message(user_id, text, reply_markup=markup)
    bot.answer_callback_query(call.id)

# --- НОВІ ФУНКЦІЇ ДЛЯ КОШИКА ---
def show_cart(message):
    user_id = str(message.from_user.id)
    cart_ids = clients_db.get(user_id, {}).get('cart', [])
    
    if not cart_ids:
        bot.send_message(message.chat.id, get_text("cart_empty", user_id))
        return

    text = get_text("cart_title", user_id) + "\n\n"
    total_price = 0
    product_counts = Counter(cart_ids)
    discounts = db.get('discounts', [])

    for product_id, count in product_counts.items():
        product = get_product_by_id(product_id)
        if product:
            discounted_product = apply_discounts([product], discounts)[0]
            price_to_use = discounted_product['discounted_price']
            total_price += price_to_use * count
            text += f"• {product['name']} x{count} - {price_to_use * count} грн\n"

    text += f"\n{get_text('total_price', user_id)} {total_price} грн"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(get_text("btn_clear_cart", user_id), callback_data="clear_cart"),
        types.InlineKeyboardButton(get_text("btn_checkout", user_id), callback_data="buy_cart")
    )
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('add_to_cart_'))
@check_ban
def handle_add_to_cart(call):
    user_id = str(call.from_user.id)
    product_id = call.data.split('add_to_cart_')[1]

    if user_id not in clients_db:
        bot.answer_callback_query(call.id, "Спочатку зареєструйтесь.", show_alert=True)
        return
        
    if 'cart' not in clients_db[user_id]:
        clients_db[user_id]['cart'] = []
        
    clients_db[user_id]['cart'].append(product_id)
    save_clients(clients_db)
    bot.answer_callback_query(call.id, text=get_text("added_to_cart", user_id))

@bot.callback_query_handler(func=lambda call: call.data == 'clear_cart')
@check_ban
def handle_clear_cart(call):
    user_id = str(call.from_user.id)
    if user_id in clients_db:
        clients_db[user_id]['cart'] = []
        save_clients(clients_db)
        bot.edit_message_text(get_text("cart_empty", user_id), call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, "Кошик очищено.")
# --- КІНЕЦЬ НОВИХ ФУНКЦІЙ ---

@bot.message_handler(commands=['news'])
def admin_add_news(message):
    if message.from_user.id not in ADMIN_IDS: return
    text = message.text.split(maxsplit=1)
    if len(text) < 2:
        bot.reply_to(message, "Використовуйте: /news <текст новини>")
        return
    new_item = {"id": str(uuid.uuid4()), "text": text[1], "created_at": datetime.datetime.now().isoformat()}
    db['news'].append(new_item)
    save_data(db)
    bot.reply_to(message, "✅ Новину додано.")

@bot.message_handler(commands=['post'])
def admin_broadcast(message):
    if message.from_user.id not in ADMIN_IDS: return
    text = message.text.split(maxsplit=1)
    if len(text) < 2:
        bot.reply_to(message, "Використовуйте: /post <текст розсилки>")
        return
    broadcast_thread = Thread(target=send_broadcast_message, args=(text[1], message.chat.id, None, None))
    broadcast_thread.start()

def send_broadcast_message(message_text, admin_chat_id, photo_id=None, document_id=None):
    success_count = 0
    fail_count = 0
    bot.send_message(admin_chat_id, f"🚀 Починаю розсилку...")
    for user_id in clients_db.keys():
        if not clients_db[user_id].get('is_banned', False):
            try:
                if photo_id:
                    bot.send_photo(user_id, photo_id, caption=message_text, parse_mode="HTML")
                elif document_id:
                    bot.send_document(user_id, document_id, caption=message_text, parse_mode="HTML")
                elif message_text:
                    bot.send_message(user_id, message_text, parse_mode="HTML")
                success_count += 1
                time.sleep(0.1)
            except Exception as e:
                logging.warning(f"Не вдалося відправити повідомлення користувачу {user_id}: {e}")
                fail_count += 1
    bot.send_message(admin_chat_id, f"🏁 Розсилку завершено.\n✅ Успішно: {success_count}\n❌ Помилок: {fail_count}")

def show_deal_of_the_day(message):
    user_id = str(message.from_user.id)
    deal = db.get("deal_of_the_day", {})
    if not deal or not deal.get("product_id"):
        bot.send_message(message.chat.id, get_text("no_deal_of_the_day", user_id))
        return

    product = get_product_by_id(deal["product_id"])
    if not product:
        bot.send_message(message.chat.id, get_text("no_deal_of_the_day", user_id))
        return

    # Перевірка, чи не закінчився термін дії акції
    if 'end_date' in deal and deal['end_date']:
        try:
            end_date = datetime.datetime.fromisoformat(deal['end_date'])
            if datetime.datetime.now() > end_date:
                bot.send_message(message.chat.id, get_text("no_deal_of_the_day", user_id))
                # Очистити прострочену акцію
                db['deal_of_the_day'] = {}
                save_data(db)
                return
        except (ValueError, TypeError):
            pass # Якщо дата некоректна, ігноруємо перевірку

    discount_percentage = deal.get("discount_percentage", 0)
    discounted_price = round(product['price'] * (1 - discount_percentage / 100))

    text = get_text("deal_of_the_day_title", user_id) + "\n\n"
    text += f"<b>{product['name']}</b>\n\n"
    text += f"Звичайна ціна: <s>{product['price']} грн</s>\n"
    text += f"🔥 <b>Ціна дня: {discounted_price} грн!</b> 🔥"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Переглянути товар", callback_data=f"show_product_{product['id']}"))
    
    try:
        bot.send_photo(message.chat.id, product['image'], caption=text, reply_markup=markup)
    except Exception:
        bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda message: True)
@check_ban
def handle_text_messages(message):
    try:
        user_id = message.from_user.id
        state = ORDER_STATE.get(user_id)

        # --- НОВА ЛОГІКА ПІДТРИМКИ ---
        if state and state.get('step') == 'in_support_chat':
            if message.text == get_text("btn_end_chat", user_id):
                del ORDER_STATE[user_id]
                bot.send_message(user_id, get_text("support_end", user_id))
                show_main_menu(user_id)
            else:
                bot.forward_message(TELEGRAM_CHAT_ID, from_chat_id=user_id, message_id=message.message_id)
            return
        
        if user_id in ADMIN_IDS and message.reply_to_message and message.reply_to_message.forward_from:
            original_user_id = message.reply_to_message.forward_from.id
            bot.send_message(original_user_id, f"<b>Відповідь від оператора:</b>\n\n{message.text}")
            return
        # --- КІНЕЦЬ НОВОЇ ЛОГІКИ ПІДТРИМКИ ---

        # Отримуємо текст кнопки на мові користувача для порівняння
        btn_catalog_text = get_text("btn_catalog", user_id)
        btn_cart_text = get_text("btn_cart", user_id)
        btn_purchases_text = get_text("btn_purchases", user_id)
        btn_support_text = get_text("btn_support", user_id)
        btn_promotions_text = get_text("btn_promotions", user_id)
        btn_about_text = get_text("btn_about", user_id)
        btn_reviews_text = get_text("btn_reviews", user_id)
        btn_profile_text = get_text("btn_profile", user_id)
        btn_settings_text = get_text("btn_settings", user_id)
        btn_wishlist_text = get_text("btn_wishlist", user_id)
        btn_bundles_text = get_text("btn_bundles", user_id)
        btn_news_text = get_text("btn_news", user_id)
        btn_deal_of_the_day_text = get_text("btn_deal_of_the_day", user_id)

        if state and message.text not in [btn_catalog_text, btn_cart_text, btn_purchases_text, btn_support_text, btn_promotions_text, btn_about_text, btn_reviews_text, btn_profile_text, btn_settings_text, btn_wishlist_text, btn_bundles_text, btn_news_text, btn_deal_of_the_day_text]:
            handle_order_flow(message)
            return

        if message.text == btn_catalog_text:
            text = get_text("catalog_title", user_id)
            markup = get_categories_markup(user_id)
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return

        if message.text == btn_cart_text:
            show_cart(message)
            return

        if message.text == btn_settings_text:
            show_settings_menu(message)
            return
        
        if message.text == btn_wishlist_text:
            show_wishlist(message)
            return
            
        if message.text == btn_bundles_text:
            show_bundles(message)
            return
            
        if message.text == btn_news_text:
            show_news(message)
            return

        if message.text == btn_purchases_text:
            show_my_purchases(message)
            return

        if message.text == btn_support_text:
            ORDER_STATE[user_id] = {'step': 'in_support_chat'}
            support_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            support_markup.add(types.KeyboardButton(get_text("btn_end_chat", user_id)))
            bot.send_message(user_id, get_text("support_start", user_id), reply_markup=support_markup)
            return

        if message.text == btn_promotions_text:
            show_promotions(message)
            return

        if message.text == btn_about_text:
            shop_info = db.get("shop_info", {})
            bot.send_message(message.chat.id, f"<b>{shop_info.get('name', 'Наш магазин')}</b>\n\n{shop_info.get('description', 'Ми найкращі!')}")
            return

        if message.text == btn_reviews_text:
            show_reviews(message)
            return

        if message.text == btn_profile_text:
            show_profile(message)
            return
            
        if message.text == btn_deal_of_the_day_text:
            show_deal_of_the_day(message)
            return

        found_products = search_products(message.text)
        if found_products:
            bot.send_message(message.chat.id, "🔎 Можливо, ви шукали:")
            for product in found_products[:3]:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("Переглянути", callback_data=f"show_product_{product['id']}"))
                bot.send_message(message.chat.id, f"<b>{product['name']}</b>\nЦіна: {product['price']} грн", reply_markup=markup)
            return

        for entry in chatbot_knowledge:
            keywords_list = [kw.strip().lower() for kw in entry.get('keywords', '').split(',')]
            if any(kw in message.text.lower() for kw in keywords_list):
                bot.send_message(message.chat.id, entry.get('response', '...'))
                return
        
        if not (message.from_user.id in ADMIN_IDS and message.reply_to_message):
            bot.send_message(message.chat.id, "Вибачте, я не зрозумів вашого запиту. Спробуйте використати кнопки або команду /start.")

    except Exception as e:
        logging.error(f"Помилка в handle_text_messages: {e}")
        bot.send_message(message.chat.id, "Виникла помилка під час обробки вашого повідомлення.")

# --- Статичні файли (завжди в кінці) ---
@app.route("/<path:filename>")
def serve_files(filename):
    return send_from_directory('.', filename)

# -----------------
# Запуск Flask та бота
# -----------------
if __name__ == "__main__":
    # Запускаємо бота в окремому потоці
    if bot:
        def run_bot_polling():
            while True:
                try:
                    logging.info("Telegram bot polling started...")
                    bot.infinity_polling(timeout=10, long_polling_timeout=5)
                except Exception as e:
                    logging.error(f"Помилка в боті, перезапускаємо... {e}")
                    time.sleep(5)
        bot_thread = Thread(target=run_bot_polling, daemon=True)
        bot_thread.start()

    # Запускаємо Flask-додаток
    logging.info("===================================================================")
    logging.info(f" * Адмін-панель доступна за локальною адресою: http://127.0.0.1:5000/admin.html")
    logging.info("===================================================================")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
