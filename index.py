import os
import json
import asyncio
from aiohttp import web

PORT = int(os.environ.get("PORT", 8080))
MODS_DIR = 'mods'

# --- ХРАНИЛИЩЕ МИРА ---
WORLD_STATE = []
# Хранилище клиентов: {ws: {'id': 123, 'name': 'Player'}}
CONNECTED_CLIENTS = {}

async def handle_index(request):
    return web.FileResponse('./index.html')

async def handle_mods_list(request):
    mods = []
    if os.path.exists(MODS_DIR):
        for f in os.listdir(MODS_DIR):
            if f.endswith('.js'):
                mods.append(f)
    return web.json_response(mods)

async def websocket_handler(request):
    # ВАЖНО: Объявляем global в самом начале функции
    global WORLD_STATE
    
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    player_id = id(ws)
    # По умолчанию имя гость
    CONNECTED_CLIENTS[ws] = {'id': player_id, 'name': f"Guest_{str(player_id)[-4:]}"}
    print(f"[WS] Игрок {player_id} подключился")

    try:
        # 1. Отправляем ID игроку
        await ws.send_json({"type": "init", "id": player_id})

        # 2. Отправляем текущий мир (Чтение WORLD_STATE)
        if WORLD_STATE:
            await ws.send_json({
                "type": "world_load", 
                "blocks": WORLD_STATE
            })

        # 3. Слушаем сообщения
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    data['id'] = player_id 

                    # Обработка входа
                    if data.get('type') == 'join':
                        name = data.get('name', 'Guest')
                        CONNECTED_CLIENTS[ws]['name'] = name
                        data['name'] = name

                    if data.get('type') == 'move':
                        data['name'] = CONNECTED_CLIENTS[ws]['name']

                    # ЛОГИКА БЛОКОВ
                    if data.get('type') == 'block':
                        if data['action'] == 'add':
                            # Добавление (изменение списка методом append не требует global, но для единообразия ок)
                            block_data = {
                                'x': data['x'], 'y': data['y'], 'z': data['z'], 
                                'color': data['color']
                            }
                            WORLD_STATE.append(block_data)
                        
                        elif data['action'] == 'remove':
                            # Удаление (перезапись переменной требует global)
                            WORLD_STATE = [b for b in WORLD_STATE if not (
                                abs(b['x'] - data['x']) < 0.1 and 
                                abs(b['y'] - data['y']) < 0.1 and 
                                abs(b['z'] - data['z']) < 0.1
                            )]

                    # Рассылка
                    for client in list(CONNECTED_CLIENTS.keys()):
                        if client != ws and not client.closed:
                            await client.send_json(data)
                            
                except Exception as e:
                    print(f"Ошибка данных: {e}")
            elif msg.type == web.WSMsgType.ERROR:
                print('ws connection closed with exception %s', ws.exception())

    finally:
        if ws in CONNECTED_CLIENTS:
            del CONNECTED_CLIENTS[ws]
        
        leave_msg = {"type": "player_leave", "id": player_id}
        for client in list(CONNECTED_CLIENTS.keys()):
            if not client.closed:
                await client.send_json(leave_msg)

    return ws

async def init_app():
    if not os.path.exists(MODS_DIR):
        os.makedirs(MODS_DIR)

    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/ws', websocket_handler)
    app.router.add_get('/api/get_mods', handle_mods_list)
    app.router.add_static('/mods/', path=MODS_DIR, name='mods')
    
    return app

if __name__ == '__main__':
    print(f"--- Сервер запущен: http://localhost:{PORT} ---")
    web.run_app(init_app(), port=PORT)
