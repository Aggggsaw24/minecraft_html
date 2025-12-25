import http.server
import socketserver
import os
import json
import asyncio
import threading
import mimetypes

# Попробуйте установить: pip install websockets
try:
    import websockets
except ImportError:
    print("ОШИБКА: Нужна библиотека websockets. Выполните: pip install websockets")
    exit()

HTTP_PORT = 8000
WS_PORT = 8001
MODS_DIR = 'mods'

# 1. HTTP СЕРВЕР (Раздает игру и моды)
class GameRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # API endpoint для получения списка модов
        if self.path == '/api/get_mods':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            mods = []
            if os.path.exists(MODS_DIR):
                for f in os.listdir(MODS_DIR):
                    if f.endswith('.js'):
                        mods.append(f)
            
            self.wfile.write(json.dumps(mods).encode())
            print(f"[API] Список модов отправлен: {mods}")
            return
        
        # Раздача файлов из папки mods
        if self.path.startswith('/mods/'):
            # Безопасная отдача файлов
            return super().do_GET()

        return super().do_GET()

def run_http_server():
    print(f"--- HTTP Сервер запущен: http://localhost:{HTTP_PORT} ---")
    # Разрешаем js файлы как модули
    mimetypes.add_type('application/javascript', '.js')
    with socketserver.TCPServer(("", HTTP_PORT), GameRequestHandler) as httpd:
        httpd.serve_forever()

# 2. WEBSOCKET СЕРВЕР (Мультиплеер)
CONNECTED_CLIENTS = {}

async def handler(websocket):
    # Присваиваем ID игроку
    player_id = id(websocket)
    CONNECTED_CLIENTS[player_id] = websocket
    print(f"[WS] Игрок {player_id} подключился")
    
    try:
        # Отправляем игроку его ID
        await websocket.send(json.dumps({"type": "init", "id": player_id}))
        
        async for message in websocket:
            data = json.loads(message)
            
            # Добавляем ID отправителя к данным
            data['id'] = player_id
            
            # Рассылаем всем ОСТАЛЬНЫМ игрокам
            for pid, client in CONNECTED_CLIENTS.items():
                if pid != player_id:
                    try:
                        await client.send(json.dumps(data))
                    except:
                        pass # Ошибка отправки (клиент отключился)
    except Exception as e:
        print(f"Ошибка сокета: {e}")
    finally:
        del CONNECTED_CLIENTS[player_id]
        print(f"[WS] Игрок {player_id} отключился")
        # Сообщаем всем, что игрок ушел, чтобы удалить его модельку
        disconnect_msg = json.dumps({"type": "player_leave", "id": player_id})
        for client in CONNECTED_CLIENTS.values():
            try:
                await client.send(disconnect_msg)
            except:
                pass

async def start_ws_server():
    print(f"--- WebSocket Сервер запущен на порту {WS_PORT} ---")
    async with websockets.serve(handler, "0.0.0.0", WS_PORT):
        await asyncio.Future()  # run forever

# Запуск в потоках
if __name__ == "__main__":
    if not os.path.exists(MODS_DIR):
        os.makedirs(MODS_DIR)
        print(f"Создана папка '{MODS_DIR}'. Положите туда .js скрипты!")

    # Запускаем HTTP в отдельном потоке
    http_thread = threading.Thread(target=run_http_server)
    http_thread.daemon = True
    http_thread.start()

    # Запускаем WS в основном потоке (asyncio)
    try:
        asyncio.run(start_ws_server())
    except KeyboardInterrupt:
        print("Сервер остановлен.")
