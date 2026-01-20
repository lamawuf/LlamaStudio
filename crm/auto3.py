#!/usr/bin/env python3
"""
ClientFarmer v3 — Остаётся на странице поиска
Кликает карточки → читает боковую панель → следующая

Запуск: python3 auto3.py krasnodar "ремонт квартир"
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

    print(f"\n{'='*55}")
    print("  ClientFarmer v3 — ПЫЛЕСОС")
    print(f"{'='*55}")
    print(f"  Город: {city}")
    print(f"  Запрос: {query}")
    print(f"{'='*55}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1400, 'height': 900})

        # Открываем поиск с сортировкой "по новизне"
        url = f"https://2gis.ru/{city}/search/{query.replace(' ', '%20')}/sort/dateUpdated"
        print(f"🌐 Открываю: {url}\n")
        page.goto(url, timeout=30000)
        time.sleep(4)

        # Если сортировка не применилась через URL — кликаем вручную
        try:
            sort_btn = page.locator('text=Сортировка').first
            if sort_btn:
                sort_btn.click()
                time.sleep(0.5)
                page.locator('text=По новизне').first.click()
                time.sleep(1)
                print("📋 Сортировка: По новизне\n")
        except:
            pass

        processed_indices = set()
        total_processed = 0
        max_iterations = 500  # Защита от бесконечного цикла

        for iteration in range(max_iterations):
            # Находим все карточки в списке слева
            # Селектор для элементов списка 2GIS
            cards = page.locator('div[class*="_1kf6gff"]').all()

            if not cards:
                cards = page.locator('a[href*="/firm/"]').all()

            if not cards:
                # Пробуем другой селектор
                cards = page.locator('[data-marker="catalog-item"]').all()

            found_new = False

            for idx, card in enumerate(cards):
                if idx in processed_indices:
                    continue

                try:
                    # Кликаем на карточку
                    card.click()
                    time.sleep(1.5)
                    processed_indices.add(idx)
                    found_new = True
                    total_processed += 1

                    # Читаем данные из правой панели
                    # Название - ищем h1 или заголовок
                    name = None
                    try:
                        name_el = page.locator('h1').first
                        if name_el:
                            name = name_el.inner_text(timeout=2000).strip()
                    except:
                        pass

                    if not name:
                        continue

                    # Телефон
                    phone = None
                    try:
                        phone_links = page.locator('a[href^="tel:"]').all()
                        for pl in phone_links:
                            href = pl.get_attribute('href')
                            if href:
                                ph = re.sub(r'[^\d+]', '', href.replace('tel:', ''))
                                if len(ph) >= 10:
                                    if ph.startswith('8') and len(ph) == 11:
                                        ph = '+7' + ph[1:]
                                    phone = ph
                                    break
                    except:
                        pass

                    # Проверяем сайт — ищем ссылку с текстом домена
                    has_site = False
                    try:
                        # Ищем элементы которые выглядят как сайт
                        all_links = page.locator('a[href^="http"]').all()
                        for link in all_links:
                            href = (link.get_attribute('href') or '').lower()
                            # Исключаем соцсети и служебные
                            skip = ['2gis', 'vk.com', 'instagram', 't.me', 'wa.me',
                                   'facebook', 'youtube', 'ok.ru', 'whatsapp', 'viber']
                            if href and not any(x in href for x in skip):
                                # Проверяем что это похоже на сайт компании
                                if re.search(r'\.[a-z]{2,3}/?$', href) or re.search(r'\.[a-z]{2,3}/[^/]*$', href):
                                    has_site = True
                                    break
                    except:
                        pass

                    # Результат
                    if phone and phone not in seen_phones:
                        if not has_site:
                            seen_phones.add(phone)
                            leads.append({
                                'name': name,
                                'phone': phone,
                            })
                            print(f"✅ [{len(leads)}] {name[:45]}")
                            print(f"   📞 {phone}")
                        else:
                            print(f"⏭  {name[:45]} — сайт есть")
                    else:
                        if not phone:
                            print(f"⏭  {name[:45]} — нет телефона")

                except Exception as e:
                    continue

            # Если не нашли новых карточек — скроллим
            if not found_new:
                print(f"\n📜 Скролл... (обработано: {total_processed}, лидов: {len(leads)})")

                # Скроллим список
                try:
                    # Ищем контейнер списка и скроллим его
                    page.keyboard.press('End')
                    time.sleep(1.5)

                    # Проверяем появились ли новые карточки
                    new_cards = page.locator('a[href*="/firm/"]').all()
                    if len(new_cards) <= len(processed_indices):
                        # Больше карточек не появляется
                        print("⚠️  Достигнут конец списка")
                        break
                except:
                    break

            # Автосохранение каждые 10 лидов
            if len(leads) > 0 and len(leads) % 10 == 0:
                save_leads(leads, city)
                print(f"💾 Сохранено: {len(leads)}\n")

        browser.close()

    # Финальное сохранение
    save_leads(leads, city)
    print(f"\n{'='*55}")
    print(f"  ✅ ИТОГО: {len(leads)} лидов БЕЗ сайта")
    print(f"  📁 Проверено компаний: {total_processed}")
    print(f"{'='*55}\n")


def save_leads(leads, city):
    if not leads:
        return

    filename = f"leads_{city}.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'phone'])
        writer.writeheader()
        writer.writerows(leads)


def main():
    city = sys.argv[1] if len(sys.argv) > 1 else "krasnodar"
    query = sys.argv[2] if len(sys.argv) > 2 else "ремонт квартир"
    run(city, query)


if __name__ == '__main__':
    main()
