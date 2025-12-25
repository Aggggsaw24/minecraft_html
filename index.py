import os
import json
import asyncio
from aiohttp import web, WSMsgType

PORT = int(os.environ.get("PORT", 8080))
MODS_DIR = 'mods'

# --- ХРАНИЛИЩЕ МИРА ---
WORLD_STATE = []

# Хранилище клиентов и их состояния
# {ws: {'id': 123, 'name': 'Guest', 'x': 0, 'y': 0, 'z': 0, 'ry': 0}}
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
    global WORLD_STATE
    
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    player_id = id(ws)
    default_name = f"Guest_{str(player_id)[-4:]}"
    
    # Инициализируем игрока с начальными координатами
    CONNECTED_CLIENTS[ws] = {
        'id': player_id, 
        'name': default_name,
        'x': 0, 'y': 10, 'z': 0, 'ry': 0
    }
    print(f"[WS] Игрок {player_id} подключился")

    try:
        # 1. Отправляем ID игроку (Личная инициализация)
        await ws.send_json({"type": "init", "id": player_id})

        # 2. Отправляем текущий мир (Загрузка блоков)
        if WORLD_STATE:
            await ws.send_json({
                "type": "world_load", 
                "blocks": WORLD_STATE
            })

        # 3. Отправляем новому игроку позиции ВСЕХ существующих игроков
        for client_ws, info in CONNECTED_CLIENTS.items():
            if client_ws != ws and not client_ws.closed:
                try:
                    await ws.send_json({
                        'type': 'move',
                        'id': info['id'],
                        'name': info['name'],
                        'x': info['x'],
                        'y': info['y'],
                        'z': info['z'],
                        'ry': info['ry']
                    })
                except Exception:
                    pass

        # 4. СООБЩАЕМ ВСЕМ ОСТАЛЬНЫМ О НОВОМ ИГРОКЕ СРАЗУ
        # Это решает проблему "невидимости" при входе
        join_announcement = {
            'type': 'join',
            'id': player_id,
            'name': default_name
        }
        for client in list(CONNECTED_CLIENTS.keys()):
            if client != ws and not client.closed:
                try:
                    await client.send_json(join_announcement)
                except Exception:
                    pass

        # 5. Слушаем сообщения
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    data['id'] = player_id 

                    # Обработка смены ника (join)
                    if data.get('type') == 'join':
                        name = data.get('name', default_name)
                        CONNECTED_CLIENTS[ws]['name'] = name
                        data['name'] = name

                    # Обработка движения (сохраняем в памяти сервера)
                    if data.get('type') == 'move':
                        CONNECTED_CLIENTS[ws]['x'] = data.get('x', 0)
                        CONNECTED_CLIENTS[ws]['y'] = data.get('y', 0)
                        CONNECTED_CLIENTS[ws]['z'] = data.get('z', 0)
                        CONNECTED_CLIENTS[ws]['ry'] = data.get('ry', 0)
                        data['name'] = CONNECTED_CLIENTS[ws]['name']

                    # Логика блоков
                    if data.get('type') == 'block':
                        if data['action'] == 'add':
                            block_data = {
                                'x': data['x'], 'y': data['y'], 'z': data['z'], 
                                'color': data['color']
                            }
                            WORLD_STATE.append(block_data)
                            print(f"[Block] Add at {data['x']}, {data['y']}, {data['z']}")
                        
                        elif data['action'] == 'remove':
                            WORLD_STATE = [b for b in WORLD_STATE if not (
                                abs(b['x'] - data['x']) < 0.1 and 
                                abs(b['y'] - data['y']) < 0.1 and 
                                abs(b['z'] - data['z']) < 0.1
                            )]
                            print(f"[Block] Remove at {data['x']}, {data['y']}, {data['z']}")

                    # Рассылка всем остальным игрокам
                    for client in list(CONNECTED_CLIENTS.keys()):
                        if client != ws and not client.closed:
                            try:
                                await client.send_json(data)
                            except Exception:
                                pass # Игнорируем ошибки сети при рассылке
                            
                except Exception as e:
                    print(f"Ошибка данных: {e}")
            elif msg.type == WSMsgType.ERROR:
                print('ws connection closed with exception %s', ws.exception())

    finally:
        if ws in CONNECTED_CLIENTS:
            del CONNECTED_CLIENTS[ws]
        
        # Сообщаем всем о выходе игрока
        leave_msg = {"type": "player_leave", "id": player_id}
        for client in list(CONNECTED_CLIENTS.keys()):
            if not client.closed:
                try:
                    await client.send_json(leave_msg)
                except Exception:
                    pass

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
