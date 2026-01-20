#!/usr/bin/env python3
"""
ClientFarmer — Парсер буфера обмена
1. Открой 2GIS, поищи "ремонт квартир краснодар"
2. Скролль список слева
3. Cmd+A, Cmd+C (выдели и скопируй всю страницу)
4. Запусти: python3 parser.py
"""

import csv
import re
import subprocess
import sys
from datetime import datetime


def get_clipboard():
    """Получить текст из буфера обмена (macOS)"""
    result = subprocess.run(['pbpaste'], capture_output=True, text=True)
    return result.stdout


def parse_2gis_text(text: str) -> list:
    """Парсинг текста из 2GIS"""
    leads = []

    # Разбиваем на блоки (каждая компания обычно отделена)
    lines = text.split('\n')

    current_company = {}

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # Ищем телефоны (формат +7, 8-, итд)
        phone_match = re.search(r'(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}', line)
        if phone_match:
            phone = re.sub(r'[^\d+]', '', phone_match.group())
            # Нормализуем к +7
            if phone.startswith('8') and len(phone) == 11:
                phone = '+7' + phone[1:]
            current_company['phone'] = phone

        # Ищем сайты
        site_match = re.search(r'(https?://)?([a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,}', line.lower())
        if site_match:
            site = site_match.group()
            # Игнорируем соцсети
            if 'vk.com' not in site and 'instagram' not in site and 't.me' not in site and '2gis' not in site:
                current_company['has_site'] = True

        # Если строка похожа на название компании (не содержит цифр в начале, не слишком длинная)
        if len(line) > 3 and len(line) < 100 and not line[0].isdigit():
            if not any(x in line.lower() for x in ['отзыв', 'рейтинг', 'открыто', 'закрыто', 'часов', 'http', 'www', '.ru', '.com']):
                if 'name' not in current_company:
                    current_company['name'] = line

        # Если нашли и имя и телефон — сохраняем
        if 'name' in current_company and 'phone' in current_company:
            if not current_company.get('has_site'):  # Только БЕЗ сайта
                if not any(l['phone'] == current_company['phone'] for l in leads):
                    leads.append({
                        'name': current_company['name'],
                        'phone': current_company['phone'],
                    })
            current_company = {}

    return leads


def parse_yandex_text(text: str) -> list:
    """Парсинг текста из Яндекс.Карт"""
    # Похожая логика
    return parse_2gis_text(text)  # Формат примерно одинаковый


def main():
    print("\n" + "="*50)
    print("ClientFarmer — Парсер буфера")
    print("="*50)

    # Получаем текст из буфера
    text = get_clipboard()

    if len(text) < 100:
        print("\n❌ Буфер пустой или слишком мало текста!")
        print("\nИнструкция:")
        print("1. Открой https://2gis.ru")
        print("2. Найди 'ремонт квартир краснодар'")
        print("3. Скролль список компаний слева")
        print("4. Нажми Cmd+A (выделить всё)")
        print("5. Нажми Cmd+C (копировать)")
        print("6. Запусти этот скрипт снова")
        return

    print(f"\n📋 Получено {len(text)} символов из буфера")
    print("🔍 Парсинг...")

    leads = parse_2gis_text(text)

    if not leads:
        print("\n❌ Не удалось найти лиды. Попробуй:")
        print("   - Скроллить больше")
        print("   - Копировать именно список компаний")
        return

    # Сохраняем
    filename = f"leads_{datetime.now().strftime('%H%M')}.csv"

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'phone'])
        writer.writeheader()
        writer.writerows(leads)

    print(f"\n✅ ГОТОВО: {len(leads)} лидов БЕЗ сайта")
    print(f"📁 Файл: {filename}")
    print("\n" + "="*50)

    # Показываем первые 5
    print("\nПервые лиды:")
    for lead in leads[:5]:
        print(f"  • {lead['name'][:40]}: {lead['phone']}")
    if len(leads) > 5:
        print(f"  ... и ещё {len(leads) - 5}")


if __name__ == '__main__':
    main()
