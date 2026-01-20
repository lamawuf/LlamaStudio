#!/usr/bin/env python3
"""
ClientFarmer — Кликер
Ты кликаешь на карточки в 2GIS, скрипт собирает телефоны.

Запуск: python3 clicker.py
"""

import csv
import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright


def main():
    leads = []
    seen = set()

    print(f"\n{'='*55}")
    print("  ClientFarmer — КЛИКЕР")
    print(f"{'='*55}")
    print("""
  1. Откроется браузер с 2GIS
  2. Введи поиск (например "ремонт квартир")
  3. КЛИКАЙ на карточки компаний слева
  4. Скрипт автоматически соберёт: название + телефон
  5. Закрой браузер когда закончишь

  💡 Бери только тех, у кого НЕТ сайта в карточке!
""")
    print(f"{'='*55}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1400, 'height': 900})
        page = context.new_page()

        page.goto("https://2gis.ru/krasnodar")
        print("✅ Браузер открыт. Ищи и кликай!\n")

        last_url = ""

        try:
            while True:
                time.sleep(1)

                current_url = page.url

                # Если URL изменился (кликнули на карточку)
                if current_url != last_url and '/firm/' in current_url:
                    last_url = current_url
                    time.sleep(1.5)  # Ждём загрузки

                    try:
                        # Название компании
                        name = None
                        name_selectors = [
                            'h1', '[class*="title"]', '[class*="name"]',
                            '[data-marker="firm-card-title"]'
                        ]
                        for sel in name_selectors:
                            el = page.query_selector(sel)
                            if el:
                                text = el.inner_text().strip()
                                if text and len(text) > 2 and len(text) < 200:
                                    name = text
                                    break

                        # Телефон
                        phone = None
                        phone_el = page.query_selector('a[href^="tel:"]')
                        if phone_el:
                            href = phone_el.get_attribute('href')
                            if href:
                                phone = re.sub(r'[^\d+]', '', href.replace('tel:', ''))
                                if phone.startswith('8') and len(phone) == 11:
                                    phone = '+7' + phone[1:]

                        # Проверяем сайт
                        has_site = False
                        site_el = page.query_selector('a[href^="http"]:not([href*="2gis"]):not([href*="vk.com"]):not([href*="instagram"])')
                        if site_el:
                            href = site_el.get_attribute('href') or ''
                            if href and not any(x in href.lower() for x in ['2gis', 'vk.com', 'instagram', 't.me', 'wa.me']):
                                has_site = True

                        # Сохраняем
                        if name and phone and phone not in seen:
                            if not has_site:
                                seen.add(phone)
                                leads.append({
                                    'name': name,
                                    'phone': phone,
                                })
                                print(f"  ✅ {name[:45]}")
                                print(f"     📞 {phone}")
                                print(f"     [{len(leads)} собрано]\n")
                            else:
                                print(f"  ⏭  {name[:45]} — есть сайт, пропускаю\n")

                    except Exception as e:
                        pass

                last_url = current_url

        except KeyboardInterrupt:
            pass
        except Exception:
            pass

    # Сохранение
    if leads:
        filename = f"leads_{datetime.now().strftime('%H%M')}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'phone'])
            writer.writeheader()
            writer.writerows(leads)

        print(f"\n{'='*55}")
        print(f"  ✅ СОХРАНЕНО: {len(leads)} лидов БЕЗ сайтов")
        print(f"  📁 Файл: {filename}")
        print(f"{'='*55}\n")

        print("Собранные контакты:")
        for i, lead in enumerate(leads, 1):
            print(f"  {i}. {lead['name'][:40]} | {lead['phone']}")
    else:
        print("\n❌ Ничего не собрано")


if __name__ == '__main__':
    main()
