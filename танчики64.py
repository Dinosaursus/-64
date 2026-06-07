import pygame
import random

pygame.init()

# НАЛАШТУВАННЯ ВІКНА ТА СІТКИ
TILE = 24
COLS, ROWS = 26, 26
GAME_W = COLS * TILE
GAME_H = ROWS * TILE
SIDE_W = 164
WIN_W = GAME_W + SIDE_W
WIN_H = GAME_H
FPS = 30

# НАПРЯМКИ РУХУ
UP, LEFT, DOWN, RIGHT = 0, 90, 180, 270

VX = {UP: 0, RIGHT: 1, DOWN: 0, LEFT: -1}
VY = {UP: -1, RIGHT: 0, DOWN: 1, LEFT: 0}

BG_COLOR = (16, 16, 16)
HUD_COLOR = (30, 30, 30)
WHITE = (255, 255, 255)

screen = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption("Танчики: Карта, Класи та Меню")
clock = pygame.time.Clock()

# КЛАСИ ПРОТИВНИКІВ
ENEMY_TYPES = [
    {"speed": 2, "hp": 1, "points": 100, "color": (200, 48, 48)},
    {"speed": 4, "hp": 1, "points": 200, "color": (55, 185, 65)},
    {"speed": 1, "hp": 3, "points": 400, "color": (78, 78, 200)}
]
ENEMY_WEIGHTS = [0.60, 0.25, 0.15]

# ДИЗАЙН РІВНЯ
LEVEL = [
    "@@@@@@@@@@@@@@@@@@@@@@@@@@",
    "@S.........S...........S.@",
    "@..##..##..@@@@..##..##..@",
    "@..##..##..@@@@..##..##..@",
    "@..##..##..####..##..##..@",
    "@..##..##........##..##..@",
    "@..##..##...##...##..##..@",
    "@......##...##...##......@",
    "@......##...##...##......@",
    "@..@@..##........##..@@..@",
    "@..@@..##...##...##..@@..@",
    "@...........##...........@",
    "@...####..........####...@",
    "@...####..........####...@",
    "@........@@@@@@@@........@",
    "@........@@@@@@@@........@",
    "@..##..##........##..##..@",
    "@..##..##........##..##..@",
    "@..##..##...##...##..##..@",
    "@..##..##...##...##..##..@",
    "@..##..##...##...##..##..@",
    "@...........##...........@",
    "@.......###.##.###.......@",
    "@.......#........#.......@",
    "@...P...#...E....#.......@",
    "@@@@@@@@@@@@@@@@@@@@@@@@@@"
]


