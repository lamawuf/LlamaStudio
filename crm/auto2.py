#!/usr/bin/env python3
"""
ClientFarmer v2 — С фильтрами 2GIS
Собирает ВСЮ базу без сайтов.

Запуск: python3 auto2.py krasnodar "ремонт квартир"
"""

import csv
import sys
import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright


def run(city: str, query: str):
    leads = []
    seen_phones = set()
    seen_names = set()

    print(f"\n{'='*55}")
    print("  ClientFarmer v2 — ПЫЛЕСОС")
    print(f"{'='*55}")
    print(f"  Город: {city}")
    print(f"  Запрос: {query}")
    print(f"  Цель: ВСЯ БАЗА без сайтов")
    print(f"{'='*55}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1400, 'height': 900})

        # URL с рубрикой "ремонт квартир" и сортировкой
        # Важно: НЕ включаем фильтр "с сайтом"
        base_url = f"https://2gis.ru/{city}/search/{query.replace(' ', '%20')}"

        print(f"🌐 Открываю: {base_url}\n")
        page.goto(base_url, timeout=30000)
        time.sleep(3)

        # Ждём загрузки списка
        page.wait_for_selector('a[href*="/firm/"]', timeout=10000)

        print("📋 Собираю ссылки на все компании...\n")

        all_firm_links = set()
        last_count = 0
        no_change_count = 0

        # Скроллим и собираем ВСЕ ссылки на фирмы
        while no_change_count < 10:
            # Находим все ссылки на фирмы
            links = page.query_selector_all('a[href*="/firm/"]')

            for link in links:
                href = link.get_attribute('href')
                if href and '/firm/' in href:
                    # Извлекаем ID фирмы
                    firm_url = href.split('?')[0]  # Убираем параметры
                    if firm_url not in all_firm_links:
                        all_firm_links.add(firm_url)

            current_count = len(all_firm_links)

            if current_count == last_count:
                no_change_count += 1
            else:
                no_change_count = 0
                print(f"  Найдено ссылок: {current_count}")

            last_count = current_count

            # Скроллим
            page.keyboard.press('End')
            time.sleep(0.8)

        print(f"\n✅ Собрано {len(all_firm_links)} уникальных компаний")
        print("🔍 Проверяю каждую на наличие сайта...\n")

        # Теперь проходим по каждой фирме
        for i, firm_url in enumerate(all_firm_links):
            try:
                # Формируем полный URL
                full_url = firm_url if firm_url.startswith('http') else f"https://2gis.ru{firm_url}"

                page.goto(full_url, timeout=15000)
                time.sleep(1)

                # Название
                name = None
                name_el = page.query_selector('h1')
                if name_el:
                    name = name_el.inner_text().strip()

                if not name or name in seen_names:
                    continue

                seen_names.add(name)

                # Проверяем есть ли сайт
                has_site = False

                # Ищем секцию с сайтом
                site_section = page.query_selector('[class*="website"], a[href^="http"]:not([href*="2gis"]):not([href*="vk.com"]):not([href*="instagram"]):not([href*="wa.me"]):not([href*="t.me"])')

                # Более точная проверка - ищем иконку/текст "Сайт"
                page_content = page.content()
                if 'class="website"' in page_content.lower() or '>сайт<' in page_content.lower():
                    # Проверяем что это не соцсеть
                    site_links = page.query_selector_all('a[href^="http"]')
                    for sl in site_links:
                        href = (sl.get_attribute('href') or '').lower()
                        text = (sl.inner_text() or '').lower()
                        if href and 'сайт' in text or ('.' in href and not any(x in href for x in ['2gis', 'vk.com', 'instagram', 't.me', 'wa.me', 'facebook', 'youtube', 'ok.ru', 'whatsapp'])):
                            # Дополнительная проверка - это ссылка на внешний сайт?
                            if re.match(r'https?://[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}', href):
                                if not any(x in href for x in ['2gis', 'vk.com', 'instagram', 't.me', 'wa.me', 'facebook', 'youtube', 'ok.ru']):
                                    has_site = True
                                    break

                # Если есть сайт - пропускаем
                if has_site:
                    print(f"⏭  [{i+1}/{len(all_firm_links)}] {name[:40]} — есть сайт")
                    continue

                # Ищем телефон
                phone = None
                phone_links = page.query_selector_all('a[href^="tel:"]')
                for pl in phone_links:
                    href = pl.get_attribute('href')
                    if href:
                        ph = re.sub(r'[^\d+]', '', href.replace('tel:', ''))
                        if len(ph) >= 10:
                            if ph.startswith('8') and len(ph) == 11:
                                ph = '+7' + ph[1:]
                            if ph not in seen_phones:
                                phone = ph
                                seen_phones.add(ph)
                                break

                if not phone:
                    print(f"⏭  [{i+1}/{len(all_firm_links)}] {name[:40]} — нет телефона")
                    continue

                # Добавляем лид!
                leads.append({
                    'name': name,
                    'phone': phone,
                    'city': city,
                    'query': query,
                    'url': full_url
                })

                print(f"✅ [{len(leads)}] {name[:40]}")
                print(f"   📞 {phone}\n")

            except Exception as e:
                continue

            # Каждые 20 - сохраняем промежуточный результат
            if len(leads) > 0 and len(leads) % 20 == 0:
                save_leads(leads, city, interim=True)

        browser.close()

    # Финальное сохранение
    save_leads(leads, city, interim=False)


def save_leads(leads, city, interim=False):
    if not leads:
        return

    filename = f"leads_{city}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'phone', 'city', 'query', 'url'])
        writer.writeheader()
        writer.writerows(leads)

    if interim:
        print(f"💾 Промежуточное сохранение: {len(leads)} лидов → {filename}\n")
    else:
        print(f"\n{'='*55}")
        print(f"  ✅ ГОТОВО: {len(leads)} лидов БЕЗ сайтов")
        print(f"  📁 Файл: {filename}")
        print(f"{'='*55}\n")


def main():
    city = sys.argv[1] if len(sys.argv) > 1 else "krasnodar"
    query = sys.argv[2] if len(sys.argv) > 2 else "ремонт квартир"

    run(city, query)


if __name__ == '__main__':
    main()
