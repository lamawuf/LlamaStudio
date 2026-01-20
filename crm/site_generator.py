#!/usr/bin/env python3
"""
Генератор портфолио-сайтов с 6 уникальными шаблонами
"""

import json
import os
import re
from pathlib import Path

# 6 разных шаблонов с уникальными цветовыми схемами
TEMPLATES = [
    {
        "name": "corporate",
        "dir": "corporate",
        "primary": "#1e3a5f",
        "primary_light": "#2d5a8a",
        "accent": "#c9a86c",
        "description": "Классический корпоративный"
    },
    {
        "name": "minimal",
        "dir": "minimal",
        "primary": "#0f766e",
        "primary_light": "#14b8a6",
        "accent": "#f59e0b",
        "description": "Минималистичный чистый"
    },
    {
        "name": "bold",
        "dir": "bold",
        "primary": "#7c3aed",
        "primary_light": "#8b5cf6",
        "accent": "#22d3ee",
        "description": "Смелый динамичный"
    },
    {
        "name": "premium",
        "dir": "premium",
        "primary": "#78350f",
        "primary_light": "#92400e",
        "accent": "#b45309",
        "description": "Премиальный элегантный"
    },
    {
        "name": "dark",
        "dir": "dark",
        "primary": "#0a0a0a",
        "primary_light": "#171717",
        "accent": "#10b981",
        "description": "Тёмный технологичный"
    },
    {
        "name": "warm",
        "dir": "warm",
        "primary": "#b91c1c",
        "primary_light": "#dc2626",
        "accent": "#f97316",
        "description": "Тёплый дружелюбный"
    }
]

# Варианты hero текстов
HERO_VARIANTS = [
    {"title": "Ремонт квартир под ключ", "subtitle": "Фиксированная цена в договоре. Гарантия 5 лет. Сдаём объекты точно в срок.", "badge": "Более 500 выполненных проектов"},
    {"title": "Качественный ремонт квартир", "subtitle": "От дизайн-проекта до финальной уборки. Работаем по договору с гарантией.", "badge": "12 лет опыта"},
    {"title": "Ремонт квартир с гарантией", "subtitle": "Прозрачные цены, поэтапная оплата, строгое соблюдение сроков.", "badge": "Гарантия 5 лет"},
    {"title": "Профессиональный ремонт", "subtitle": "Берём на себя все заботы: от закупки материалов до вывоза мусора.", "badge": "Работаем без предоплаты"},
    {"title": "Ремонт квартир любой сложности", "subtitle": "Косметический, капитальный, дизайнерский. Индивидуальный подход.", "badge": "Бесплатный выезд замерщика"},
    {"title": "Ваш ремонт — наша забота", "subtitle": "Делаем качественно, в срок и по фиксированной цене. Без сюрпризов.", "badge": "Честные цены без накруток"},
]

# Статистика варианты
STATS_VARIANTS = [
    [{"value": "12", "label": "лет на рынке"}, {"value": "500+", "label": "проектов"}, {"value": "5 лет", "label": "гарантия"}],
    [{"value": "8", "label": "лет опыта"}, {"value": "350+", "label": "объектов"}, {"value": "98%", "label": "довольных клиентов"}],
    [{"value": "15", "label": "лет работы"}, {"value": "1000+", "label": "ремонтов"}, {"value": "3 года", "label": "гарантия"}],
    [{"value": "10", "label": "лет в деле"}, {"value": "700+", "label": "квартир"}, {"value": "100%", "label": "в срок"}],
    [{"value": "7", "label": "лет практики"}, {"value": "400+", "label": "клиентов"}, {"value": "24/7", "label": "поддержка"}],
    [{"value": "20", "label": "мастеров"}, {"value": "600+", "label": "проектов"}, {"value": "0₽", "label": "предоплата"}],
]


def format_phone(phone_raw: str) -> str:
    """Форматирует телефон красиво"""
    digits = re.sub(r'[^\d]', '', phone_raw)
    if len(digits) == 11:
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    return phone_raw