# ФУНКЦІЇ ДЛЯ КАРТИНОК
def create_placeholder(color):
    surf = pygame.Surface((TILE - 2, TILE - 2), pygame.SRCALPHA)
    pygame.draw.rect(surf, color, (0, 0, TILE - 2, TILE - 2))
    pygame.draw.rect(surf, (50, 50, 50), (TILE // 2 - 3, 0, 4, TILE // 2))
    return surf


def colorize(image, color):
    tinted = image.copy()
    tinted.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
    return tinted


try:
    img_player_base = pygame.image.load("player.png").convert_alpha()
    img_enemy_base = pygame.image.load("enemy.png").convert_alpha()
    img_player_base = pygame.transform.scale(img_player_base, (TILE - 2, TILE - 2))
    img_enemy_base = pygame.transform.scale(img_enemy_base, (TILE - 2, TILE - 2))
    USE_IMAGES = True
except FileNotFoundError:
    USE_IMAGES = False


# КЛАСИ ОБ'ЄКТІВ
class Wall:
    def __init__(self, col, row, kind):
        self.rect = pygame.Rect(col * TILE, row * TILE, TILE, TILE)
        self.kind = kind
        self.hp = 2 if kind == "#" else -1
        self.alive = True

    def hit(self):
        if self.hp > 0:
            self.hp -= 1
            if self.hp <= 0:
                self.alive = False

    def draw(self, surf):
        if self.kind == "#":
            pygame.draw.rect(surf, (165, 72, 32), self.rect)
            pygame.draw.rect(surf, (88, 36, 14), self.rect, 1)
        else:
            pygame.draw.rect(surf, (108, 128, 148), self.rect)
            pygame.draw.rect(surf, (58, 82, 100), self.rect, 2)


class Eagle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE, TILE)
        self.alive = True

    def draw(self, surf):
        color = (220, 190, 0) if self.alive else (110, 60, 60)
        pygame.draw.rect(surf, color, self.rect)
        pygame.draw.circle(surf, (0, 0, 0), self.rect.center, 5)


class Bullet:
    def __init__(self, x, y, direction, is_player):
        self.rect = pygame.Rect(x - 2, y - 2, 4, 4)
        self.vx = VX[direction] * 6
        self.vy = VY[direction] * 6
        self.is_player = is_player
        self.alive = True

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if not (0 < self.rect.x < GAME_W and 0 < self.rect.y < GAME_H):
            self.alive = False

    def draw(self, surf):
        color = (255, 255, 120) if self.is_player else (255, 128, 78)
        pygame.draw.rect(surf, color, self.rect)


class Tank:
    def __init__(self, x, y, is_player, stats=None):
        self.rect = pygame.Rect(x, y, TILE - 2, TILE - 2)
        self.is_player = is_player
        self.direction = UP if is_player else DOWN
        self.alive = True
        self.fire_cd = 0

        if is_player:
            self.speed = 2
            self.hp = 1
            self.points = 0
            color = (235, 215, 0)
            self.image = img_player_base if USE_IMAGES else create_placeholder(color)
        else:
            self.speed = stats["speed"]
            self.hp = stats["hp"]
            self.points = stats["points"]
            color = stats["color"]
            self.image = colorize(img_enemy_base, color) if USE_IMAGES else create_placeholder(color)

    def move(self, dx, dy, walls, tanks):
        old_x, old_y = self.rect.x, self.rect.y
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed

        self.rect.x = max(0, min(GAME_W - self.rect.width, self.rect.x))
        self.rect.y = max(0, min(GAME_H - self.rect.height, self.rect.y))

        collision = False
        for w in walls:
            if w.alive and self.rect.colliderect(w.rect):
                collision = True
        for t in tanks:
            if t.alive and t is not self and self.rect.colliderect(t.rect):
                collision = True

        if collision:
            self.rect.x, self.rect.y = old_x, old_y
            return False
        return True

    def shoot(self):
        if self.fire_cd <= 0:
            self.fire_cd = 30
            return Bullet(self.rect.centerx, self.rect.centery, self.direction, self.is_player)
        return None

    def take_damage(self):
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False

    def draw(self, surf):
        rotated_img = pygame.transform.rotate(self.image, self.direction)
        img_rect = rotated_img.get_rect(center=self.rect.center)
        surf.blit(rotated_img, img_rect.topleft)

        if not self.is_player and self.hp > 1:
            for i in range(self.hp):
                pygame.draw.circle(surf, WHITE, (self.rect.x + 4 + i * 6, self.rect.y + 4), 2)


# ================================
# ГОЛОВНЕ МЕНЮ
# ================================
def main_menu():
    menu_font = pygame.font.SysFont("monospace", 50, bold=True)
    button_font = pygame.font.SysFont("monospace", 30, bold=True)

    # Розміри та позиції кнопок
    btn_w, btn_h = 200, 50
    play_btn = pygame.Rect(WIN_W // 2 - btn_w // 2, WIN_H // 2 - 40, btn_w, btn_h)
    exit_btn = pygame.Rect(WIN_W // 2 - btn_w // 2, WIN_H // 2 + 40, btn_w, btn_h)

    while True:
        screen.fill(BG_COLOR)

        # Заголовок
        title_text = menu_font.render("ТАНЧИКИ", True, (235, 215, 0))
        screen.blit(title_text, (WIN_W // 2 - title_text.get_width() // 2, WIN_H // 4))

        mouse_pos = pygame.mouse.get_pos()

        # Зміна кольору при наведенні миші (Hover ефект)
        play_color = (80, 200, 80) if play_btn.collidepoint(mouse_pos) else (55, 185, 65)
        exit_color = (220, 80, 80) if exit_btn.collidepoint(mouse_pos) else (200, 48, 48)

        # Малюємо кнопки
        pygame.draw.rect(screen, play_color, play_btn)
        pygame.draw.rect(screen, exit_color, exit_btn)

        # Текст на кнопках
        play_text = button_font.render("PLAY", True, WHITE)
        exit_text = button_font.render("EXIT", True, WHITE)

        screen.blit(play_text,
                    (play_btn.centerx - play_text.get_width() // 2, play_btn.centery - play_text.get_height() // 2))
        screen.blit(exit_text,
                    (exit_btn.centerx - exit_text.get_width() // 2, exit_btn.centery - exit_text.get_height() // 2))

        # Обробка подій у меню
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Лівий клік миші
                    if play_btn.collidepoint(mouse_pos):
                        return "play"
                    if exit_btn.collidepoint(mouse_pos):
                        return "exit"

        pygame.display.flip()
        clock.tick(FPS)


# ================================
# ОСНОВНИЙ ЦИКЛ ГРИ
# ================================
def main():
    walls = []
    spawn_points = []
    player_start = (0, 0)
    eagle_start = (0, 0)

    for row_idx, row in enumerate(LEVEL):
        for col_idx, char in enumerate(row):
            x = col_idx * TILE
            y = row_idx * TILE
            if char == '#':
                walls.append(Wall(col_idx, row_idx, "#"))
            elif char == '@':
                walls.append(Wall(col_idx, row_idx, "@"))
            elif char == 'P':
                player_start = (x, y)
            elif char == 'E':
                eagle_start = (x, y)
            elif char == 'S':
                spawn_points.append((x, y))

    player = Tank(player_start[0], player_start[1], True)
    eagle = Eagle(eagle_start[0], eagle_start[1])

    tanks = [player]
    bullets = []

    spawn_timer = 0
    score = 0
    game_over = False

    font = pygame.font.SysFont("monospace", 20, bold=True)
    running = True

    while running:
        # 1. ОБРОБКА ПОДІЙ
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"  # Повне закриття гри
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "menu"  # Повернення в меню
            if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                return main()  # Рестарт гри (запускаємо заново)

        if not game_over:
            # 2. РУХ ГРАВЦЯ
            keys = pygame.key.get_pressed()
            dx = dy = 0
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                dy = -1; player.direction = UP
            elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
                dy = 1; player.direction = DOWN
            elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
                dx = -1; player.direction = LEFT
            elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                dx = 1; player.direction = RIGHT

            if dx != 0 or dy != 0:
                player.move(dx, dy, walls, tanks)

            if keys[pygame.K_SPACE]:
                b = player.shoot()
                if b: bullets.append(b)

            # 3. СПАВН ВОРОГІВ
            spawn_timer -= 1
            if spawn_timer <= 0 and len(tanks) < 5:
                sx, sy = random.choice(spawn_points)
                enemy_stats = random.choices(ENEMY_TYPES, weights=ENEMY_WEIGHTS)[0]

                spawn_rect = pygame.Rect(sx, sy, TILE - 2, TILE - 2)
                can_spawn = True
                for t in tanks:
                    if t.rect.colliderect(spawn_rect):
                        can_spawn = False

                if can_spawn:
                    tanks.append(Tank(sx, sy, False, stats=enemy_stats))
                    spawn_timer = 120
                else:
                    spawn_timer = 30

            # 4. ЛОГІКА ВОРОГІВ
            for t in tanks:
                if t.fire_cd > 0: t.fire_cd -= 1

                if not t.is_player:
                    success = t.move(VX[t.direction], VY[t.direction], walls, tanks)
                    if not success:
                        t.direction = random.choice([UP, DOWN, LEFT, RIGHT])
                    if random.random() < 0.02:
                        b = t.shoot()
                        if b: bullets.append(b)

            # 5. ЛОГІКА КУЛЬ ТА ЗІТКНЕНЬ
            for b in bullets:
                b.update()
                if not b.alive: continue

                for w in walls:
                    if w.alive and b.rect.colliderect(w.rect):
                        w.hit()
                        b.alive = False
                        break

                if eagle.alive and b.rect.colliderect(eagle.rect):
                    eagle.alive = False
                    game_over = True

                if b.alive:
                    for t in tanks:
                        if t.alive and b.is_player != t.is_player and b.rect.colliderect(t.rect):
                            t.take_damage()
                            b.alive = False
                            if not t.alive and not t.is_player:
                                score += t.points
                            if not t.alive and t.is_player:
                                game_over = True
                            break

            bullets = [b for b in bullets if b.alive]
            tanks = [t for t in tanks if t.alive]
            walls = [w for w in walls if w.alive]

        # 6. МАЛЮВАННЯ
        screen.fill(BG_COLOR)

        pygame.draw.rect(screen, HUD_COLOR, (GAME_W, 0, SIDE_W, WIN_H))
        score_text = font.render(f"SCORE: {score}", True, WHITE)
        screen.blit(score_text, (GAME_W + 10, 50))

        # Підказка в грі
        esc_text = font.render("ESC: Меню", True, (150, 150, 150))
        screen.blit(esc_text, (GAME_W + 10, WIN_H - 40))

        for w in walls: w.draw(screen)
        eagle.draw(screen)
        for t in tanks: t.draw(screen)
        for b in bullets: b.draw(screen)

        if game_over:
            go_text = font.render("GAME OVER [R - Рестарт]", True, (255, 50, 50))
            screen.blit(go_text, (GAME_W // 2 - 120, GAME_H // 2))

        pygame.display.flip()
        clock.tick(FPS)

    return "menu"


# ================================
# СТАРТ ПРОГРАМИ
# ================================
if __name__ == "__main__":
    while True:
        # Спочатку показуємо меню
        action = main_menu()

        # Якщо повернулося "exit", перериваємо загальний цикл і йдемо до pygame.quit()
        if action == "exit" or action == "quit":
            break

        # Якщо натиснули "PLAY", запускаємо гру
        elif action == "play":
            game_result = main()
            # Якщо з гри повернулося "quit" (натиснули хрестик на вікні), закриваємо програму
            if game_result == "quit":
                break

    # Коректний вихід з Pygame тільки тут, наприкінці
    pygame.quit()