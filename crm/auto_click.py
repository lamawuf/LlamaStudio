#!/usr/bin/env python3
"""
АВТОМАТИЧЕСКИЙ СБОР — сам кликает, сам листает страницы
"""

import csv
import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright


def main():
    leads = []
    seen_phones = set()

    print(f"\n{'='*55}")
    print("  АВТОМАТ — сам кликает, сам листает")
    print(f"{'='*55}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--start-maximized'])
        page = browser.new_page(no_viewport=True)

        page.goto("https://2gis.ru/krasnodar/search/ремонт%20квартир")
        print("🌐 Загружаю 2GIS...\n")
        time.sleep(3)

        # Сортировка по новизне
        print("📋 Ставлю сортировку 'По новизне'...")
        try:
            # Клик на выпадающий список сортировки
            sort_dropdown = page.locator('xpath=//*[@id="root"]/div/div/div[1]/div[1]/div[3]/div/div/div[2]/div/div/div/div[2]/div[1]/div/div/div/div/div/div/div[2]/div/div/div/div/div/div/ul/li[1]/div/div[1]/div/span')
            sort_dropdown.click()
            time.sleep(1)
            # Клик на "По новизне"
            novizne_btn = page.locator('xpath=//*[@id="root"]/div/div/div[1]/div[1]/div[3]/div/div/div[2]/div/div/div/div[2]/div[1]/div/div/div/div/div/div/div[2]/div/div/div/div/div/div/ul/li[1]/div/div[2]/button[2]/span')
            novizne_btn.click()
            time.sleep(2)
            print("✅ Сортировка установлена\n")
        except Exception as e:
            print(f"⚠️ Не удалось установить сортировку: {e}\n")

        # Перейдём на страницу 21
        print("⏩ Перехожу на страницу 21...")
        # Кликаем по страницам чтобы добраться до 21
        for skip_page in [3, 5, 7, 9, 11, 13, 15, 17, 19, 21]:
            try:
                page.locator(f'text="{skip_page}"').first.click()
                time.sleep(1)
            except:
                pass

        current_page = 21
        max_pages = 999  # До конца

        while current_page <= max_pages:
            print(f"📄 Страница {current_page}/{max_pages}")

            # Находим все карточки компаний в списке
            # Ищем ссылки которые ведут на /firm/
            cards = page.locator('a[href*="/firm/"]').all()

            # Фильтруем только те что в списке слева (не в рекламе)
            firm_links = []
            for card in cards:
                try:
                    href = card.get_attribute('href')
                    if href and '/firm/' in href and 'tab' not in href:
                        firm_links.append(card)
                except:
                    pass

            print(f"   Найдено {len(firm_links)} компаний")

            # Кликаем на каждую карточку
            clicked = set()
            for i, card in enumerate(firm_links):
                try:
                    href = card.get_attribute('href')
                    if href in clicked:
                        continue
                    clicked.add(href)

                    card.click()
                    time.sleep(1.2)

                    # Парсим данные
                    parse_company(page, leads, seen_phones)

                except Exception as e:
                    continue

            print(f"   Собрано лидов: {len(leads)}\n")

            # Переключаем страницу
            if current_page < max_pages:
                try:
                    next_btn = page.locator(f'text="{current_page + 1}"').first
                    if next_btn:
                        next_btn.click()
                        time.sleep(2)
                        current_page += 1
                    else:
                        # Пробуем кнопку ">"
                        next_arrow = page.locator('[aria-label="Следующая страница"], text="›"').first
                        if next_arrow:
                            next_arrow.click()
                            time.sleep(2)
                            current_page += 1
                        else:
                            break
                except:
                    break
            else:
                break

        browser.close()

    # Сохраняем
    save_leads(leads)


def parse_company(page, leads, seen_phones):
    """Парсим данные открытой карточки"""

    try:
        # Телефон
        phone_els = page.query_selector_all('a[href^="tel:"]')
        for phone_el in phone_els:
            href = phone_el.get_attribute('href')
            if not href:
                continue

            phone = re.sub(r'[^\d+]', '', href.replace('tel:', ''))
            if phone.startswith('8') and len(phone) == 11:
                phone = '+7' + phone[1:]

            if len(phone) < 11 or phone in seen_phones:
                continue

            seen_phones.add(phone)

            # Название
            name = "Компания"
            try:
                h1 = page.query_selector('h1')
                if h1:
                    name = h1.inner_text().strip()
            except:
                pass

            # URL
            current_url = page.url

            # Соцсети
            SOCIALS = {
                'vk.com': 'VK', 'vk.ru': 'VK',
                't.me': 'Telegram', 'telegram': 'Telegram',
                'wa.me': 'WhatsApp', 'whatsapp': 'WhatsApp',
                'instagram': 'Instagram', 'youtube': 'YouTube',
                'ok.ru': 'OK', 'taplink': 'Taplink', 'linktree': 'Linktree',
            }
            NOT_A_SITE = list(SOCIALS.keys()) + ['2gis', 'facebook', 'fb.com', 'tiktok', 'rutube', 'viber']

            has_real_site = False
            found_socials = []

            links = page.query_selector_all('a')
            for link in links:
                text = (link.inner_text() or '').strip().lower()
                href_link = (link.get_attribute('href') or '').lower()

                for key, label in SOCIALS.items():
                    if key in href_link or key in text:
                        if label not in found_socials:
                            found_socials.append(label)

                if re.match(r'^[a-zа-яё0-9][a-zа-яё0-9\-\.]*\.(ru|com|рф|pro|su|net|org|biz|info|online|site|store|shop)$', text):
                    if not any(s in text for s in NOT_A_SITE):
                        has_real_site = True
                        break

            if has_real_site:
                print(f"   ⏭ {name[:35]} — есть сайт")
                return

            social_str = ', '.join(found_socials) if found_socials else ''
            leads.append({
                'name': name,
                'phone': phone,
                'social': social_str,
                '2gis_url': current_url
            })

            social_info = f" [{social_str}]" if social_str else ""
            print(f"   ✅ {name[:35]}{social_info}")
            print(f"      📞 {phone}")
            return

    except:
        pass


def save_leads(leads):
    if leads:
        filename = f"leads_auto_{datetime.now().strftime('%H%M')}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'phone', 'social', '2gis_url'])
            writer.writeheader()
            writer.writerows(leads)

        print(f"\n{'='*55}")
        print(f"  ✅ СОБРАНО: {len(leads)} лидов")
        print(f"  📁 Файл: {filename}")
        print(f"{'='*55}\n")
    else:
        print("\n❌ Ничего не собрано")


if __name__ == '__main__':
    main()
