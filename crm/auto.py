#!/usr/bin/env python3
"""
ClientFarmer — ПОЛНЫЙ АВТОМАТ
Сам кликает, сам скроллит, сам собирает.

Запуск: python3 auto.py "краснодар" "ремонт квартир"
"""

import csv
import sys
import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright


def run(city: str, query: str, max_leads: int = 100):
    leads = []
    seen_phones = set()

    print(f"\n{'='*55}")
    print("  ClientFarmer — АВТОМАТ")
    print(f"{'='*55}")
    print(f"  Город: {city}")
    print(f"  Запрос: {query}")
    print(f"  Цель: {max_leads} лидов")
    print(f"{'='*55}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1400, 'height': 900})

        # Открываем 2GIS
        url = f"https://2gis.ru/{city}/search/{query.replace(' ', '%20')}"
        print(f"🌐 Открываю: {url}\n")
        page.goto(url, timeout=30000)
        time.sleep(3)

        processed_names = set()
        scroll_count = 0
        max_scrolls = 50
        no_new_count = 0

        while len(leads) < max_leads and scroll_count < max_scrolls:
            # Ищем карточки компаний в списке
            cards = page.query_selector_all('[class*="_1hf6nkq"], [class*="miniCard"], a[href*="/firm/"]')

            if not cards:
                # Альтернативные селекторы
                cards = page.query_selector_all('a[data-marker="item"]')

            if not cards:
                # Ещё вариант - любые ссылки на firm
                cards = page.locator('a[href*="/firm/"]').all()

            new_found = False

            for card in cards:
                try:
                    # Получаем текст или название
                    card_text = card.inner_text() if hasattr(card, 'inner_text') else ""

                    # Пропускаем уже обработанные
                    if card_text[:50] in processed_names:
                        continue

                    processed_names.add(card_text[:50])
                    new_found = True

                    # Кликаем на карточку
                    card.click()
                    time.sleep(1.5)

                    # Теперь ищем данные в открывшейся панели справа

                    # Название
                    name = None
                    for sel in ['h1', '[class*="_oqoid"]', '[class*="title"]']:
                        el = page.query_selector(sel)
                        if el:
                            text = el.inner_text().strip()
                            if text and len(text) > 2 and len(text) < 150:
                                name = text
                                break

                    # Телефон - ищем ссылку tel:
                    phone = None
                    phone_links = page.query_selector_all('a[href^="tel:"]')
                    for pl in phone_links:
                        href = pl.get_attribute('href')
                        if href:
                            ph = re.sub(r'[^\d+]', '', href.replace('tel:', ''))
                            if len(ph) >= 10:
                                if ph.startswith('8') and len(ph) == 11:
                                    ph = '+7' + ph[1:]
                                phone = ph
                                break

                    # Проверяем сайт
                    has_site = False
                    site_links = page.query_selector_all('a[href^="http"]')
                    for sl in site_links:
                        href = (sl.get_attribute('href') or '').lower()
                        # Игнорируем соцсети и 2gis
                        if href and not any(x in href for x in ['2gis', 'vk.com', 'instagram', 't.me', 'wa.me', 'facebook', 'youtube', 'ok.ru']):
                            # Это реальный сайт
                            has_site = True
                            break

                    # Добавляем лид
                    if name and phone and phone not in seen_phones:
                        if not has_site:
                            seen_phones.add(phone)
                            leads.append({
                                'name': name,
                                'phone': phone,
                                'city': city,
                                'query': query
                            })
                            print(f"✅ [{len(leads)}] {name[:45]}")
                            print(f"   📞 {phone}\n")
                        else:
                            print(f"⏭  {name[:45]} — есть сайт\n")

                except Exception as e:
                    continue

            if not new_found:
                no_new_count += 1
                if no_new_count > 3:
                    print("⚠️  Новых карточек нет, скроллю...")
            else:
                no_new_count = 0

            # Скроллим список
            try:
                # Ищем контейнер со списком
                list_container = page.query_selector('[class*="_1hf6nkq"]') or page.query_selector('[class*="scroll"]')
                if list_container:
                    list_container.evaluate('el => el.scrollBy(0, 500)')
                else:
                    page.keyboard.press('PageDown')
            except:
                page.keyboard.press('PageDown')

            time.sleep(1)
            scroll_count += 1

            # Прогресс
            if scroll_count % 5 == 0:
                print(f"📊 Скролл {scroll_count}, собрано: {len(leads)} лидов\n")

        browser.close()

    # Сохранение
    if leads:
        filename = f"leads_{city}_{datetime.now().strftime('%H%M')}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'phone', 'city', 'query'])
            writer.writeheader()
            writer.writerows(leads)

        print(f"\n{'='*55}")
        print(f"  ✅ ГОТОВО: {len(leads)} лидов БЕЗ сайтов")
        print(f"  📁 Файл: {filename}")
        print(f"{'='*55}\n")
    else:
        print("\n❌ Не удалось собрать лиды")


def main():
    city = sys.argv[1] if len(sys.argv) > 1 else "krasnodar"
    query = sys.argv[2] if len(sys.argv) > 2 else "ремонт квартир"
    max_leads = int(sys.argv[3]) if len(sys.argv) > 3 else 100

    run(city, query, max_leads)


if __name__ == '__main__':
    main()
