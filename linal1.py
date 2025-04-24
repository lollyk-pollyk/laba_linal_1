import asyncio
import platform
import pygame
import math

# Инициализация Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Seashell Surface")
clock = pygame.time.Clock()

# Параметры поверхности
alpha = 0.2  # Начальное значение alpha
beta = 0.15  # Начальное значение beta
u_steps = 50  # Количество шагов по u
v_steps = 150  # Количество шагов по v
u_range = (0, 2 * math.pi)
v_range = (0, 6 * math.pi)

# Параметры для вращения
angle_x, angle_y = 0, 0
mouse_down = False
last_mouse_pos = None

# Функция для вычисления точки на поверхности
def get_point(u, v):
    x = alpha * math.exp(beta * v) * math.cos(v) * (1 + math.cos(u))
    y = alpha * math.exp(beta * v) * math.sin(v) * (1 + math.cos(u))
    z = alpha * math.exp(beta * v) * math.sin(u)
    return (x, y, z)

# Функция для вращения точки вокруг осей X и Y
def rotate_point(point, angle_x, angle_y):
    x, y, z = point

    # Вращение вокруг оси X
    y_new = y * math.cos(angle_x) - z * math.sin(angle_x)
    z_new = y * math.sin(angle_x) + z * math.cos(angle_x)
    y, z = y_new, z_new

    # Вращение вокруг оси Y
    x_new = x * math.cos(angle_y) + z * math.sin(angle_y)
    z_new = -x * math.sin(angle_y) + z * math.cos(angle_y)
    x, z = x_new, z_new

    return (x, y, z)

# Функция для проекции 3D точки на 2D экран
def project(point):
    x, y, z = point
    # Простая перспективная проекция
    distance = 5  # Расстояние от камеры
    scale = 200  # Масштаб
    if z + distance > 0:  # Проверяем, что точка перед камерой
        factor = scale / (z + distance)
        x_2d = x * factor + WIDTH / 2
        y_2d = y * factor + HEIGHT / 2
        return (x_2d, y_2d, z)  # Возвращаем z для сортировки
    return None

def setup():
    global points
    points = []
    # Генерируем точки поверхности
    for i in range(u_steps):
        u = u_range[0] + i * (u_range[1] - u_range[0]) / (u_steps - 1)
        row = []
        for j in range(v_steps):
            v = v_range[0] + j * (v_range[1] - v_range[0]) / (v_steps - 1)
            point = get_point(u, v)
            row.append(point)
        points.append(row)

def update_loop():
    global angle_x, angle_y, mouse_down, last_mouse_pos

    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            return False  # Сигнал для выхода из цикла
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_down = True
            last_mouse_pos = pygame.mouse.get_pos()
        elif event.type == pygame.MOUSEBUTTONUP:
            mouse_down = False
        elif event.type == pygame.MOUSEMOTION and mouse_down:
            current_pos = pygame.mouse.get_pos()
            dx = current_pos[0] - last_mouse_pos[0]
            dy = current_pos[1] - last_mouse_pos[1]
            angle_y += dx * 0.01
            angle_x += dy * 0.01
            last_mouse_pos = current_pos

    # Очистка экрана
    screen.fill((255, 255, 255))

    # Список полигонов для сортировки по глубине
    polygons = []

    # Проецируем точки и собираем полигоны
    for i in range(u_steps - 1):
        for j in range(v_steps - 1):
            # Получаем четыре точки полигона
            p1 = rotate_point(points[i][j], angle_x, angle_y)
            p2 = rotate_point(points[i + 1][j], angle_x, angle_y)
            p3 = rotate_point(points[i + 1][j + 1], angle_x, angle_y)
            p4 = rotate_point(points[i][j + 1], angle_x, angle_y)

            # Проецируем на 2D
            proj1 = project(p1)
            proj2 = project(p2)
            proj3 = project(p3)
            proj4 = project(p4)

            # Проверяем, что все точки перед камерой
            if all([proj1, proj2, proj3, proj4]):
                # Вычисляем среднюю z-координату для сортировки
                avg_z = (proj1[2] + proj2[2] + proj3[2] + proj4[2]) / 4
                # Собираем полигон: [(x, y) точки, средняя z, цвет]
                polygons.append(([(proj1[0], proj1[1]), (proj2[0], proj2[1]),
                                  (proj3[0], proj3[1]), (proj4[0], proj4[1])], avg_z, (248, 24, 148)))

    # Сортируем полигоны по глубине (от дальних к ближним)
    polygons.sort(key=lambda x: x[1], reverse=True)

    # Отрисовываем полигоны
    for polygon, _, color in polygons:
        pygame.draw.polygon(screen, color, polygon)
        # Отрисовываем контуры для большей чёткости
        pygame.draw.polygon(screen, (50, 50, 50), polygon, 1)

    pygame.display.flip()
    return True  # Продолжаем цикл

async def main():
    setup()
    while True:
        if not update_loop():  # Проверяем, нужно ли выйти
            break
        await asyncio.sleep(1.0 / 60)  # 60 FPS

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())