#!/usr/bin/env python3
"""
Объединяет все CSV файлы в SQLite базу данных
"""

import csv
import sqlite3
import glob
from datetime import datetime

DB_PATH = "leads.db"

def init_db():
    """Создаём базу данных"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT UNIQUE,
            social TEXT,
            url_2gis TEXT,
            status TEXT DEFAULT 'new',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            called_at TIMESTAMP,
            result TEXT
        )
    ''')

    conn.commit()
    return conn

def merge_csvs():
    """Импортируем все CSV в базу"""
    conn = init_db()
    c = conn.cursor()

    csv_files = glob.glob("leads*.csv")

    total_imported = 0
    duplicates = 0

    for csv_file in csv_files:
        print(f"📁 Обрабатываю {csv_file}...")

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                phone = row.get('phone', '')
                if not phone:
                    continue

                name = row.get('name', 'Компания')
                social = row.get('social', '')
                url_2gis = row.get('2gis_url', '')

                try:
                    c.execute('''
                        INSERT INTO leads (name, phone, social, url_2gis)
                        VALUES (?, ?, ?, ?)
                    ''', (name, phone, social, url_2gis))
                    total_imported += 1
                except sqlite3.IntegrityError:
                    # Дубликат по телефону
                    duplicates += 1

    conn.commit()
    conn.close()

    print(f"\n{'='*50}")
    print(f"  Импортировано: {total_imported}")
    print(f"  Дубликатов: {duplicates}")
    print(f"  База данных: {DB_PATH}")
    print(f"{'='*50}\n")

if __name__ == '__main__':
    merge_csvs()
