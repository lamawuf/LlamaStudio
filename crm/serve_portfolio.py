#!/usr/bin/env python3
"""
Запускает все портфолио-сайты на разных портах
"""

import http.server
import socketserver
import os
import threading
from pathlib import Path

def serve_site(port: int, directory: str, name: str):
    """Запускает HTTP сервер для одного сайта"""
    os.chdir(directory)

    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *args: None  # Тихий режим

    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"  🌐 Site {port - 5000}: http://localhost:{port}  ({name})")
        httpd.serve_forever()

def main():
    base_dir = Path('/Users/lama/Downloads/Apps/ClientFarmer/portfolio_sites')

    print(f"\n{'='*60}")
    print("  ПОРТФОЛИО-САЙТЫ ЗАПУЩЕНЫ")
    print(f"{'='*60}\n")

    threads = []

    for i in range(1, 7):
        site_dir = base_dir / f"site{i}"
        if not site_dir.exists():
            continue

        # Читаем название компании
        config_path = site_dir / 'config.json'
        name = f"Site {i}"
        if config_path.exists():
            import json
            with open(config_path) as f:
                config = json.load(f)
                name = config.get('company', name)

        port = 5000 + i

        thread = threading.Thread(
            target=serve_site,
            args=(port, str(site_dir), name),
            daemon=True
        )
        thread.start()
        threads.append(thread)

    print(f"\n{'='*60}")
    print("  Нажми Ctrl+C чтобы остановить все сайты")
    print(f"{'='*60}\n")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\n\n  👋 Сайты остановлены\n")

if __name__ == '__main__':
    main()
