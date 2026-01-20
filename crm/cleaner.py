#!/usr/bin/env python3
"""
Чистильщик — убирает из CSV тех, у кого есть сайт.
Проходит по каждой ссылке 2GIS и проверяет.

Запуск: python3 cleaner.py leads_krasnodar_20260120_0729.csv
"""

import csv
import sys
import time
import re
from playwright.sync_api import sync_playwright


def has_website(page, url: str) -> bool:
    """Проверяет есть ли у компании сайт"""
    try:
        page.goto(url, timeout=15000)
        time.sleep(1.5)

        # Ищем ссылки на сайт
        content = page.content().lower()

        # Паттерны сайтов которые НЕ считаем (соцсети)
        skip_domains = ['2gis', 'vk.com', 'instagram', 't.me', 'wa.me',
                       'facebook', 'youtube', 'ok.ru', 'whatsapp', 'viber',
                       'yandex.ru/maps', 'google.com/maps']

        # Ищем ссылки
        all_links = page.locator('a[href^="http"]').all()

        for link in all_links:
            try:
                href = (link.get_attribute('href') or '').lower()

                # Пропускаем служебные
                if any(skip in href for skip in skip_domains):
                    continue

                # Проверяем текст ссылки - часто там написано "сайт" или домен
                text = link.inner_text().lower().strip()

                # Если текст похож на домен (xxx.ru, xxx.com)
                if re.match(r'^[a-zа-я0-9\-]+\.[a-zа-я]{2,}$', text):
                    return True

                # Или если в href есть нормальный домен
                if re.search(r'https?://[a-z0-9\-]+\.[a-z]{2,}', href):
                    if not any(skip in href for skip in skip_domains):
                        return True

            except:
                continue

        # Дополнительно ищем текст "Сайт:" или подобное
        if 'website' in content or '>сайт<' in content:
            return True

        return False

    except Exception as e:
        print(f"  ⚠️ Ошибка загрузки: {e}")
        return False  # При ошибке считаем что сайта нет


def clean_csv(input_file: str):
    """Чистит CSV от компаний с сайтами"""

    # Читаем входной файл
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"\n{'='*55}")
    print(f"  Чистильщик")
    print(f"{'='*55}")
    print(f"  Входной файл: {input_file}")
    print(f"  Всего записей: {len(rows)}")
    print(f"{'='*55}\n")

    if 'url' not in rows[0]:
        print("❌ В файле нет колонки 'url'. Нужен файл с URL компаний.")
        return

    clean_leads = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Без окна — быстрее
        page = browser.new_page()

        for i, row in enumerate(rows):
            name = row.get('name', 'Без имени')
            url = row.get('url', '')

            print(f"[{i+1}/{len(rows)}] {name[:40]}...", end=" ")

            if not url:
                print("⏭ нет URL")
                continue

            if has_website(page, url):
                print("❌ есть сайт")
            else:
                print("✅ БЕЗ сайта")
                clean_leads.append({
                    'name': row.get('name'),
                    'phone': row.get('phone'),
                })

        browser.close()

    # Сохраняем чистый файл
    output_file = input_file.replace('.csv', '_clean.csv')
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'phone'])
        writer.writeheader()
        writer.writerows(clean_leads)

    print(f"\n{'='*55}")
    print(f"  ✅ Очищено!")
    print(f"  Было: {len(rows)}")
    print(f"  Стало: {len(clean_leads)} (без сайтов)")
    print(f"  Файл: {output_file}")
    print(f"{'='*55}\n")


def main():
    if len(sys.argv) < 2:
        print("Использование: python3 cleaner.py <файл.csv>")
        return

    clean_csv(sys.argv[1])


if __name__ == '__main__':
    main()
