// Этот код выполнится в браузере автоматически
console.log("--- Mod Loaded: Structures ---");

// Используем API, который мы предоставили в index.html
const API = window.GameAPI;

API.chat("Mod 'Structures' is active!");

// Создадим случайные башни при старте
for (let i = 0; i < 10; i++) {
    const x = (Math.random() - 0.5) * 40;
    const z = (Math.random() - 0.5) * 40;
    const height = Math.floor(Math.random() * 5) + 3;
    
    // Цвет башни
    const color = Math.random() * 0xffffff;

    for (let h = 0; h < height; h++) {
        API.addBlock(x, h + 0.5, z, color);
    }
}

// Добавим прослушку клавиши "M" чтобы спавнить магический блок
document.addEventListener('keydown', (e) => {
    if (e.code === 'KeyM') {
        const playerPos = API.camera.position;
        API.addBlock(playerPos.x, playerPos.y, playerPos.z, 0xffff00); // Желтый блок в игроке
        API.chat("Magic block spawned at your position!");
    }
});