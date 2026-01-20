#!/usr/bin/env python3
"""
Скрипт для обогащения существующих лидов соцсетями из 2GIS.
Проходит по всем лидам с url_2gis и обновляет поле social.

Использование:
    python enrich_socials.py              # Обновить все лиды без соцсетей
    python enrich_socials.py --all        # Обновить ВСЕ лиды (перезаписать соцсети)
    python enrich_socials.py --dry-run    # Тестовый режим (без записи в БД)
"""

import os
import re
import sys
import time
import random
import requests

# Настройки
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
}

API_KEY = 'rurbbn3446'  # Публичный ключ 2GIS


def get_socials_from_2gis(firm_id: str) -> dict:
    """Получает соцсети компании по ID из 2GIS API"""
    url = f"https://catalog.api.2gis.com/3.0/items/byid"
    params = {
        'id': firm_id,
        'fields': 'items.contact_groups',
        'key': API_KEY
    }

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = resp.json()

        items = data.get('result', {}).get('items', [])
        if not items:
            return {'social': None, 'phones': None}

        item = items[0]
        socials = []
        phones = []

        contacts = item.get('contact_groups', [])
        for group in contacts:
            for contact in group.get('contacts', []):
                contact_type = contact.get('type', '')
                contact_value = contact.get('value', '')

                # Телефоны
                if contact_type == 'phone':
                    phones.append(contact_value)

                # Соцсети и мессенджеры
                if contact_type == 'whatsapp':
                    socials.append('WhatsApp')
                elif contact_type == 'telegram':
                    socials.append('Telegram')
                elif contact_type == 'viber':
                    socials.append('Viber')
                elif contact_type == 'vkontakte':
                    socials.append('VK')
                elif contact_type == 'instagram':
                    socials.append('Instagram')
                elif contact_type == 'youtube':
                    socials.append('YouTube')
                elif contact_type == 'facebook':
                    socials.append('Facebook')
                elif contact_type == 'odnoklassniki':
                    socials.append('OK')

        return {
            'social': ', '.join(sorted(set(socials))) if socials else None,
            'phones': ', '.join(phones) if phones else None
        }

    except Exception as e:
        print(f"    Ошибка API: {e}")
        return {'social': None, 'phones': None}


def extract_firm_id(url_2gis: str) -> str:
    """Извлекает ID фирмы из URL 2GIS"""
    if not url_2gis:
        return None

    # Формат: https://2gis.ru/krasnodar/firm/70000001012345678
    # или: https://2gis.ru/firm/70000001012345678
    match = re.search(r'/firm/(\d+)', url_2gis)
    return match.group(1) if match else None


def main():
    # Импортируем Flask app для доступа к БД
    from app import app, db, Lead

    dry_run = '--dry-run' in sys.argv
    update_all = '--all' in sys.argv

    print("=" * 60)
    print("ENRICH SOCIALS — Обогащение лидов соцсетями из 2GIS")
    print("=" * 60)
    if dry_run:
        print("РЕЖИМ: Тестовый (без записи в БД)")
    if update_all:
        print("РЕЖИМ: Обновить ВСЕ лиды")
    print()

    with app.app_context():
        # Получаем лидов для обновления
        if update_all:
            leads = Lead.query.filter(Lead.url_2gis.isnot(None)).all()
        else:
            leads = Lead.query.filter(
                Lead.url_2gis.isnot(None),
                (Lead.social.is_(None) | (Lead.social == ''))
            ).all()

        print(f"Найдено лидов для обработки: {len(leads)}")
        print()

        updated = 0
        skipped = 0
        errors = 0

        for i, lead in enumerate(leads, 1):
            print(f"[{i}/{len(leads)}] {lead.name}")

            firm_id = extract_firm_id(lead.url_2gis)
            if not firm_id:
                print(f"    Пропуск: не удалось извлечь ID из {lead.url_2gis}")
                skipped += 1
                continue

            # Запрос к API
            result = get_socials_from_2gis(firm_id)

            if result['social']:
                print(f"    Соцсети: {result['social']}")
                if not dry_run:
                    lead.social = result['social']
                    db.session.commit()
                updated += 1
            else:
                print(f"    Соцсети не найдены")
                skipped += 1

            # Пауза чтобы не забанили
            time.sleep(random.uniform(0.3, 0.7))

        print()
        print("=" * 60)
        print(f"ГОТОВО!")
        print(f"  Обновлено: {updated}")
        print(f"  Пропущено: {skipped}")
        print(f"  Ошибок: {errors}")
        print("=" * 60)


if __name__ == '__main__':
    main()
