#!/usr/bin/env python3
"""
ClientFarmer — Avito Услуги
Ищет мастеров/компании с телефонами, без сайтов
"""

import csv
import sys
import time
import re
from playwright.sync_api import sync_playwright


def search_avito(city: str, query: str, max_pages: int = 5) -> list:
    """Парсинг Avito услуги"""
    leads = []

    # Маппинг городов на slug Avito
    city_slugs = {
        'москва': 'moskva', 'санкт-петербург': 'sankt-peterburg',
        'краснодар': 'krasnodar', 'сочи': 'sochi',
        'новосибирск': 'novosibirsk', 'екатеринбург': 'ekaterinburg',
        'казань': 'kazan', 'ростов-на-дону': 'rostov-na-donu',
        'нижний новгород': 'nizhniy_novgorod', 'воронеж': 'voronezh',
    }

    slug = city_slugs.get(city.lower(), city.lower())

    print(f"[Avito] Запуск браузера...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Видимый режим для отладки
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = context.new_page()

        for page_num in range(1, max_pages + 1):
            url = f"https://www.avito.ru/{slug}/predlozheniya_uslug?q={query.replace(' ', '+')}&p={page_num}"
            print(f"\n[Avito] Страница {page_num}: {url}")

            try:
                page.goto(url, timeout=30000)
                time.sleep(3)

                # Ждём загрузки объявлений
                page.wait_for_selector('[data-marker="item"]', timeout=10000)

                # Получаем все объявления
                items = page.query_selector_all('[data-marker="item"]')
                print(f"  Найдено объявлений: {len(items)}")

                for item in items:
                    try:
                        # Название
                        title_el = item.query_selector('[itemprop="name"]')
                        title = title_el.inner_text().strip() if title_el else None

                        # Ссылка на объявление
                        link_el = item.query_selector('a[itemprop="url"]')
                        link = link_el.get_attribute('href') if link_el else None

                        if not title or not link:
                            continue

                        # Открываем объявление в новой вкладке
                        detail_page = context.new_page()
                        detail_page.goto(f"https://www.avito.ru{link}", timeout=20000)
                        time.sleep(2)

                        # Ищем кнопку "Показать телефон"
                        phone_btn = detail_page.query_selector('[data-marker="item-phone-button"]')
                        phone = None

                        if phone_btn:
                            phone_btn.click()
                            time.sleep(1.5)

                            # Ищем телефон
                            phone_el = detail_page.query_selector('[data-marker="phone-popup/phone-number"], a[href^="tel:"]')
                            if phone_el:
                                phone_text = phone_el.inner_text().strip()
                                # Чистим телефон
                                phone = re.sub(r'[^\d+]', '', phone_text)

                        # У Avito услуг редко бывают сайты - берём всех с телефонами
                        if title and phone and len(phone) >= 10:
                            if not any(l['phone'] == phone for l in leads):
                                leads.append({
                                    'name': title,
                                    'phone': phone,
                                    'category': query,
                                    'city': city,
                                    'source': 'avito'
                                })
                                print(f"    + {title[:40]}: {phone}")

                        detail_page.close()
                        time.sleep(0.5)

                    except Exception as e:
                        continue

            except Exception as e:
                print(f"  Ошибка: {e}")
                continue

        browser.close()

    return leads


def save_leads(leads: list, filename: str = 'leads.csv'):
    if not leads:
        print("\nНет лидов!")
        return

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'phone', 'category', 'city', 'source'])
        writer.writeheader()
        writer.writerows(leads)

    print(f"\n{'='*50}")
    print(f"ГОТОВО: {len(leads)} лидов")
    print(f"Файл: {filename}")
    print(f"{'='*50}")


def main():
    if len(sys.argv) < 3:
        print("Использование: python3 farmer_avito.py <город> <запрос>")
        print("Пример: python3 farmer_avito.py краснодар 'ремонт квартир'")
        sys.exit(1)

    city = sys.argv[1]
    query = sys.argv[2]

    print(f"\n{'='*50}")
    print(f"ClientFarmer — Avito")
    print(f"Город: {city}")
    print(f"Ниша: {query}")
    print(f"{'='*50}")

    leads = search_avito(city, query)
    save_leads(leads)


if __name__ == '__main__':
    main()
