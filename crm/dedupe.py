#!/usr/bin/env python3
"""
Объединяет дубликаты компаний по URL 2GIS
Все телефоны одной компании в одну строку
"""

import sqlite3
from collections import defaultdict

def dedupe():
    conn = sqlite3.connect('instance/leads.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Получаем все лиды
    c.execute("SELECT * FROM leads ORDER BY id")
    leads = c.fetchall()

    # Группируем по URL (или по имени если URL нет)
    companies = defaultdict(lambda: {'phones': set(), 'data': None})

    for lead in leads:
        # Ключ - URL или имя
        key = lead['url_2gis'] or lead['name']
        if not key:
            continue

        # Добавляем телефон
        if lead['phones']:
            for phone in lead['phones'].split(','):
                phone = phone.strip()
                if phone:
                    companies[key]['phones'].add(phone)

        # Сохраняем данные первого лида
        if companies[key]['data'] is None:
            companies[key]['data'] = dict(lead)

    # Очищаем таблицу
    c.execute("DELETE FROM leads")

    # Вставляем объединённые данные
    for key, company in companies.items():
        data = company['data']
        phones = ', '.join(sorted(company['phones']))

        c.execute('''
            INSERT INTO leads (name, phones, social, url_2gis, city_id, category_id, status, source, notes, result)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['name'],
            phones,
            data['social'],
            data['url_2gis'],
            data['city_id'],
            data['category_id'],
            data['status'],
            data.get('source', '2gis'),
            data['notes'],
            data['result']
        ))

    conn.commit()

    print(f"\n{'='*50}")
    print(f"  Было лидов: {len(leads)}")
    print(f"  Стало компаний: {len(companies)}")
    print(f"  Убрано дублей: {len(leads) - len(companies)}")
    print(f"{'='*50}\n")

    conn.close()

if __name__ == '__main__':
    dedupe()
