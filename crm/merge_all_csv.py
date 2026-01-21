#!/usr/bin/env python3
"""
Объединяет все CSV файлы в один мастер-файл с дедупликацией.

Правила:
1. Один клиент = одна строка (идентификация по 2GIS URL или по имени)
2. Несколько телефонов одного клиента - через запятую
3. Дедупликация по телефону
"""

import csv
import glob
import re
from collections import defaultdict


def normalize_phone(phone):
    """Нормализует телефон: 8XXXXXXXXXX -> +7XXXXXXXXXX"""
    if not phone:
        return None
    # Убираем всё кроме цифр и +
    phone = re.sub(r'[^\d+]', '', phone)
    # Убираем дублирующиеся +
    phone = re.sub(r'\++', '+', phone)
    # 8 -> +7
    if phone.startswith('8') and len(phone) == 11:
        phone = '+7' + phone[1:]
    # 7 без + -> +7
    if phone.startswith('7') and len(phone) == 11:
        phone = '+' + phone
    return phone if phone else None


def extract_firm_id(url):
    """Извлекает ID фирмы из 2GIS URL"""
    if not url:
        return None
    match = re.search(r'firm/(\d+)', url)
    return match.group(1) if match else None


def merge_csvs():
    """Объединяет все CSV в один мастер-файл"""

    csv_files = sorted(glob.glob("/Users/lama/Downloads/Apps/LlamaStudio/crm/leads*.csv"))

    # Хранилище: firm_id -> данные компании
    companies = {}
    # Для компаний без URL - по имени
    companies_by_name = {}
    # Все телефоны которые уже видели
    seen_phones = set()

    print(f"Найдено CSV файлов: {len(csv_files)}")

    for csv_file in csv_files:
        print(f"\n📄 Обрабатываю: {csv_file}")

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                name = row.get('name', '').strip()
                phone_raw = row.get('phone', '').strip()
                social = row.get('social', '').strip()

                # URL может быть в разных полях
                url = row.get('2gis_url', '') or row.get('url', '')
                url = url.strip()

                phone = normalize_phone(phone_raw)
                if not phone:
                    continue

                # Пропускаем уже виденные телефоны
                if phone in seen_phones:
                    continue
                seen_phones.add(phone)

                firm_id = extract_firm_id(url)

                # Город из CSV
                city = row.get('city', '').strip()

                if firm_id:
                    # Компания с 2GIS URL
                    if firm_id in companies:
                        # Добавляем телефон к существующей компании
                        existing_phones = companies[firm_id]['phones'].split(', ')
                        if phone not in existing_phones:
                            companies[firm_id]['phones'] += f', {phone}'
                        # Обновляем social если пустой
                        if social and not companies[firm_id]['social']:
                            companies[firm_id]['social'] = social
                    else:
                        companies[firm_id] = {
                            'name': name,
                            'phones': phone,
                            'social': social,
                            'url_2gis': url,
                            'city': city
                        }
                else:
                    # Компания без URL - группируем по имени
                    if name in companies_by_name:
                        existing_phones = companies_by_name[name]['phones'].split(', ')
                        if phone not in existing_phones:
                            companies_by_name[name]['phones'] += f', {phone}'
                    else:
                        companies_by_name[name] = {
                            'name': name,
                            'phones': phone,
                            'social': social,
                            'url_2gis': '',
                            'city': city
                        }

    # Объединяем результаты
    all_companies = list(companies.values()) + list(companies_by_name.values())

    # Сортируем по имени
    all_companies.sort(key=lambda x: x['name'])

    # Записываем мастер-файл
    output_file = "/Users/lama/Downloads/Apps/LlamaStudio/crm/leads_master.csv"

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'phones', 'social', 'url_2gis', 'city'])
        writer.writeheader()
        writer.writerows(all_companies)

    # Статистика
    total_phones = sum(len(c['phones'].split(', ')) for c in all_companies)

    print(f"\n{'='*50}")
    print(f"✅ ГОТОВО!")
    print(f"   Уникальных компаний: {len(all_companies)}")
    print(f"   Уникальных телефонов: {total_phones}")
    print(f"   Мастер-файл: {output_file}")
    print(f"{'='*50}\n")

    return output_file


if __name__ == '__main__':
    merge_csvs()
