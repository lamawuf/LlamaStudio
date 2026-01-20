#!/usr/bin/env python3
"""
ClientFarmer — сбор лидов без сайтов
Использование: python farmer.py "Краснодар" "ремонт квартир"
"""

import csv
import sys
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

# Настройки
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
}

def search_zoon(city: str, query: str, pages: int = 5) -> list:
    """Парсинг Zoon.ru"""
    leads = []
    base_url = f"https://{city.lower()}.zoon.ru/search/"

    print(f"[Zoon] Ищу: {query} в {city}")

    for page in range(1, pages + 1):
        url = f"{base_url}?search_query={quote(query)}&page={page}"
        print(f"  Страница {page}...", end=" ")

        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                print(f"Ошибка {resp.status_code}")
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')
            items = soup.select('.minicard-item')

            if not items:
                print("Пусто, стоп")
                break

            for item in items:
                try:
                    name_el = item.select_one('.minicard-item__title a')
                    name = name_el.text.strip() if name_el else None

                    # Ищем телефон
                    phone_el = item.select_one('[data-phone]')
                    phone = phone_el.get('data-phone') if phone_el else None

                    # Проверяем наличие сайта
                    website_el = item.select_one('.minicard-item__website')
                    has_real_website = False
                    if website_el:
                        site_text = website_el.text.lower()
                        # VK/Instagram не считаем сайтом
                        if 'vk.com' not in site_text and 'instagram' not in site_text:
                            has_real_website = True

                    # Берём только БЕЗ сайта
                    if name and phone and not has_real_website:
                        leads.append({
                            'name': name,
                            'phone': phone,
                            'category': query,
                            'city': city,
                            'source': 'zoon'
                        })

                except Exception as e:
                    continue

            print(f"Найдено: {len(items)} карточек")
            time.sleep(random.uniform(1, 2))  # Пауза между страницами

        except Exception as e:
            print(f"Ошибка: {e}")
            continue

    return leads


def search_yell(city: str, query: str, pages: int = 5) -> list:
    """Парсинг Yell.ru"""
    leads = []

    print(f"[Yell] Ищу: {query} в {city}")

    for page in range(1, pages + 1):
        url = f"https://www.yell.ru/{city.lower()}/top/{quote(query)}/?page={page}"
        print(f"  Страница {page}...", end=" ")

        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                print(f"Ошибка {resp.status_code}")
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')
            items = soup.select('.company-card')

            if not items:
                print("Пусто, стоп")
                break

            for item in items:
                try:
                    name_el = item.select_one('.company-card__title')
                    name = name_el.text.strip() if name_el else None

                    phone_el = item.select_one('.company-card__phone')
                    phone = phone_el.text.strip() if phone_el else None

                    # Проверяем сайт
                    website_el = item.select_one('.company-card__website')
                    has_real_website = False
                    if website_el:
                        site_text = website_el.text.lower()
                        if 'vk.com' not in site_text and 'instagram' not in site_text:
                            has_real_website = True

                    if name and phone and not has_real_website:
                        leads.append({
                            'name': name,
                            'phone': phone,
                            'category': query,
                            'city': city,
                            'source': 'yell'
                        })

                except Exception:
                    continue

            print(f"Найдено: {len(items)} карточек")
            time.sleep(random.uniform(1, 2))

        except Exception as e:
            print(f"Ошибка: {e}")
            continue

    return leads


