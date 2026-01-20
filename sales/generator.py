#!/usr/bin/env python3
"""
КП Генератор — создаёт персонализированные сообщения из лидов
Использование: python generator.py leads.csv
"""

import csv
import sys
import os
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"

# Портфолио для разных ниш
PORTFOLIO_LINKS = {
    "ремонт квартир": "https://privozzz-remont.vercel.app",
    "ремонт": "https://privozzz-remont.vercel.app",
    "автосервис": "https://privozzz-remont.vercel.app",  # TODO: добавить автосервис
    "салон красоты": "https://privozzz-remont.vercel.app",  # TODO: добавить салон
    "default": "https://privozzz-remont.vercel.app"
}


def load_template(template_name: str) -> str:
    """Загрузить шаблон по имени"""
    template_path = TEMPLATES_DIR / f"{template_name}.txt"
    if not template_path.exists():
        print(f"Шаблон не найден: {template_path}")
        sys.exit(1)
    return template_path.read_text(encoding="utf-8")


def get_portfolio_link(category: str) -> str:
    """Получить ссылку на портфолио по нише"""
    category_lower = category.lower() if category else ""
    for key, link in PORTFOLIO_LINKS.items():
        if key in category_lower:
            return link
    return PORTFOLIO_LINKS["default"]


def generate_message(lead: dict, template_name: str = "cold_first") -> str:
    """Генерация сообщения для лида"""
    template = load_template(template_name)

    # Подготовка данных
    name = lead.get("name", "").strip()
    phone = lead.get("phone", "").strip()
    city = lead.get("city", "").strip()
    category = lead.get("category", "").strip()

    # Получаем ссылку на портфолио
    portfolio_link = get_portfolio_link(category)

    # Форматируем телефон для WhatsApp
    phone_clean = "".join(filter(str.isdigit, phone))
    if phone_clean.startswith("8"):
        phone_clean = "7" + phone_clean[1:]
    whatsapp_link = f"https://wa.me/{phone_clean}"

    # Заменяем плейсхолдеры
    message = template.format(
        name=name,
        phone=phone,
        city=city,
        category=category,
        portfolio_link=portfolio_link,
        whatsapp_link=whatsapp_link,
        analysis=""  # Для шаблона with_site_analysis
    )

    return message


def process_leads(csv_path: str, template_name: str = "cold_first", limit: int = None):
    """Обработка CSV с лидами"""
    if not os.path.exists(csv_path):
        print(f"Файл не найден: {csv_path}")
        sys.exit(1)

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        leads = list(reader)

    if limit:
        leads = leads[:limit]

    print(f"\n{'='*60}")
    print(f"КП Генератор — LlamaStudio")
    print(f"Лидов: {len(leads)}")
    print(f"Шаблон: {template_name}")
    print(f"{'='*60}\n")

    results = []

    for i, lead in enumerate(leads, 1):
        message = generate_message(lead, template_name)
        phone = lead.get("phone", "")
        name = lead.get("name", "")

        # Форматируем телефон для WhatsApp
        phone_clean = "".join(filter(str.isdigit, phone))
        if phone_clean.startswith("8"):
            phone_clean = "7" + phone_clean[1:]

        results.append({
            "name": name,
            "phone": phone,
            "whatsapp": f"https://wa.me/{phone_clean}",
            "message": message
        })

        print(f"--- Лид #{i}: {name} ---")
        print(f"WhatsApp: https://wa.me/{phone_clean}")
        print(f"\n{message}")
        print(f"\n{'='*60}\n")

    # Сохраняем в файл
    output_path = csv_path.replace(".csv", "_messages.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(f"=== {r['name']} ===\n")
            f.write(f"WhatsApp: {r['whatsapp']}\n\n")
            f.write(r['message'])
            f.write(f"\n\n{'='*60}\n\n")

    print(f"Сохранено в: {output_path}")

    return results


def main():
    if len(sys.argv) < 2:
        print("Использование: python generator.py <leads.csv> [template_name] [limit]")
        print("\nШаблоны:")
        print("  cold_first      — первое холодное сообщение (по умолчанию)")
        print("  cold_short      — короткое сообщение")
        print("  follow_up       — повторное сообщение")
        print("  with_site_analysis — для тех у кого есть сайт")
        print("\nПример: python generator.py leads.csv cold_short 10")
        sys.exit(1)

    csv_path = sys.argv[1]
    template_name = sys.argv[2] if len(sys.argv) > 2 else "cold_first"
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else None

    process_leads(csv_path, template_name, limit)


if __name__ == "__main__":
    main()
