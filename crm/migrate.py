#!/usr/bin/env python3
"""
Миграция лидов из старой SQLite в новую схему
"""

import sqlite3
from app import app, db, Lead, City, Category

def migrate():
    """Импортируем лиды из старой БД"""

    # Подключаемся к старой базе
    old_conn = sqlite3.connect('leads.db')
    old_conn.row_factory = sqlite3.Row
    cursor = old_conn.cursor()

    with app.app_context():
        # Получаем город Краснодар и категорию Ремонт квартир
        krasnodar = City.query.filter_by(name='Краснодар').first()
        remont = Category.query.filter_by(name='Ремонт квартир').first()

        if not krasnodar or not remont:
            print("Сначала запусти app.py для создания базовых данных")
            return

        # Читаем старые лиды
        cursor.execute("SELECT * FROM leads")
        old_leads = cursor.fetchall()

        imported = 0
        skipped = 0

        for row in old_leads:
            # Проверяем, нет ли уже такого телефона
            existing = Lead.query.filter_by(phone=row['phone']).first()
            if existing:
                skipped += 1
                continue

            lead = Lead(
                name=row['name'],
                phone=row['phone'],
                social=row['social'],
                url_2gis=row['url_2gis'],
                city_id=krasnodar.id,
                category_id=remont.id,
                status=row['status'] or 'new',
                notes=row['notes'],
                result=row['result'],
                source='2gis'
            )
            db.session.add(lead)
            imported += 1

        db.session.commit()

        print(f"\n{'='*50}")
        print(f"  Импортировано: {imported}")
        print(f"  Пропущено (дубликаты): {skipped}")
        print(f"{'='*50}\n")

    old_conn.close()

if __name__ == '__main__':
    migrate()
