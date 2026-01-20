#!/usr/bin/env python3
"""
РУЧНОЙ РЕЖИМ — самый надёжный

1. Открой 2GIS в обычном браузере
2. Найди "ремонт квартир", поставь фильтры
3. Прокрути ВСЮ страницу вниз (чтобы загрузились все)
4. Cmd+A (выделить всё), Cmd+C (копировать)
5. Запусти: python3 manual.py

Скрипт вытащит все телефоны из буфера.
"""

import csv
import re
import subprocess
from datetime import datetime


def get_clipboard():
    """Получить текст из буфера (macOS)"""
    result = subprocess.run(['pbpaste'], capture_output=True, text=True)
    return result.stdout


def extract_phones(text: str) -> list:
    """Вытащить все телефоны из текста"""

    # Паттерны телефонов
    patterns = [
        r'\+7\s*\(?\d{3}\)?\s*\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',  # +7 (999) 123-45-67
        r'8\s*\(?\d{3}\)?\s*\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',    # 8 (999) 123-45-67
        r'\+7\d{10}',  # +79991234567
        r'8\d{10}',    # 89991234567
    ]

    phones = set()
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Чистим телефон
            clean = re.sub(r'[^\d+]', '', match)
            if clean.startswith('8') and len(clean) == 11:
                clean = '+7' + clean[1:]
            if len(clean) >= 11:
                phones.add(clean)

    return list(phones)


def extract_companies(text: str) -> list:
    """Попытка извлечь пары название-телефон"""

    leads = []
    lines = text.split('\n')

    current_name = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Ищем телефон в строке
        phone_match = re.search(r'(\+7|8)[\s\-\(\)]*\d{3}[\s\-\(\)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}', line)

        if phone_match:
            phone = re.sub(r'[^\d+]', '', phone_match.group())
            if phone.startswith('8') and len(phone) == 11:
                phone = '+7' + phone[1:]

            leads.append({
                'name': current_name or 'Компания',
                'phone': phone
            })
            current_name = None

        # Потенциальное название компании
        elif len(line) > 3 and len(line) < 80:
            # Не служебные строки
            skip_words = ['отзыв', 'оценк', 'закрыт', 'открыт', 'ремонт помещ',
                         'реклама', 'рассчитать', 'филиал', 'краснодар', 'улица',
                         'фильтр', 'сортировка', 'места', 'рейтинг']
            if not any(w in line.lower() for w in skip_words):
                current_name = line

    return leads


def main():
    print(f"\n{'='*55}")
    print("  РУЧНОЙ ПАРСЕР")
    print(f"{'='*55}")
    print("""
  1. Открой 2GIS → "ремонт квартир" → фильтры
  2. Прокрути страницу ВНИЗ до конца
  3. Cmd+A → Cmd+C (скопируй всё)
  4. Вернись сюда — данные уже в буфере
""")
    print(f"{'='*55}\n")

    text = get_clipboard()

    if len(text) < 200:
        print("❌ Буфер пустой. Скопируй страницу 2GIS!")
        return

    print(f"📋 Получено {len(text)} символов\n")

    # Извлекаем
    leads = extract_companies(text)

    # Убираем дубликаты по телефону
    seen = set()
    unique = []
    for lead in leads:
        if lead['phone'] not in seen:
            seen.add(lead['phone'])
            unique.append(lead)

    if not unique:
        # Fallback — просто телефоны
        phones = extract_phones(text)
        unique = [{'name': f'Компания {i+1}', 'phone': p} for i, p in enumerate(phones)]

    if not unique:
        print("❌ Не нашёл телефонов. Попробуй скопировать ещё раз.")
        return

    # Сохраняем
    filename = f"leads_manual_{datetime.now().strftime('%H%M')}.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'phone'])
        writer.writeheader()
        writer.writerows(unique)

    print(f"✅ Найдено: {len(unique)} телефонов")
    print(f"📁 Файл: {filename}\n")

    print("Первые 10:")
    for lead in unique[:10]:
        print(f"  • {lead['name'][:35]} | {lead['phone']}")

    if len(unique) > 10:
        print(f"  ... и ещё {len(unique) - 10}")


if __name__ == '__main__':
    main()