def render_template(template_html: str, data: dict) -> str:
    """Рендерит Mustache-подобный шаблон"""

    html = template_html

    # Обрабатываем секции {{#stats}}...{{/stats}}
    stats_pattern = r'\{\{#stats\}\}(.*?)\{\{/stats\}\}'
    stats_match = re.search(stats_pattern, html, re.DOTALL)

    if stats_match and 'stats' in data:
        stats_template = stats_match.group(1)
        stats_html = ''
        for stat in data['stats']:
            item_html = stats_template
            item_html = item_html.replace('{{value}}', stat['value'])
            item_html = item_html.replace('{{label}}', stat['label'])
            stats_html += item_html
        html = re.sub(stats_pattern, stats_html, html, flags=re.DOTALL)

    # Простые замены
    replacements = {
        '{{company_name}}': data.get('company_name', 'Компания'),
        '{{phone}}': data.get('phone', '+7 (999) 123-45-67'),
        '{{phone_raw}}': data.get('phone_raw', '79991234567'),
        '{{city}}': data.get('city', 'Краснодар'),
        '{{primary}}': data.get('primary', '#1e3a5f'),
        '{{primary_light}}': data.get('primary_light', '#2d5a8a'),
        '{{accent}}': data.get('accent', '#c9a86c'),
        '{{hero_title}}': data.get('hero_title', 'Ремонт квартир'),
        '{{hero_subtitle}}': data.get('hero_subtitle', 'Качественно и в срок'),
        '{{badge}}': data.get('badge', 'Опыт работы'),
    }

    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    return html


def generate_site(company: dict, variant_idx: int, templates_base: Path, output_dir: Path):
    """Генерирует сайт для компании"""

    template = TEMPLATES[variant_idx % len(TEMPLATES)]
    hero = HERO_VARIANTS[variant_idx % len(HERO_VARIANTS)]
    stats = STATS_VARIANTS[variant_idx % len(STATS_VARIANTS)]

    # Получаем первый телефон
    phones = company.get('phones', '').split(',')
    first_phone = phones[0].strip() if phones else '+79999999999'
    phone_raw = re.sub(r'[^\d]', '', first_phone)

    # Данные для шаблона
    data = {
        'company_name': company.get('name', 'Компания'),
        'phone': format_phone(first_phone),
        'phone_raw': phone_raw,
        'city': 'Краснодар',
        'primary': template['primary'],
        'primary_light': template['primary_light'],
        'accent': template['accent'],
        'hero_title': hero['title'],
        'hero_subtitle': hero['subtitle'],
        'badge': hero['badge'],
        'stats': stats
    }

    # Читаем шаблон
    template_path = templates_base / template['dir'] / 'index.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        template_html = f.read()

    # Рендерим
    html = render_template(template_html, data)

    # Сохраняем
    site_dir = output_dir / f"site{variant_idx + 1}"
    site_dir.mkdir(exist_ok=True)

    with open(site_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(html)

    # Сохраняем конфиг
    config = {
        'company': company.get('name'),
        'template': template['name'],
        'template_description': template['description'],
        'colors': {
            'primary': template['primary'],
            'accent': template['accent']
        },
        'phone': data['phone']
    }

    with open(site_dir / 'config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    return {
        'name': company.get('name'),
        'template': template['name'],
        'description': template['description'],
        'phone': data['phone'],
        'site_dir': str(site_dir)
    }


def main():
    from app import app, db, Lead

    templates_base = Path('/Users/lama/Downloads/Apps/ClientFarmer/templates_base')
    output_dir = Path('/Users/lama/Downloads/Apps/ClientFarmer/portfolio_sites')
    output_dir.mkdir(exist_ok=True)

    with app.app_context():
        # Выбираем 6 компаний с WhatsApp
        companies = Lead.query.filter(
            Lead.social.ilike('%WhatsApp%'),
            Lead.portfolio_used == False
        ).limit(6).all()

        if len(companies) < 6:
            print(f"Найдено только {len(companies)} компаний с WhatsApp")
            more = Lead.query.filter(
                Lead.portfolio_used == False
            ).limit(6 - len(companies)).all()
            companies.extend(more)

        print(f"\n{'='*60}")
        print("  ГЕНЕРАЦИЯ ПОРТФОЛИО-САЙТОВ (6 УНИКАЛЬНЫХ ШАБЛОНОВ)")
        print(f"{'='*60}\n")

        results = []
        for i, company in enumerate(companies):
            company_data = {
                'name': company.name,
                'phones': company.phones,
                'social': company.social or ''
            }

            result = generate_site(company_data, i, templates_base, output_dir)
            results.append(result)

            # Помечаем как использованную
            company.portfolio_used = True

            print(f"  ✅ Site {i+1}: {result['name']}")
            print(f"     📐 Шаблон: {result['template']} ({result['description']})")
            print(f"     📞 {result['phone']}")
            print()

        db.session.commit()

        print(f"{'='*60}")
        print(f"  Создано {len(results)} сайтов в {output_dir}")
        print(f"{'='*60}\n")

        # Выводим сводку шаблонов
        print("  Использованные шаблоны:")
        for i, t in enumerate(TEMPLATES[:len(results)]):
            print(f"    {i+1}. {t['name']}: {t['description']}")
        print()


if __name__ == '__main__':
    main()
