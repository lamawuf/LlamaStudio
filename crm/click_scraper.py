#!/usr/bin/env python3
"""
ТЫ КЛИКАЕШЬ — СКРИПТ ПАРСИТ
"""

import csv
import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright


def main():
    leads = []
    seen = set()

    print(f"\n{'='*55}")
    print("  ТЫ КЛИКАЕШЬ — Я СОБИРАЮ")
    print(f"{'='*55}")
    print("""
  1. Откроется браузер
  2. Кликай на компании слева
  3. Внизу страницы 1 2 3 4 5 6 7 — переключай!
  4. Закрой браузер когда всё прошёл
""")
    print(f"{'='*55}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--start-maximized'])
        page = browser.new_page(no_viewport=True)

        page.goto("https://2gis.ru/krasnodar/search/ремонт%20квартир")
        print("✅ Браузер открыт. Кликай на компании!\n")

        last_phone = None

        try:
            while True:
                time.sleep(1)

                try:
                    phone_els = page.query_selector_all('a[href^="tel:"]')

                    for phone_el in phone_els:
                        href = phone_el.get_attribute('href')
                        if not href:
                            continue

                        phone = re.sub(r'[^\d+]', '', href.replace('tel:', ''))
                        if phone.startswith('8') and len(phone) == 11:
                            phone = '+7' + phone[1:]

                        if len(phone) < 11 or phone == last_phone or phone in seen:
                            continue

                        last_phone = phone
                        seen.add(phone)

                        # Название
                        name = "Компания"
                        try:
                            h1 = page.query_selector('h1')
                            if h1:
                                name = h1.inner_text().strip()
                        except:
                            pass

                        # URL страницы (2GIS профиль)
                        current_url = page.url

                        # Соцсети/мессенджеры
                        SOCIALS = {
                            'vk.com': 'VK',
                            'vk.ru': 'VK',
                            't.me': 'Telegram',
                            'telegram': 'Telegram',
                            'wa.me': 'WhatsApp',
                            'whatsapp': 'WhatsApp',
                            'instagram': 'Instagram',
                            'youtube': 'YouTube',
                            'ok.ru': 'OK',
                            'taplink': 'Taplink',
                            'linktree': 'Linktree',
                        }

                        NOT_A_SITE = list(SOCIALS.keys()) + ['2gis', 'facebook', 'fb.com', 'tiktok', 'rutube', 'viber']

                        has_real_site = False
                        found_domain = None
                        found_socials = []

                        try:
                            links = page.query_selector_all('a')
                            for link in links:
                                text = (link.inner_text() or '').strip().lower()
                                href = (link.get_attribute('href') or '').lower()

                                # Собираем соцсети
                                for key, label in SOCIALS.items():
                                    if key in href or key in text:
                                        if label not in found_socials:
                                            found_socials.append(label)

                                # Текст ссылки похож на домен?
                                if re.match(r'^[a-zа-яё0-9][a-zа-яё0-9\-\.]*\.(ru|com|рф|pro|su|net|org|biz|info|online|site|store|shop)$', text):
                                    if any(s in text for s in NOT_A_SITE):
                                        continue
                                    else:
                                        has_real_site = True
                                        found_domain = text
                                        break
                        except:
                            pass

                        if has_real_site:
                            print(f"⏭  {name[:40]} — сайт: {found_domain}\n")
                            continue

                        # НЕТ САЙТА — записываем!
                        social_str = ', '.join(found_socials) if found_socials else ''

                        leads.append({
                            'name': name,
                            'phone': phone,
                            'social': social_str,
                            '2gis_url': current_url
                        })

                        social_info = f" [{social_str}]" if social_str else ""
                        print(f"✅ [{len(leads)}] {name[:40]}{social_info}")
                        print(f"   📞 {phone}\n")

                except Exception as e:
                    pass

        except:
            pass

    # Сохраняем
    if leads:
        filename = f"leads_{datetime.now().strftime('%H%M')}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'phone', 'social', '2gis_url'])
            writer.writeheader()
            writer.writerows(leads)

        print(f"\n{'='*55}")
        print(f"  ✅ СОБРАНО: {len(leads)} лидов БЕЗ сайта")
        print(f"  📁 Файл: {filename}")
        print(f"{'='*55}\n")
    else:
        print("\n❌ Ничего не собрано")


if __name__ == '__main__':
    main()
