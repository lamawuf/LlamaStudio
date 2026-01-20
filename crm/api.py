#!/usr/bin/env python3
"""
ClientFarmer — через API 2GIS (без браузера)
Быстро, надёжно.

Запуск: python3 api.py krasnodar "ремонт квартир"
"""

import csv
import sys
import time
import requests

# API ключ из веб-версии 2GIS (публичный)
API_KEY = "rurbbn3446"

# ID регионов
REGIONS = {
    'krasnodar': 4959,
    'краснодар': 4959,
    'moscow': 32,
    'москва': 32,
    'spb': 38,
    'санкт-петербург': 38,
    'sochi': 11079,
    'сочи': 11079,
    'novosibirsk': 4400,
    'новосибирск': 4400,
    'ekaterinburg': 3562,
    'екатеринбург': 3562,
    'kazan': 4150,
    'казань': 4150,
    'rostov': 5044,
    'ростов-на-дону': 5044,
}


def search_2gis(city: str, query: str, page: int = 1):
    """Поиск через API 2GIS"""

    region_id = REGIONS.get(city.lower(), 4959)

    url = "https://catalog.api.2gis.com/3.0/items"
    params = {
        'q': query,
        'region_id': region_id,
        'page': page,
        'page_size': 50,
        'key': API_KEY,
        'fields': 'items.contact_groups,items.external_content',
        'sort': 'relevance',
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        return data.get('result', {}).get('items', [])
    except Exception as e:
        print(f"Ошибка API: {e}")
        return []


def extract_lead(item: dict) -> dict | None:
    """Извлечь данные из элемента API"""

    name = item.get('name', '')
    if not name:
        return None

    # Телефон
    phone = None
    contacts = item.get('contact_groups', [])
    for group in contacts:
        for contact in group.get('contacts', []):
            if contact.get('type') == 'phone':
                phone = contact.get('value', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
                if phone.startswith('8') and len(phone) == 11:
                    phone = '+7' + phone[1:]
                break
        if phone:
            break

    if not phone:
        return None

    # Проверка сайта
    has_website = False
    for group in contacts:
        for contact in group.get('contacts', []):
            if contact.get('type') == 'website':
                url = contact.get('value', '').lower()
                # Игнорируем соцсети
                skip = ['vk.com', 'instagram', 't.me', 'wa.me', 'facebook', 'youtube', 'ok.ru']
                if not any(s in url for s in skip):
                    has_website = True
                    break
        if has_website:
            break

    if has_website:
        return None  # Пропускаем с сайтом

    return {
        'name': name,
        'phone': phone,
    }


def main():
    city = sys.argv[1] if len(sys.argv) > 1 else "krasnodar"
    query = sys.argv[2] if len(sys.argv) > 2 else "ремонт квартир"

    print(f"\n{'='*55}")
    print(f"  ClientFarmer — API")
    print(f"{'='*55}")
    print(f"  Город: {city}")
    print(f"  Запрос: {query}")
    print(f"{'='*55}\n")

    leads = []
    seen_phones = set()

    # Перебираем страницы
    for page in range(1, 30):  # Максимум 30 страниц = 1500 результатов
        print(f"📄 Страница {page}...", end=" ")

        items = search_2gis(city, query, page)

        if not items:
            print("пусто, стоп")
            break

        page_leads = 0
        for item in items:
            lead = extract_lead(item)
            if lead and lead['phone'] not in seen_phones:
                seen_phones.add(lead['phone'])
                leads.append(lead)
                page_leads += 1

        print(f"+{page_leads} лидов (всего: {len(leads)})")

        time.sleep(0.5)  # Пауза между запросами

    # Сохранение
    if leads:
        filename = f"leads_{city}_api.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'phone'])
            writer.writeheader()
            writer.writerows(leads)

        print(f"\n{'='*55}")
        print(f"  ✅ ГОТОВО: {len(leads)} лидов БЕЗ сайта")
        print(f"  📁 Файл: {filename}")
        print(f"{'='*55}\n")

        # Показать первые 10
        print("Первые лиды:")
        for lead in leads[:10]:
            print(f"  • {lead['name'][:40]} | {lead['phone']}")
    else:
        print("\n❌ Не удалось собрать лиды")


if __name__ == '__main__':
    main()
