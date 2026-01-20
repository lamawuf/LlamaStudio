#!/usr/bin/env python3
"""
Импорт CSV в PostgreSQL с ЖЁСТКОЙ дедупликацией
- Проверяет по телефону И по URL
- Не добавляет если уже есть в базе
"""

import csv
import glob
import os
from app import app, db, Lead, City, Category


def import_csv(csv_file=None):
    """Импорт одного или всех CSV файлов"""

    with app.app_context():
        # Получаем город и категорию
        krasnodar = City.query.filter_by(name='Краснодар').first()
        remont = Category.query.filter_by(name='Ремонт квартир').first()

        if not krasnodar:
            krasnodar = City(name='Краснодар')
            db.session.add(krasnodar)
            db.session.commit()

        if not remont:
            remont = Category(name='Ремонт квартир')
            db.session.add(remont)
            db.session.commit()

        # Загружаем существующие телефоны и URL из базы
        existing_phones = set()
        existing_urls = set()

        all_leads = Lead.query.all()
        for lead in all_leads:
            if lead.phones:
                for phone in lead.phones.split(','):
                    existing_phones.add(phone.strip())
            if lead.url_2gis:
                existing_urls.add(lead.url_2gis)

        print(f"📊 В базе уже: {len(existing_phones)} телефонов, {len(existing_urls)} URL\n")

        # Какие файлы импортировать
        if csv_file:
            csv_files = [csv_file]
        else:
            csv_files = sorted(glob.glob("leads*.csv"))

        print(f"📁 Файлов для импорта: {len(csv_files)}")

        total_imported = 0
        total_skipped = 0
        total_rows = 0

        for fname in csv_files:
            if not os.path.exists(fname):
                print(f"  ⚠️ Файл не найден: {fname}")
                continue

            print(f"\n{'─'*50}")
            print(f"📄 {fname}")

            imported = 0
            skipped = 0

            with open(fname, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    total_rows += 1
                    phone = row.get('phone', '').strip()
                    url = row.get('2gis_url', '').strip()
                    name = row.get('name', 'Компания').strip()
                    social = row.get('social', '').strip()

                    if not phone:
                        skipped += 1
                        continue

                    # ПРОВЕРКА ДУБЛИКАТА
                    is_duplicate = False

                    # По телефону
                    if phone in existing_phones:
                        is_duplicate = True

                    # По URL
                    if url and url in existing_urls:
                        is_duplicate = True

                    if is_duplicate:
                        skipped += 1
                        continue

                    # Добавляем в базу
                    lead = Lead(
                        name=name,
                        phones=phone,
                        social=social,
                        url_2gis=url if url else None,
                        city_id=krasnodar.id,
                        category_id=remont.id,
                        status='waiting',
                        source='2gis'
                    )

                    try:
                        db.session.add(lead)
                        db.session.commit()

                        # Добавляем в set чтобы не добавить повторно из этого же файла
                        existing_phones.add(phone)
                        if url:
                            existing_urls.add(url)

                        imported += 1

                    except Exception as e:
                        db.session.rollback()
                        skipped += 1

            print(f"   ✅ Импортировано: {imported}")
            print(f"   ⏭️  Пропущено (дубли): {skipped}")

            total_imported += imported
            total_skipped += skipped

        print(f"\n{'='*50}")
        print(f"  📊 ИТОГО")
        print(f"  Строк в CSV: {total_rows}")
        print(f"  Импортировано: {total_imported}")
        print(f"  Пропущено: {total_skipped}")
        print(f"{'='*50}\n")

        return total_imported


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        # Импорт конкретного файла
        import_csv(sys.argv[1])
    else:
        # Импорт всех leads*.csv
        import_csv()
