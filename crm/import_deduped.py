#!/usr/bin/env python3
"""
Импорт CSV с дедупликацией - одна компания = одна строка
"""

import csv
import glob
from collections import defaultdict
from app import app, db, Lead, City, Category

def import_all():
    with app.app_context():
        # Получаем город и категорию
        krasnodar = City.query.filter_by(name='Краснодар').first()
        remont = Category.query.filter_by(name='Ремонт квартир').first()

        if not krasnodar or not remont:
            print("Ошибка: нет города или категории")
            return

        # Группируем по URL
        companies = defaultdict(lambda: {'phones': set(), 'social': '', 'name': ''})

        csv_files = glob.glob("leads*.csv")
        print(f"Найдено {len(csv_files)} CSV файлов")

        for csv_file in csv_files:
            print(f"  📁 {csv_file}")
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row.get('2gis_url', '')
                    phone = row.get('phone', '')
                    name = row.get('name', 'Компания')
                    social = row.get('social', '')

                    if not url and not phone:
                        continue

                    # Ключ - URL или телефон
                    key = url if url else phone

                    if phone:
                        companies[key]['phones'].add(phone)
                    if name and not companies[key]['name']:
                        companies[key]['name'] = name
                    if social and not companies[key]['social']:
                        companies[key]['social'] = social
                    if url:
                        companies[key]['url'] = url

        # Импортируем
        imported = 0
        for key, data in companies.items():
            phones = ', '.join(sorted(data['phones']))
            if not phones:
                continue

            url = data.get('url', '')
            # Пропускаем если URL пустой и уже есть такой
            if not url:
                url = None  # NULL вместо пустой строки для unique constraint

            lead = Lead(
                name=data['name'] or 'Компания',
                phones=phones,
                social=data['social'],
                url_2gis=url,
                city_id=krasnodar.id,
                category_id=remont.id,
                status='waiting',
                source='2gis'
            )
            db.session.add(lead)
            imported += 1

            # Коммитим по одному чтобы пропускать дубли
            try:
                db.session.commit()
            except:
                db.session.rollback()
                imported -= 1

        print(f"\n{'='*50}")
        print(f"  Импортировано компаний: {imported}")
        print(f"{'='*50}\n")

if __name__ == '__main__':
    import_all()