def search_2gis_api(city: str, query: str) -> list:
    """2GIS через публичный API (без ключа, лимиты)"""
    leads = []

    # Маппинг городов на region_id 2GIS
    city_ids = {
        'москва': 32, 'санкт-петербург': 38, 'краснодар': 36,
        'новосибирск': 22, 'екатеринбург': 66, 'казань': 30,
        'нижний новгород': 34, 'самара': 40, 'ростов-на-дону': 39,
        'воронеж': 26, 'красноярск': 35, 'сочи': 1061,
    }

    region_id = city_ids.get(city.lower(), 32)

    print(f"[2GIS] Ищу: {query} в {city}")

    # Публичный API endpoint (может потребовать ключ в будущем)
    api_url = f"https://catalog.api.2gis.com/3.0/items"
    params = {
        'q': query,
        'region_id': region_id,
        'page_size': 50,
        'fields': 'items.contact_groups,items.name_ex,items.external_content',
        'key': 'rurbbn3446'  # Публичный ключ из веб-версии
    }

    try:
        resp = requests.get(api_url, params=params, headers=HEADERS, timeout=10)
        data = resp.json()

        items = data.get('result', {}).get('items', [])
        print(f"  Получено: {len(items)} результатов")

        for item in items:
            name = item.get('name', '')
            item_id = item.get('id', '')

            # Извлекаем контакты
            phone = None
            socials = []
            has_website = False

            contacts = item.get('contact_groups', [])
            for group in contacts:
                for contact in group.get('contacts', []):
                    contact_type = contact.get('type', '')
                    contact_value = contact.get('value', '')

                    # Телефон
                    if contact_type == 'phone' and not phone:
                        phone = contact_value

                    # Соцсети и мессенджеры
                    if contact_type == 'whatsapp':
                        socials.append('WhatsApp')
                    elif contact_type == 'telegram':
                        socials.append('Telegram')
                    elif contact_type == 'viber':
                        socials.append('Viber')
                    elif contact_type == 'vkontakte':
                        socials.append('VK')
                    elif contact_type == 'instagram':
                        socials.append('Instagram')
                    elif contact_type == 'youtube':
                        socials.append('YouTube')
                    elif contact_type == 'facebook':
                        socials.append('Facebook')
                    elif contact_type == 'odnoklassniki':
                        socials.append('OK')

                    # Проверяем сайт
                    if contact_type == 'website':
                        url_lower = contact_value.lower()
                        if 'vk.com' not in url_lower and 'instagram' not in url_lower:
                            has_website = True

            # Формируем URL на 2GIS
            url_2gis = f"https://2gis.ru/firm/{item_id}" if item_id else None

            if name and phone and not has_website:
                leads.append({
                    'name': name,
                    'phone': phone,
                    'social': ', '.join(sorted(set(socials))) if socials else None,
                    'url_2gis': url_2gis,
                    'category': query,
                    'city': city,
                    'source': '2gis'
                })

    except Exception as e:
        print(f"  Ошибка 2GIS API: {e}")

    return leads


def save_leads(leads: list, filename: str = 'leads.csv'):
    """Сохранение в CSV"""
    if not leads:
        print("Нет лидов для сохранения!")
        return

    # Убираем дубликаты по телефону
    seen = set()
    unique = []
    for lead in leads:
        if lead['phone'] not in seen:
            seen.add(lead['phone'])
            unique.append(lead)

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'phone', 'social', 'url_2gis', 'category', 'city', 'source'])
        writer.writeheader()
        writer.writerows(unique)

    print(f"\n{'='*50}")
    print(f"ГОТОВО: {len(unique)} уникальных лидов")
    print(f"Файл: {filename}")
    print(f"{'='*50}")


def main():
    if len(sys.argv) < 3:
        print("Использование: python farmer.py <город> <запрос>")
        print("Пример: python farmer.py Краснодар 'ремонт квартир'")
        sys.exit(1)

    city = sys.argv[1]
    query = sys.argv[2]

    print(f"\n{'='*50}")
    print(f"ClientFarmer — DEFCON 1")
    print(f"Город: {city}")
    print(f"Ниша: {query}")
    print(f"{'='*50}\n")

    all_leads = []

    # Собираем из всех источников
    all_leads.extend(search_2gis_api(city, query))
    all_leads.extend(search_zoon(city, query))
    # all_leads.extend(search_yell(city, query))  # Раскомментируй если нужно больше

    save_leads(all_leads)


if __name__ == '__main__':
    main()
