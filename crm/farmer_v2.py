#!/usr/bin/env python3
"""
ClientFarmer v2 — через Playwright (обход защиты)
Использование: python3 farmer_v2.py "Краснодар" "ремонт квартир"
"""

import csv
import sys
import time
import re
from playwright.sync_api import sync_playwright


def search_2gis(city: str, query: str, max_results: int = 200) -> list:
    """Парсинг 2GIS через браузер"""
    leads = []

    print(f"[2GIS] Запуск браузера...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = context.new_page()

        # Формируем URL поиска
        search_url = f"https://2gis.ru/{city.lower()}/search/{query.replace(' ', '%20')}"
        print(f"[2GIS] Открываю: {search_url}")

        try:
            page.goto(search_url, timeout=30000)
            page.wait_for_load_state('networkidle', timeout=15000)
            time.sleep(2)

            scroll_count = 0
            max_scrolls = 20

            while len(leads) < max_results and scroll_count < max_scrolls:
                # Ищем карточки компаний
                cards = page.query_selector_all('div[class*="miniCard"], div[class*="cardRow"], a[class*="_1hf6nkq"]')

                if not cards:
                    # Альтернативный селектор
                    cards = page.query_selector_all('[class*="orgsList"] > div')

                print(f"  Скролл {scroll_count + 1}: найдено {len(cards)} карточек")

                for card in cards:
                    try:
                        # Получаем название
                        name_el = card.query_selector('[class*="title"], [class*="name"], h3, a')
                        name = name_el.inner_text().strip() if name_el else None

                        if not name or len(name) < 3:
                            continue

                        # Кликаем на карточку чтобы открыть детали
                        card.click()
                        time.sleep(1)

                        # Ищем телефон в открывшейся панели
                        phone_el = page.query_selector('[class*="phone"] a, a[href^="tel:"]')
                        phone = None
                        if phone_el:
                            href = phone_el.get_attribute('href')
                            if href and href.startswith('tel:'):
                                phone = href.replace('tel:', '').strip()

                        # Проверяем наличие сайта
                        website_el = page.query_selector('[class*="website"], a[class*="link"][href^="http"]')
                        has_real_website = False
                        if website_el:
                            href = website_el.get_attribute('href') or ''
                            if href and 'vk.com' not in href.lower() and 'instagram' not in href.lower():
                                has_real_website = True

                        # Добавляем только без сайта
                        if name and phone and not has_real_website:
                            # Проверяем дубликаты
                            if not any(l['phone'] == phone for l in leads):
                                leads.append({
                                    'name': name,
                                    'phone': phone,
                                    'category': query,
                                    'city': city,
                                    'source': '2gis'
                                })
                                print(f"    + {name}: {phone}")

                    except Exception as e:
                        continue

                # Скроллим вниз
                page.keyboard.press('End')
                time.sleep(1.5)
                scroll_count += 1

        except Exception as e:
            print(f"[2GIS] Ошибка: {e}")

        finally:
            browser.close()

    return leads


def search_yandex_maps(city: str, query: str) -> list:
    """Парсинг Яндекс.Карт через браузер"""
    leads = []

    print(f"\n[Яндекс] Запуск браузера...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        search_url = f"https://yandex.ru/maps/?text={query.replace(' ', '%20')}%20{city}"
        print(f"[Яндекс] Открываю: {search_url}")

        try:
            page.goto(search_url, timeout=30000)
            page.wait_for_load_state('networkidle', timeout=15000)
            time.sleep(3)

            # Ищем карточки в списке слева
            cards = page.query_selector_all('[class*="search-snippet-view"], [class*="card-title-view"]')
            print(f"[Яндекс] Найдено карточек: {len(cards)}")

            for i, card in enumerate(cards[:50]):  # Берём первые 50
                try:
                    card.click()
                    time.sleep(1)

                    # Название
                    name_el = page.query_selector('[class*="title-view"], h1[class*="header"]')
                    name = name_el.inner_text().strip() if name_el else None

                    # Телефон
                    phone_el = page.query_selector('a[href^="tel:"]')
                    phone = None
                    if phone_el:
                        href = phone_el.get_attribute('href')
                        phone = href.replace('tel:', '').strip() if href else None

                    # Сайт
                    website_el = page.query_selector('[class*="website"], a[class*="business-urls"]')
                    has_real_website = False
                    if website_el:
                        text = website_el.inner_text().lower()
                        if text and 'vk.com' not in text and 'instagram' not in text:
                            has_real_website = True

                    if name and phone and not has_real_website:
                        if not any(l['phone'] == phone for l in leads):
                            leads.append({
                                'name': name,
                                'phone': phone,
                                'category': query,
                                'city': city,
                                'source': 'yandex'
                            })
                            print(f"    + {name}: {phone}")

                except Exception:
                    continue

        except Exception as e:
            print(f"[Яндекс] Ошибка: {e}")

        finally:
            browser.close()

    return leads


def save_leads(leads: list, filename: str = 'leads.csv'):
    """Сохранение в CSV"""
    if not leads:
        print("\nНет лидов для сохранения!")
        return

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'phone', 'category', 'city', 'source'])
        writer.writeheader()
        writer.writerows(leads)

    print(f"\n{'='*50}")
    print(f"ГОТОВО: {len(leads)} уникальных лидов БЕЗ САЙТА")
    print(f"Файл: {filename}")
    print(f"{'='*50}")


def main():
    if len(sys.argv) < 3:
        print("Использование: python3 farmer_v2.py <город> <запрос>")
        print("Пример: python3 farmer_v2.py Краснодар 'ремонт квартир'")
        sys.exit(1)

    city = sys.argv[1]
    query = sys.argv[2]

    print(f"\n{'='*50}")
    print(f"ClientFarmer v2 — DEFCON 1")
    print(f"Город: {city}")
    print(f"Ниша: {query}")
    print(f"{'='*50}\n")

    all_leads = []

    # 2GIS - основной источник
    all_leads.extend(search_2gis(city, query))

    # Яндекс - дополнительный
    if len(all_leads) < 50:
        all_leads.extend(search_yandex_maps(city, query))

    save_leads(all_leads)


if __name__ == '__main__':
    main()
