#!/usr/bin/env python3
"""
ClientFarmer — Полуавтоматический сборщик
Открывает браузер, ты скроллишь — скрипт собирает.

Запуск: python3 collector.py "краснодар" "ремонт квартир"
"""

import csv
import sys
import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright


def collect_leads(city: str, query: str):
    """Открываем браузер, юзер скроллит, мы собираем"""

    leads = []
    seen_phones = set()

    print(f"\n{'='*50}")
    print("ClientFarmer — Сборщик")
    print(f"{'='*50}")
    print(f"\n🌐 Открываю браузер...")
    print("📋 Твоя задача: скроллить список и кликать на карточки")
    print("⏹  Когда закончишь — просто закрой браузер")
    print(f"{'='*50}\n")

    with sync_playwright() as p:
        # ВИДИМЫЙ браузер
        browser = p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        context = browser.new_context(
            viewport=None,  # Максимальный размер
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = context.new_page()

        # Открываем 2GIS
        url = f"https://2gis.ru/{city}/search/{query.replace(' ', '%20')}"
        page.goto(url)

        print("✅ Браузер открыт. Скролль список слева!")
        print("   Скрипт автоматически собирает данные каждые 5 сек\n")

        try:
            while True:
                time.sleep(5)

                # Пытаемся собрать данные со страницы
                try:
                    # Получаем весь текст страницы
                    content = page.content()

                    # Ищем телефоны
                    phones = re.findall(r'tel:(\+?\d[\d\s\-\(\)]{9,})', content)

                    for phone in phones:
                        clean_phone = re.sub(r'[^\d+]', '', phone)
                        if clean_phone.startswith('8') and len(clean_phone) == 11:
                            clean_phone = '+7' + clean_phone[1:]

                        if clean_phone not in seen_phones and len(clean_phone) >= 11:
                            seen_phones.add(clean_phone)

                            # Пытаемся найти название рядом с телефоном
                            # Упрощённо берём как "Компания N"
                            leads.append({
                                'phone': clean_phone,
                                'name': f'Компания #{len(leads)+1}',
                                'query': query,
                                'city': city
                            })

                    if leads:
                        print(f"\r📊 Собрано: {len(leads)} телефонов", end="", flush=True)

                except Exception:
                    pass

        except KeyboardInterrupt:
            pass
        except Exception:
            pass  # Браузер закрыт

    # Сохраняем результат
    if leads:
        filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'phone', 'query', 'city'])
            writer.writeheader()
            writer.writerows(leads)

        print(f"\n\n{'='*50}")
        print(f"✅ СОХРАНЕНО: {len(leads)} контактов")
        print(f"📁 Файл: {filename}")
        print(f"{'='*50}")
    else:
        print("\n\n❌ Ничего не собрано")


def main():
    if len(sys.argv) < 3:
        # Дефолтные значения
        city = "krasnodar"
        query = "ремонт квартир"
        print(f"Использую по умолчанию: {city}, {query}")
    else:
        city = sys.argv[1]
        query = sys.argv[2]

    collect_leads(city, query)


if __name__ == '__main__':
    main()
