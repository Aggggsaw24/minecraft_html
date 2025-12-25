from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import math
import random

# Инициализация приложения
app = Ursina()

# --- КОНФИГУРАЦИЯ ---
window.title = 'Minecraft Python - Ursina'
window.borderless = False
window.fullscreen = False
window.exit_button.visible = False
window.fps_counter.enabled = False  # Мы сделаем свой счетчик

# Настройка неба (цвет как в JS коде)
window.color = color.rgb(135, 206, 235)  # Sky blue
scene.fog_density = 0.04
scene.fog_color = window.color

# Цвета блоков (аналог текстур из JS)
block_colors = {
    1: color.rgb(91, 140, 56),    # Grass (Зеленый)
    2: color.rgb(112, 72, 40),    # Dirt (Коричневый)
    3: color.rgb(119, 119, 119),  # Stone (Серый)
    4: color.rgb(74, 51, 26),     # Wood (Темное дерево)
    5: color.rgb(58, 95, 11),     # Leaves (Листва)
}

current_block_type = 1

# --- КЛАСС БЛОКА ---
class Voxel(Button):
    def __init__(self, position=(0,0,0), block_type=1):
        super().__init__(
            parent=scene,
            position=position,
            model='cube', # Можно использовать 'assets/block' если есть модель
            origin_y=0.5,
            texture='white_cube',
            color=block_colors.get(block_type, color.white),
            highlight_color=color.lime,
        )
        self.block_type = block_type

    def input(self, key):
        if self.hovered:
            # ЛКМ - Ломать (в Ursina 'left mouse down')
            if key == 'left mouse down':
                destroy(self)
                update_ui()
            
            # ПКМ - Ставить (в Ursina 'right mouse down')
            elif key == 'right mouse down':
                # Ставим блок в направлении нормали (куда смотрит грань)
                Voxel(position=self.position + mouse.normal, block_type=current_block_type)
                update_ui()

# --- ГЕНЕРАЦИЯ МИРА ---
# Используем ту же логику синусоид, что и в твоем JS коде
def generate_world():
    world_size = 20  # Радиус
    for x in range(-world_size // 2, world_size // 2):
        for z in range(-world_size // 2, world_size // 2):
            # Высота ландшафта (формула из JS: sin(x*0.1)*2 + cos(z*0.1)*2 + 2)
            height = math.floor(math.sin(x * 0.1) * 2 + math.cos(z * 0.1) * 2) + 2
            
            # Коренная порода (Bedrock/Stone)
            Voxel(position=(x, -2, z), block_type=3)

            # Заполнение
            for y in range(-1, height + 1):
                b_type = 3 # Stone
                if y == height: b_type = 1 # Grass
                elif y > height - 3: b_type = 2 # Dirt
                
                Voxel(position=(x, y, z), block_type=b_type)
            
            # Деревья (редко)
            if not (-5 < x < 5 and -5 < z < 5): # Чистая зона спавна
                if random.random() < 0.02 and height > 0:
                    create_tree(x, height + 1, z)

    update_ui()

def create_tree(x, y, z):
    # Ствол
    for i in range(4):
        Voxel(position=(x, y+i, z), block_type=4)
    
    # Листва
    for lx in range(-2, 3):
        for ly in range(3, 6):
            for lz in range(-2, 3):
                if abs(lx) == 2 and abs(lz) == 2: continue
                if random.random() > 0.2:
                    Voxel(position=(x+lx, y+ly, z+lz), block_type=5)

# --- ИГРОК ---
player = FirstPersonController()
player.cursor.visible = True # Прицел
player.gravity = 0.5
player.jump_height = 1.2
player.speed = 5

# --- UI (Интерфейс) ---
ui_blocks_count = Text(text='Блоков: 0', position=(-0.85, 0.45), scale=1.5)
ui_fps = Text(text='FPS: 60', position=(-0.85, 0.40), scale=1.5)
ui_info = Text(text='1-5: Выбор блока', position=(-0.85, 0.35), scale=1)

# Индикатор выбранного блока (квадратик внизу)
active_block_indicator = Entity(parent=camera.ui, model='quad', scale=0.05, color=block_colors[1], position=(0, -0.4))

def update_ui():
    count = 0
    # Считаем сущности Voxel в сцене
    for e in scene.entities:
        if isinstance(e, Voxel):
            count += 1
    ui_blocks_count.text = f'Блоков: {count}'

# --- ОБНОВЛЕНИЕ КАДРА ---
def update():
    global current_block_type
    
    # Выбор блока на цифры 1-5
    for key in '12345':
        if held_keys[key]:
            current_block_type = int(key)
            active_block_indicator.color = block_colors[current_block_type]
    
    # Убийство игрока при падении
    if player.y < -10:
        player.position = (0, 10, 0)
        
    # FPS
    ui_fps.text = f'FPS: {int(1//time.dt)}' if time.dt > 0 else 'FPS: 0'

# Запуск
generate_world()
app.run()
