#!/usr/bin/env python3
"""
Импорт leads_master.csv в PostgreSQL (Railway)

- Добавляет только НОВЫХ лидов (по url_2gis)
- Создаёт города если их нет
- Не трогает существующих лидов

Запуск локально: DATABASE_URL=... python3 import_to_db.py
Или на Railway: python3 import_to_db.py (DATABASE_URL из env)
"""

import csv
import os
import sys

# Добавляем текущую директорию для импорта app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Lead, City, Category


def normalize_city_name(city_slug: str) -> str:
    """Преобразует slug города в нормальное название"""
    city_names = {
        'krasnodar': 'Краснодар',
        'moscow': 'Москва',
        'sochi': 'Сочи',
        'novorossiysk': 'Новороссийск',
        'anapa': 'Анапа',
        'gelendzhik': 'Геленджик',
        'tuapse': 'Туапсе',
        'slavyansk-na-kubani': 'Славянск-на-Кубани',
        'rostov-na-donu': 'Ростов-на-Дону',
        'voronezh': 'Воронеж',
        'volgograd': 'Волгоград',
        'saratov': 'Саратов',
        'samara': 'Самара',
        'kazan': 'Казань',
        'ekaterinburg': 'Екатеринбург',
        'chelyabinsk': 'Челябинск',
        'novosibirsk': 'Новосибирск',
        'krasnoyarsk': 'Красноярск',
        'omsk': 'Омск',
        'ufa': 'Уфа',
        'perm': 'Пермь',
        'nizhny-novgorod': 'Нижний Новгород',
        'kaliningrad': 'Калининград',
        'tyumen': 'Тюмень',
        'irkutsk': 'Иркутск',
        'vladivostok': 'Владивосток',
        'khabarovsk': 'Хабаровск',
        'barnaul': 'Барнаул',
        'tomsk': 'Томск',
        'kemerovo': 'Кемерово',
        'orenburg': 'Оренбург',
        'ryazan': 'Рязань',
        'penza': 'Пенза',
        'lipetsk': 'Липецк',
        'tula': 'Тула',
        'kirov': 'Киров',
        'cheboksary': 'Чебоксары',
        'kaluga': 'Калуга',
        'bryansk': 'Брянск',
        'ivanovo': 'Иваново',
        'vladimir': 'Владимир',
        'smolensk': 'Смоленск',
        'kursk': 'Курск',
        'tver': 'Тверь',
        'belgorod': 'Белгород',
        'orel': 'Орёл',
        'tambov': 'Тамбов',
        'kostroma': 'Кострома',
        'vologda': 'Вологда',
        'murmansk': 'Мурманск',
        'petrozavodsk': 'Петрозаводск',
        'syktyvkar': 'Сыктывкар',
        'arkhangelsk': 'Архангельск',
        'pskov': 'Псков',
        'yaroslavl': 'Ярославль',
        'izhevsk': 'Ижевск',
        'ulyanovsk': 'Ульяновск',
        'astrakhan': 'Астрахань',
        'makhachkala': 'Махачкала',
        'vladikavkaz': 'Владикавказ',
        'nalchik': 'Нальчик',
        'stavropol': 'Ставрополь',
        'surgut': 'Сургут',
        'nizhnevartovsk': 'Нижневартовск',
        'magnitogorsk': 'Магнитогорск',
        'zlatoust': 'Златоуст',
        'miass': 'Миасс',
        'kurgan': 'Курган',
        'cherepovets': 'Череповец',
        'rybinsk': 'Рыбинск',
        'taganrog': 'Таганрог',
        'shakhty': 'Шахты',
        'novokuznetsk': 'Новокузнецк',
        'prokopevsk': 'Прокопьевск',
        'biysk': 'Бийск',
        'rubtsovsk': 'Рубцовск',
        'angarsk': 'Ангарск',
        'bratsk': 'Братск',
        'yakutsk': 'Якутск',
        'chita': 'Чита',
        'blagoveshchensk': 'Благовещенск',
        'abakan': 'Абакан',
        'norilsk': 'Норильск',
        'dzerzhinsk': 'Дзержинск',
        'balakovo': 'Балаково',
        'engels': 'Энгельс',
        'syzran': 'Сызрань',
        'orsk': 'Орск',
        'sterlitamak': 'Стерлитамак',
        'neftekamsk': 'Нефтекамск',
        'severodvinsk': 'Северодвинск',
        'kovrov': 'Ковров',
        'berezniki': 'Березники',
    }

    # Если есть в словаре — возвращаем
    if city_slug.lower() in city_names:
        return city_names[city_slug.lower()]

    # Иначе капитализируем slug
    return city_slug.replace('-', ' ').title()


def import_csv(csv_path: str, category_name: str = 'Ремонт квартир'):
    """Импортирует CSV в базу данных"""

    with app.app_context():
        # Получаем или создаём категорию
        category = Category.query.filter_by(name=category_name).first()
        if not category:
            category = Category(name=category_name)
            db.session.add(category)
            db.session.commit()
            print(f"✅ Создана категория: {category_name}")

        # Кэш городов
        city_cache = {}
        for city in City.query.all():
            city_cache[city.name.lower()] = city

        # Существующие URL для дедупликации
        existing_urls = set(
            url for (url,) in db.session.query(Lead.url_2gis).filter(Lead.url_2gis.isnot(None)).all()
        )
        print(f"📊 В базе уже {len(existing_urls)} лидов с URL")

        # Читаем CSV
        added = 0
        skipped = 0

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                url_2gis = row.get('url_2gis', '').strip()

                # Пропускаем если уже есть
                if url_2gis and url_2gis in existing_urls:
                    skipped += 1
                    continue

                # Город
                city_slug = row.get('city', '').strip()
                city_name = normalize_city_name(city_slug) if city_slug else 'Краснодар'

                # Получаем или создаём город
                city = city_cache.get(city_name.lower())
                if not city:
                    city = City(name=city_name)
                    db.session.add(city)
                    db.session.flush()  # Чтобы получить id
                    city_cache[city_name.lower()] = city
                    print(f"  + Новый город: {city_name}")

                # Создаём лида
                lead = Lead(
                    name=row.get('name', '').strip(),
                    phones=row.get('phones', '').strip(),
                    social=row.get('social', '').strip(),
                    url_2gis=url_2gis if url_2gis else None,
                    city_id=city.id,
                    category_id=category.id,
                    status='waiting',
                    source='2gis'
                )
                db.session.add(lead)
                existing_urls.add(url_2gis)
                added += 1

                # Коммитим батчами
                if added % 500 == 0:
                    db.session.commit()
                    print(f"  ... добавлено {added}")

        db.session.commit()

        print(f"\n{'='*50}")
        print(f"✅ ИМПОРТ ЗАВЕРШЁН")
        print(f"   Добавлено: {added}")
        print(f"   Пропущено (дубли): {skipped}")
        print(f"   Всего в базе: {Lead.query.count()}")
        print(f"{'='*50}\n")


if __name__ == '__main__':
    csv_path = os.path.join(os.path.dirname(__file__), 'leads_master.csv')

    if not os.path.exists(csv_path):
        print(f"❌ Файл не найден: {csv_path}")
        print("   Сначала запусти: python3 merge_all_csv.py")
        sys.exit(1)

    print(f"\n📁 Импорт из: {csv_path}")
    print(f"🔗 База: {os.environ.get('DATABASE_URL', 'SQLite (локально)')[:50]}...")
    print()

    import_csv(csv_path)
