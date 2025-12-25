import http.server
import socketserver
import webbrowser
import os
import sys

# Настройки
PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Указываем серверу искать файлы в папке скрипта
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def run_server():
    # Пробуем запустить сервер
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            url = f"http://localhost:{PORT}"
            print(f"--- СЕРВЕР ЗАПУЩЕН ---")
            print(f"Игра доступна по адресу: {url}")
            print(f"Нажми Ctrl+C в консоли, чтобы остановить сервер.")
            
            # Автоматически открываем браузер
            webbrowser.open(url)
            
            # Держим сервер включенным
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 98: # Ошибка "Порт занят"
            print(f"Ошибка: Порт {PORT} занят. Попробуй закрыть другие серверы или поменяй PORT в скрипте.")
        else:
            print(f"Ошибка запуска: {e}")

if __name__ == "__main__":
    run_server()
