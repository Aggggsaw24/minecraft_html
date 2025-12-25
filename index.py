import os
import json
import asyncio
from aiohttp import web

# Получаем порт из окружения или используем 8080
PORT = int(os.environ.get("PORT", 8080))
MODS_DIR = 'mods'

# Хранилище подключенных игроков {ws_connection: player_id}
CONNECTED_CLIENTS = {}

async def handle_index(request):
    """Отдает главную страницу игры"""
    return web.FileResponse('./index.html')

async def handle_mods_list(request):
    """API: Отдает список модов из папки mods"""
    mods = []
    if os.path.exists(MODS_DIR):
        for f in os.listdir(MODS_DIR):
            if f.endswith('.js'):
                mods.append(f)
    return web.json_response(mods)

async def websocket_handler(request):
    """Обрабатывает мультиплеер"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    player_id = id(ws)
    CONNECTED_CLIENTS[ws] = player_id
    print(f"[WS] Игрок {player_id} подключился")

    try:
        # 1. Отправляем игроку его ID
        await ws.send_json({"type": "init", "id": player_id})

        # 2. Слушаем сообщения от игрока
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    data['id'] = player_id # Подписываем сообщение

                    # Рассылаем всем остальным
                    for client in list(CONNECTED_CLIENTS.keys()):
                        if client != ws and not client.closed:
                            await client.send_json(data)
                except Exception as e:
                    print(f"Ошибка данных: {e}")
            elif msg.type == web.WSMsgType.ERROR:
                print('ws connection closed with exception %s', ws.exception())

    finally:
        # Игрок ушел
        if ws in CONNECTED_CLIENTS:
            del CONNECTED_CLIENTS[ws]
        print(f"[WS] Игрок {player_id} отключился")
        
        # Сообщаем всем, чтобы удалили модельку игрока
        leave_msg = {"type": "player_leave", "id": player_id}
        for client in list(CONNECTED_CLIENTS.keys()):
            if not client.closed:
                await client.send_json(leave_msg)

    return ws

async def init_app():
    if not os.path.exists(MODS_DIR):
        os.makedirs(MODS_DIR)

    app = web.Application()
    
    # Маршруты
    app.router.add_get('/', handle_index)
    app.router.add_get('/ws', websocket_handler)          # Вебсокет
    app.router.add_get('/api/get_mods', handle_mods_list) # Список модов
    app.router.add_static('/mods/', path=MODS_DIR, name='mods') # Файлы модов
    
    return app

if __name__ == '__main__':
    print(f"--- Сервер запущен: http://localhost:{PORT} ---")
    try:
        web.run_app(init_app(), port=PORT)
    except KeyboardInterrupt:
        pass
