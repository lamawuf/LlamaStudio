#!/usr/bin/env python3
"""
Рандомизатор сообщений — генерирует уникальные КП из блоков
Каждое сообщение уникально, но смысл один.
"""

import random
import csv
import sys

# === БЛОКИ СООБЩЕНИЙ ===

GREETINGS = [
    "Добрый день!",
    "Здравствуйте!",
    "Приветствую!",
    "Добрый день!",
    "Доброго времени!",
]

INTROS = [
    "Делаю сайты для {category}.",
    "Занимаюсь сайтами для {category}.",
    "Разрабатываю сайты для {category}.",
    "Создаю сайты для компаний в сфере {category}.",
    "Помогаю {category} получать клиентов через сайт.",
]

OFFERS = [
    "Одностраничник под ключ — 5000₽.",
    "Лендинг за 5000₽, готово за 1-2 дня.",
    "Сайт-визитка — 5000₽, делаю за пару дней.",
    "Простой сайт под ваш бизнес — 5000₽.",
    "Одностраничник за 5к, сдам за 1-2 дня.",
]

FEATURES = [
    "Ваши фото, форма заявки, кнопка WhatsApp.",
    "Портфолио ваших работ + форма захвата.",
    "Адаптив под телефоны, WhatsApp-кнопка.",
    "Всё под ключ: фото, тексты, контакты.",
    "Форма заявки + мессенджеры + адаптив.",
]

EXAMPLES = [
    "Пример: {link}",
    "Вот как выглядит: {link}",
    "Образец работы: {link}",
    "Посмотрите пример: {link}",
    "Можете глянуть: {link}",
]

CTAS = [
    "Интересно?",
    "Если актуально — напишите.",
    "Напишите если интересно.",
    "Актуально для вас?",
    "Хотите посмотреть варианты?",
    "Интересно обсудить?",
    "Напишите, покажу ещё примеры.",
]

# Ссылка на портфолио
PORTFOLIO_LINK = "https://privozzz-remont.vercel.app"


def generate_message(category: str = "ремонт квартир", link: str = PORTFOLIO_LINK) -> str:
    """Генерирует уникальное сообщение из рандомных блоков"""

    greeting = random.choice(GREETINGS)
    intro = random.choice(INTROS).format(category=category)
    offer = random.choice(OFFERS)
    features = random.choice(FEATURES)
    example = random.choice(EXAMPLES).format(link=link)
    cta = random.choice(CTAS)

    # Собираем с рандомными переносами строк
    parts = [greeting, intro, offer, features, example, cta]

    # Вариации структуры
    structures = [
        f"{greeting}\n\n{intro} {offer}\n\n{features}\n\n{example}\n\n{cta}",
        f"{greeting}\n\n{intro}\n{offer} {features}\n\n{example}\n\n{cta}",
        f"{greeting} {intro}\n\n{offer}\n{features}\n\n{example}\n\n{cta}",
        f"{greeting}\n\n{intro} {offer} {features}\n\n{example}\n\n{cta}",
    ]

    return random.choice(structures)


def generate_batch(count: int, category: str = "ремонт квартир") -> list:
    """Генерирует пачку уникальных сообщений"""
    messages = []
    seen = set()

    attempts = 0
    while len(messages) < count and attempts < count * 10:
        msg = generate_message(category)
        if msg not in seen:
            seen.add(msg)
            messages.append(msg)
        attempts += 1

    return messages


def process_leads_csv(csv_path: str, output_path: str = None):
    """Обрабатывает CSV с лидами и генерирует уникальное сообщение для каждого"""

    if not output_path:
        output_path = csv_path.replace(".csv", "_randomized.txt")

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        leads = list(reader)

    print(f"Загружено лидов: {len(leads)}")
    print(f"Генерирую уникальные сообщения...\n")

    with open(output_path, "w", encoding="utf-8") as f:
        for i, lead in enumerate(leads, 1):
            name = lead.get("name", "")
            phone = lead.get("phone", "")
            category = lead.get("category", "ремонт квартир")

            # Форматируем телефон для WhatsApp
            phone_clean = "".join(filter(str.isdigit, phone))
            if phone_clean.startswith("8"):
                phone_clean = "7" + phone_clean[1:]

            message = generate_message(category)

            f.write(f"=== #{i} {name} ===\n")
            f.write(f"WhatsApp: https://wa.me/{phone_clean}\n\n")
            f.write(message)
            f.write(f"\n\n{'='*50}\n\n")

            # Показываем прогресс
            if i % 50 == 0:
                print(f"  Обработано: {i}/{len(leads)}")

    print(f"\nГотово! Сохранено в: {output_path}")


def main():
    if len(sys.argv) < 2:
        # Демо-режим
        print("=== ДЕМО: 5 уникальных сообщений ===\n")
        for i, msg in enumerate(generate_batch(5), 1):
            print(f"--- Вариант {i} ---")
            print(msg)
            print()

        print("\nИспользование: python randomizer.py leads.csv")
        return

    csv_path = sys.argv[1]
    process_leads_csv(csv_path)


if __name__ == "__main__":
    main()
