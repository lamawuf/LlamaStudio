#!/usr/bin/env python3
"""
СБОР ЛИДОВ — Краснодарский край
Ремонт квартир, сортировка по новизне, только без сайтов
"""

import csv
import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright


def main():
    leads = []
    seen_phones = set()

    print(f"\n{'='*60}")
    print("  КРАСНОДАРСКИЙ КРАЙ — ремонт квартир без сайтов")
    print(f"{'='*60}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--start-maximized'])
        page = browser.new_page(no_viewport=True)

        # Краснодарский край
        search_url = "https://2gis.ru/krasnodar/search/ремонт%20квартир%20краснодарский%20край"
        page.goto(search_url)
        print("🌐 Загружаю 2GIS — Краснодарский край...\n")
        time.sleep(4)

        # Сортировка по новизне
        print("📋 Ставлю сортировку 'По новизне'...")
        try:
            # Ищем кнопку сортировки
            sort_buttons = page.locator('button, span').filter(has_text=re.compile(r'По\s*(рейтингу|новизне|умолчанию)', re.I))
            if sort_buttons.count() > 0:
                sort_buttons.first.click()
                time.sleep(1)

            # Клик на "По новизне"
            novizne = page.locator('button, span, div').filter(has_text=re.compile(r'^По новизне$', re.I))
            if novizne.count() > 0:
                novizne.first.click()
                time.sleep(2)
                print("✅ Сортировка 'По новизне' установлена\n")
            else:
                print("⚠️ Кнопка 'По новизне' не найдена, пробую альтернативный метод...")
                # Альтернативный метод через xpath
                page.keyboard.press('Escape')
                time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Сортировка: {e}\n")

        current_page = 1
        max_pages = 999  # До конца
        total_checked = 0

        while current_page <= max_pages:
            print(f"\n{'─'*50}")
            print(f"📄 СТРАНИЦА {current_page}")
            print(f"{'─'*50}")

            # Скроллим список чтобы подгрузились все карточки
            try:
                list_container = page.locator('div[class*="searchResults"], div[class*="_list"]').first
                for _ in range(5):
                    list_container.evaluate('el => el.scrollBy(0, 500)')
                    time.sleep(0.3)
            except:
                pass

            # Находим все карточки компаний
            cards = page.locator('a[href*="/firm/"]').all()

            # Фильтруем уникальные
            firm_links = []
            seen_hrefs = set()
            for card in cards:
                try:
                    href = card.get_attribute('href')
                    if href and '/firm/' in href and 'tab' not in href and href not in seen_hrefs:
                        seen_hrefs.add(href)
                        firm_links.append(card)
                except:
                    pass

            print(f"   Найдено компаний: {len(firm_links)}")

            if len(firm_links) == 0:
                print("   ⚠️ Нет компаний на странице, возможно конец")
                break

            # Кликаем на каждую карточку
            page_leads_before = len(leads)

            for i, card in enumerate(firm_links):
                try:
                    total_checked += 1
                    card.scroll_into_view_if_needed()
                    time.sleep(0.2)
                    card.click()
                    time.sleep(1)

                    # Парсим данные
                    parse_company(page, leads, seen_phones, total_checked)

                except Exception as e:
                    continue

            page_leads = len(leads) - page_leads_before
            print(f"\n   📊 Страница {current_page}: +{page_leads} лидов (всего: {len(leads)})")

            # Сохраняем промежуточно каждые 5 страниц
            if current_page % 5 == 0 and leads:
                save_leads(leads, interim=True)

            # Переключаем страницу
            next_page_found = False

            # Метод 1: Ищем номер следующей страницы
            try:
                next_num = str(current_page + 1)
                next_btn = page.locator(f'a, button, span').filter(has_text=re.compile(f'^{next_num}$'))
                if next_btn.count() > 0:
                    next_btn.first.click()
                    time.sleep(2)
                    current_page += 1
                    next_page_found = True
            except:
                pass

            # Метод 2: Стрелка вправо
            if not next_page_found:
                try:
                    next_arrow = page.locator('[aria-label*="Следующая"], [aria-label*="Next"], button:has-text("›"), a:has-text("›")')
                    if next_arrow.count() > 0:
                        next_arrow.first.click()
                        time.sleep(2)
                        current_page += 1
                        next_page_found = True
                except:
                    pass

            if not next_page_found:
                print("\n🏁 Достигнут конец списка!")
                break

        browser.close()

    # Финальное сохранение
    save_leads(leads, interim=False)


def parse_company(page, leads, seen_phones, num):
    """Парсим данные открытой карточки"""

    try:
        # Название
        name = "Компания"
        try:
            h1 = page.query_selector('h1')
            if h1:
                name = h1.inner_text().strip()
        except:
            pass

        # Проверяем есть ли сайт СНАЧАЛА
        SOCIALS = {
            'vk.com': 'VK', 'vk.ru': 'VK',
            't.me': 'Telegram', 'telegram.me': 'Telegram',
            'wa.me': 'WhatsApp', 'whatsapp.com': 'WhatsApp',
            'instagram.com': 'Instagram',
            'youtube.com': 'YouTube',
            'ok.ru': 'OK',
            'taplink.cc': 'Taplink',
            'linktree': 'Linktree',
        }
        NOT_A_SITE = list(SOCIALS.keys()) + [
            '2gis', 'facebook', 'fb.com', 'tiktok', 'rutube',
            'viber', 'yandex', 'google', 'mail.ru', 'avito'
        ]

        has_real_site = False
        found_socials = []

        links = page.query_selector_all('a')
        for link in links:
            try:
                text = (link.inner_text() or '').strip().lower()
                href_link = (link.get_attribute('href') or '').lower()

                # Проверяем соцсети
                for key, label in SOCIALS.items():
                    if key in href_link or key in text:
                        if label not in found_socials:
                            found_socials.append(label)

                # Проверяем сайт (домен в тексте)
                if re.match(r'^[a-zа-яё0-9][a-zа-яё0-9\-\.]*\.(ru|com|рф|pro|su|net|org|biz|info|online|site|store|shop)$', text):
                    if not any(s in text for s in NOT_A_SITE):
                        has_real_site = True

                # Проверяем сайт в href
                if 'http' in href_link and not any(s in href_link for s in NOT_A_SITE):
                    # Это может быть сайт
                    domain_match = re.search(r'https?://([^/]+)', href_link)
                    if domain_match:
                        domain = domain_match.group(1).lower()
                        if '.' in domain and not any(s in domain for s in NOT_A_SITE):
                            has_real_site = True
            except:
                continue

        if has_real_site:
            print(f"   {num}. ⏭ {name[:40]} — ЕСТЬ САЙТ")
            return

        # Телефон
        phone = None
        phone_els = page.query_selector_all('a[href^="tel:"]')
        for phone_el in phone_els:
            href = phone_el.get_attribute('href')
            if not href:
                continue

            phone_raw = re.sub(r'[^\d+]', '', href.replace('tel:', ''))
            if phone_raw.startswith('8') and len(phone_raw) == 11:
                phone_raw = '+7' + phone_raw[1:]
            elif phone_raw.startswith('7') and len(phone_raw) == 11:
                phone_raw = '+' + phone_raw

            if len(phone_raw) >= 11 and phone_raw not in seen_phones:
                phone = phone_raw
                seen_phones.add(phone)
                break

        if not phone:
            print(f"   {num}. ⚠️ {name[:40]} — нет телефона")
            return

        # URL карточки
        current_url = page.url

        # Сохраняем лида
        social_str = ', '.join(found_socials) if found_socials else ''
        leads.append({
            'name': name,
            'phone': phone,
            'social': social_str,
            '2gis_url': current_url
        })

        social_info = f" [{social_str}]" if social_str else ""
        print(f"   {num}. ✅ {name[:40]}{social_info}")
        print(f"       📞 {phone}")

    except Exception as e:
        print(f"   {num}. ❌ Ошибка: {e}")


def save_leads(leads, interim=False):
    if not leads:
        if not interim:
            print("\n❌ Ничего не собрано")
        return

    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    suffix = "_interim" if interim else ""
    filename = f"leads_krai_{timestamp}{suffix}.csv"

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'phone', 'social', '2gis_url'])
        writer.writeheader()
        writer.writerows(leads)

    if interim:
        print(f"\n   💾 Промежуточное сохранение: {filename}")
    else:
        print(f"\n{'='*60}")
        print(f"  ✅ СОБРАНО: {len(leads)} лидов БЕЗ САЙТОВ")
        print(f"  📁 Файл: {filename}")
        print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
