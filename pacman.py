#!/usr/bin/env python3
"""
Classic Pacman Game - Классическая игра Пакман
Красивая игра с исправленным движением и классическим дизайном
"""

import pygame
import sys
from enum import Enum
from typing import List
import random
import math


# Константы игры
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
TILE_SIZE = 25
MAP_WIDTH = 25
MAP_HEIGHT = 21
FPS = 60
MOVE_DELAY = 8  # Задержка между движениями для контроля

# Цвета в стиле классического Pacman
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE_WALL = (0, 0, 255)
LIGHT_BLUE = (173, 216, 230)
PACMAN_YELLOW = (255, 255, 0)
DOT_YELLOW = (255, 215, 0)
BIG_DOT_YELLOW = (255, 255, 102)
RED_GHOST = (255, 0, 0)
PINK_GHOST = (255, 184, 255)
CYAN_GHOST = (0, 255, 255)
ORANGE_GHOST = (255, 184, 82)
GREEN_EXIT = (0, 255, 0)
UI_COLOR = (255, 255, 0)
SCORE_COLOR = (255, 255, 255)


class TileType(Enum):
    """Типы тайлов на карте"""
    EMPTY = '0'
    WALL = '1'
    DOT = '.'
    BIG_DOT = 'o'
    COLLECTIBLE = 'C'
    EXIT = 'E'
    PLAYER = 'P'
    ENEMY = 'X'


class Direction(Enum):
    """Направления движения"""
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


class Game:
    """Основной класс игры"""

    def __init__(self):
        """Инициализация игры"""
        pygame.init()

        # Настройка окна
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(
            "🟡 PACMAN GAME 🟡 - WASD движение, ESC выход")

        # Шрифты
        self.big_font = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        self.clock = pygame.time.Clock()

        # Состояние игры
        self.running = True
        self.moves_count = 0
        self.score = 0
        self.game_won = False
        self.game_lost = False

        # Игровые объекты
        self.player = None
        self.enemies = []
        self.dots = []
        self.big_dots = []
        self.exits = []

        # Карта и позиционирование
        self.game_map = []
        self.map_offset_x = (WINDOW_WIDTH - MAP_WIDTH * TILE_SIZE) // 2
        self.map_offset_y = 100

        # Анимация и управление
        self.animation_timer = 0
        self.move_timer = 0
        self.last_direction = None
        self.pending_direction = None

        # Визуальные эффекты
        self.screen_flash = 0
        self.victory_animation = 0

        self._load_classic_map()
        self._find_game_objects()

    def _load_classic_map(self):
        """Загружает карту в классическом стиле Pacman"""
        classic_map = [
            "1111111111111111111111111",
            "1............1..........1",
            "1o111.111111.1.11111.111o1",
            "1.......................1",
            "1.111.1.111111111.1.111.1",
            "1.....1.....1.....1.....1",
            "1111.11111.111.11111.1111",
            "0001.1.....X.X.....1.1000",
            "1111.1.111.....111.1.1111",
            "1......1.........1......1",
            "1.1111.1111.1.1111.1111.1",
            "1.....C...1.P.1...C.....1",
            "1111111.1.1...1.1.1111111",
            "1......1.1.111.1.1......1",
            "1.1111.1...111...1.1111.1",
            "1.1..1.11111111111.1..1.1",
            "1.1..1.................1",
            "1.1..1.111.111.111.1..1.1",
            "1......1.........1......1",
            "1o1111111.11111.1111111o1",
            "1.........1.E.1.........1",
            "1111111111111111111111111"
        ]

        self.game_map = []
        i = 0
        while i < len(classic_map):
            row = []
            j = 0
            while j < len(classic_map[i]):
                row.append(classic_map[i][j])
                j += 1
            self.game_map.append(row)
            i += 1

    def _find_game_objects(self):
        """Находит игровые объекты на карте"""
        self.dots = []
        self.big_dots = []
        self.exits = []
        self.enemies = []

        y = 0
        while y < len(self.game_map):
            x = 0
            while x < len(self.game_map[y]):
                tile = self.game_map[y][x]
                if tile == TileType.PLAYER.value:
                    self.player = Player(x, y)
                    self.game_map[y][x] = TileType.EMPTY.value
                elif tile == TileType.DOT.value:
                    self.dots.append((x, y))
                elif tile == 'o':  # Большие точки
                    self.big_dots.append((x, y))
                    self.game_map[y][x] = TileType.EMPTY.value
                elif tile == TileType.COLLECTIBLE.value:
                    self.dots.append((x, y))  # Превращаем в обычные точки
                    self.game_map[y][x] = TileType.EMPTY.value
                elif tile == TileType.EXIT.value:
                    self.exits.append((x, y))
                elif tile == TileType.ENEMY.value:
                    # Создаем разноцветных призраков
                    ghost_color = len(self.enemies) % 4
                    self.enemies.append(Enemy(x, y, ghost_color))
                    self.game_map[y][x] = TileType.EMPTY.value
                x += 1
            y += 1

    def handle_input(self):
        """Улучшенная обработка ввода"""
        keys = pygame.key.get_pressed()

        # Определяем желаемое направление
        new_direction = None
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            new_direction = Direction.UP
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            new_direction = Direction.DOWN
        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
            new_direction = Direction.LEFT
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            new_direction = Direction.RIGHT

        # Сохраняем направление для следующего движения
        if new_direction:
            self.pending_direction = new_direction

        # Двигаемся только через определенные интервалы
        if self.move_timer <= 0 and self.pending_direction:
            if self._can_move_in_direction(self.pending_direction):
                self._move_player(self.pending_direction)
                self.move_timer = MOVE_DELAY
                self.last_direction = self.pending_direction
            # Если не можем идти в желаемом направлении, продолжаем в текущем
            elif (self.last_direction and
                  self._can_move_in_direction(self.last_direction)):
                self._move_player(self.last_direction)
                self.move_timer = MOVE_DELAY

    def _can_move_in_direction(self, direction: Direction) -> bool:
        """Проверяет, можно ли двигаться в указанном направлении"""
        if not self.player:
            return False

        new_x = self.player.x + direction.value[0]
        new_y = self.player.y + direction.value[1]

        # Проверка границ
        if (new_x < 0 or new_x >= MAP_WIDTH or
                new_y < 0 or new_y >= MAP_HEIGHT):
            return False

        # Проверка стен
        return self.game_map[new_y][new_x] != TileType.WALL.value

    def _move_player(self, direction: Direction):
        """Перемещение игрока"""
        if not self.player or self.game_won or self.game_lost:
            return

        new_x = self.player.x + direction.value[0]
        new_y = self.player.y + direction.value[1]

        # Перемещение игрока
        self.player.x = new_x
        self.player.y = new_y
        self.player.direction = direction
        self.moves_count += 1

        # Проверка сбора точек
        self._check_dots()
        self._check_big_dots()

        # Проверка выхода
        self._check_exits()

        # Проверка столкновения с врагами
        self._check_enemy_collision()

    def _check_dots(self):
        """Проверка сбора обычных точек"""
        i = 0
        while i < len(self.dots):
            dot_x, dot_y = self.dots[i]
            if self.player.x == dot_x and self.player.y == dot_y:
                self.dots.pop(i)
                self.score += 10
            else:
                i += 1

    def _check_big_dots(self):
        """Проверка сбора больших точек"""
        i = 0
        while i < len(self.big_dots):
            dot_x, dot_y = self.big_dots[i]
            if self.player.x == dot_x and self.player.y == dot_y:
                self.big_dots.pop(i)
                self.score += 50
                # Эффект съедения большой точки
                self.screen_flash = 10
            else:
                i += 1

    def _check_exits(self):
        """Проверка достижения выхода"""
        # Выход активен только когда все точки собраны
        total_dots = len(self.dots) + len(self.big_dots)
        if total_dots == 0:
            i = 0
            while i < len(self.exits):
                exit_x, exit_y = self.exits[i]
                if self.player.x == exit_x and self.player.y == exit_y:
                    self.game_won = True
                    self.victory_animation = 120  # 2 секунды анимации
                    break
                i += 1

    def _check_enemy_collision(self):
        """Проверка столкновения с врагами"""
        i = 0
        while i < len(self.enemies):
            enemy = self.enemies[i]
            if self.player.x == enemy.x and self.player.y == enemy.y:
                self.game_lost = True
                break
            i += 1

    def update_enemies(self):
        """Обновление поведения врагов"""
        if self.game_won or self.game_lost:
            return

        i = 0
        while i < len(self.enemies):
            enemy = self.enemies[i]
            enemy.update(self.game_map, self.player, MAP_WIDTH, MAP_HEIGHT)
            i += 1

    def update_timers(self):
        """Обновление таймеров"""
        if self.move_timer > 0:
            self.move_timer -= 1

        if self.screen_flash > 0:
            self.screen_flash -= 1

        if self.victory_animation > 0:
            self.victory_animation -= 1

    def render(self):
        """Отрисовка игры"""
        # Фон
        if self.screen_flash > 0:
            self.screen.fill(WHITE)
        else:
            self.screen.fill(BLACK)

        # Отрисовка игровых элементов
        self._render_map()
        self._render_dots()
        self._render_enemies()
        self._render_player()

        # UI всегда сверху
        self._render_ui()

        pygame.display.flip()

    def _render_map(self):
        """Отрисовка карты в стиле классического Pacman"""
        y = 0
        while y < len(self.game_map):
            x = 0
            while x < len(self.game_map[y]):
                tile = self.game_map[y][x]
                screen_x = self.map_offset_x + x * TILE_SIZE
                screen_y = self.map_offset_y + y * TILE_SIZE

                if tile == TileType.WALL.value:
                    # Рисуем стену в стиле Pacman с объемом
                    wall_rect = pygame.Rect(screen_x, screen_y,
                                            TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(self.screen, BLUE_WALL, wall_rect)

                    # Добавляем светлую границу для объема
                    pygame.draw.rect(self.screen, LIGHT_BLUE, wall_rect, 1)

                    # Внутренняя подсветка
                    inner_rect = pygame.Rect(screen_x + 2, screen_y + 2,
                                             TILE_SIZE - 4, TILE_SIZE - 4)
                    pygame.draw.rect(self.screen, LIGHT_BLUE, inner_rect, 1)
                x += 1
            y += 1

    def _render_dots(self):
        """Отрисовка точек"""
        # Обычные точки
        i = 0
        while i < len(self.dots):
            x, y = self.dots[i]
            screen_x = self.map_offset_x + x * TILE_SIZE + TILE_SIZE // 2
            screen_y = self.map_offset_y + y * TILE_SIZE + TILE_SIZE // 2
            pygame.draw.circle(self.screen, DOT_YELLOW,
                               (screen_x, screen_y), 2)
            i += 1

        # Большие точки с анимацией
        i = 0
        while i < len(self.big_dots):
            x, y = self.big_dots[i]
            screen_x = self.map_offset_x + x * TILE_SIZE + TILE_SIZE // 2
            screen_y = self.map_offset_y + y * TILE_SIZE + TILE_SIZE // 2

            # Пульсирующий эффект
            pulse = math.sin(self.animation_timer * 0.2) * 0.3 + 0.7
            radius = int(8 * pulse)
            pygame.draw.circle(self.screen, BIG_DOT_YELLOW,
                               (screen_x, screen_y), radius)
            i += 1

        # Выходы
        i = 0
        while i < len(self.exits):
            x, y = self.exits[i]
            screen_x = self.map_offset_x + x * TILE_SIZE
            screen_y = self.map_offset_y + y * TILE_SIZE

            # Выход активен только когда все точки собраны
            total_dots = len(self.dots) + len(self.big_dots)
            if total_dots == 0:
                # Активный выход - мигающий зеленый
                alpha = math.sin(self.animation_timer * 0.3) * 0.5 + 0.5
                color = (0, int(255 * alpha), 0)
            else:
                # Неактивный выход - серый
                color = (64, 64, 64)

            exit_rect = pygame.Rect(screen_x + 3, screen_y + 3,
                                    TILE_SIZE - 6, TILE_SIZE - 6)
            pygame.draw.rect(self.screen, color, exit_rect)
            pygame.draw.rect(self.screen, WHITE, exit_rect, 2)
            i += 1

    def _render_player(self):
        """Отрисовка Pacman с красивой анимацией"""
        if not self.player:
            return

        screen_x = (self.map_offset_x + self.player.x * TILE_SIZE +
                    TILE_SIZE // 2)
        screen_y = (self.map_offset_y + self.player.y * TILE_SIZE +
                    TILE_SIZE // 2)

        # Размер Pacman
        radius = TILE_SIZE // 2 - 2

        # Анимация рта
        mouth_cycle = (self.animation_timer % 20) / 20.0
        mouth_open = math.sin(mouth_cycle * math.pi * 2) > 0

        if mouth_open:
            # Открытый рот
            mouth_angle = 60  # градусы

            # Направление рта в зависимости от движения
            start_angle = 0
            if self.player.direction == Direction.RIGHT:
                start_angle = -mouth_angle // 2
            elif self.player.direction == Direction.LEFT:
                start_angle = 180 - mouth_angle // 2
            elif self.player.direction == Direction.UP:
                start_angle = 270 - mouth_angle // 2
            elif self.player.direction == Direction.DOWN:
                start_angle = 90 - mouth_angle // 2

            # Основной круг
            pygame.draw.circle(self.screen, PACMAN_YELLOW,
                               (screen_x, screen_y), radius)

            # Вырезаем рот
            mouth_points = [
                (screen_x, screen_y)
            ]

            # Добавляем точки дуги для рта
            num_points = 10
            j = 0
            while j < num_points:
                angle = math.radians(start_angle +
                                     (mouth_angle * j / (num_points - 1)))
                point_x = screen_x + radius * math.cos(angle)
                point_y = screen_y + radius * math.sin(angle)
                mouth_points.append((point_x, point_y))
                j += 1

            if len(mouth_points) > 2:
                pygame.draw.polygon(self.screen, BLACK, mouth_points)
        else:
            # Закрытый рот - просто круг
            pygame.draw.circle(self.screen, PACMAN_YELLOW,
                               (screen_x, screen_y), radius)

        # Глаз
        eye_x = screen_x - 3
        eye_y = screen_y - 5
        if self.player.direction == Direction.LEFT:
            eye_x = screen_x + 3

        pygame.draw.circle(self.screen, BLACK, (eye_x, eye_y), 2)

    def _render_enemies(self):
        """Отрисовка призраков в классическом стиле"""
        ghost_colors = [RED_GHOST, PINK_GHOST, CYAN_GHOST, ORANGE_GHOST]

        i = 0
        while i < len(self.enemies):
            enemy = self.enemies[i]
            color = ghost_colors[enemy.color % len(ghost_colors)]

            screen_x = (self.map_offset_x + enemy.x * TILE_SIZE +
                        TILE_SIZE // 2)
            screen_y = (self.map_offset_y + enemy.y * TILE_SIZE +
                        TILE_SIZE // 2)

            # Размер призрака
            size = TILE_SIZE // 2 - 1

            # Тело призрака (полукруг сверху + прямоугольник)
            body_rect = pygame.Rect(screen_x - size, screen_y - size,
                                    size * 2, size * 2)
            pygame.draw.rect(self.screen, color, body_rect)
            pygame.draw.circle(self.screen, color,
                               (screen_x, screen_y - size // 2), size)

            # Зубчатый низ призрака
            teeth_y = screen_y + size
            num_teeth = 4
            tooth_width = (size * 2) // num_teeth

            j = 0
            while j < num_teeth:
                tooth_x = screen_x - size + j * tooth_width
                if j % 2 == 0:
                    tooth_points = [
                        (tooth_x, teeth_y),
                        (tooth_x + tooth_width // 2,
                         teeth_y - tooth_width // 2),
                        (tooth_x + tooth_width, teeth_y)
                    ]
                    pygame.draw.polygon(self.screen, color, tooth_points)
                j += 1

            # Глаза призрака
            eye_size = 4
            left_eye_x = screen_x - size // 2
            right_eye_x = screen_x + size // 2
            eyes_y = screen_y - size // 2

            # Белки глаз
            pygame.draw.circle(self.screen, WHITE, (left_eye_x, eyes_y),
                               eye_size)
            pygame.draw.circle(self.screen, WHITE, (right_eye_x, eyes_y),
                               eye_size)

            # Зрачки (смотрят на игрока если он рядом)
            pupil_size = 2
            pupil_offset = 1

            if enemy.chase_mode and self.player:
                # Зрачки следят за игроком
                dx = self.player.x - enemy.x
                dy = self.player.y - enemy.y
                if abs(dx) > abs(dy):
                    pupil_x_offset = pupil_offset if dx > 0 else -pupil_offset
                    pupil_y_offset = 0
                else:
                    pupil_x_offset = 0
                    pupil_y_offset = pupil_offset if dy > 0 else -pupil_offset
            else:
                pupil_x_offset, pupil_y_offset = 0, 0

            pygame.draw.circle(self.screen, BLACK,
                               (left_eye_x + pupil_x_offset,
                                eyes_y + pupil_y_offset),
                               pupil_size)
            pygame.draw.circle(self.screen, BLACK,
                               (right_eye_x + pupil_x_offset,
                                eyes_y + pupil_y_offset),
                               pupil_size)
            i += 1

    def _render_ui(self):
        """Красивый пользовательский интерфейс"""
        # Верхняя панель
        ui_rect = pygame.Rect(0, 0, WINDOW_WIDTH, 80)
        pygame.draw.rect(self.screen, BLACK, ui_rect)
        pygame.draw.line(self.screen, UI_COLOR, (0, 80),
                         (WINDOW_WIDTH, 80), 2)

        # Заголовок
        title_text = self.big_font.render("🟡 P A C M A N 🟡", True, UI_COLOR)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 25))
        self.screen.blit(title_text, title_rect)

        # Счетчики
        score_text = self.font.render(f"SCORE: {self.score:05d}",
                                      True, SCORE_COLOR)
        self.screen.blit(score_text, (20, 50))

        moves_text = self.font.render(f"MOVES: {self.moves_count}",
                                      True, SCORE_COLOR)
        self.screen.blit(moves_text, (250, 50))

        total_dots = len(self.dots) + len(self.big_dots)
        dots_text = self.font.render(f"DOTS: {total_dots}", True, SCORE_COLOR)
        dots_rect = dots_text.get_rect(topright=(WINDOW_WIDTH - 20, 50))
        self.screen.blit(dots_text, dots_rect)

        # Нижняя панель с инструкциями
        bottom_y = WINDOW_HEIGHT - 50
        instruction_text = self.small_font.render(
            "WASD / СТРЕЛКИ - движение  •  ESC - выход  •  "
            "Собирайте все точки!",
            True, UI_COLOR)
        instruction_rect = instruction_text.get_rect(
            center=(WINDOW_WIDTH // 2, bottom_y))
        self.screen.blit(instruction_text, instruction_rect)

        # Сообщения о состоянии игры
        if self.game_won:
            if self.victory_animation > 60:
                # Анимация победы
                flash_alpha = int(255 * abs(math.sin(
                    self.animation_timer * 0.5)))
                win_color = (255, flash_alpha, 0)
            else:
                win_color = UI_COLOR

            win_text = self.big_font.render(
                f"🏆 VICTORY! FINAL SCORE: {self.score} 🏆", True, win_color)
            win_rect = win_text.get_rect(center=(WINDOW_WIDTH // 2,
                                                 WINDOW_HEIGHT // 2))

            # Фон для сообщения
            bg_rect = pygame.Rect(win_rect.x - 20, win_rect.y - 15,
                                  win_rect.width + 40, win_rect.height + 30)
            pygame.draw.rect(self.screen, BLACK, bg_rect)
            pygame.draw.rect(self.screen, win_color, bg_rect, 3)

            self.screen.blit(win_text, win_rect)

        elif self.game_lost:
            lose_text = self.big_font.render(
                f"👻 GAME OVER! SCORE: {self.score} 👻", True, RED_GHOST)
            lose_rect = lose_text.get_rect(center=(WINDOW_WIDTH // 2,
                                                   WINDOW_HEIGHT // 2))

            # Фон для сообщения
            bg_rect = pygame.Rect(lose_rect.x - 20, lose_rect.y - 15,
                                  lose_rect.width + 40, lose_rect.height + 30)
            pygame.draw.rect(self.screen, BLACK, bg_rect)
            pygame.draw.rect(self.screen, RED_GHOST, bg_rect, 3)

            self.screen.blit(lose_text, lose_rect)

        elif total_dots == 0:
            exit_text = self.font.render(
                "✨ ALL DOTS COLLECTED! GO TO GREEN EXIT! ✨", True, GREEN_EXIT)
            exit_rect = exit_text.get_rect(center=(WINDOW_WIDTH // 2,
                                                   self.map_offset_y - 15))

            # Мигающий фон
            if int(self.animation_timer / 15) % 2:
                bg_rect = pygame.Rect(exit_rect.x - 10, exit_rect.y - 5,
                                      exit_rect.width + 20,
                                      exit_rect.height + 10)
                pygame.draw.rect(self.screen, (0, 50, 0), bg_rect)

            self.screen.blit(exit_text, exit_rect)

    def run(self):
        """Основной игровой цикл"""
        print("🟡 Добро пожаловать в PACMAN! 🟡")
        print("Управление: WASD или стрелки")
        print("Цель: собрать все точки и дойти до зеленого выхода")
        print("Избегайте красных призраков!")
        print("-" * 50)

        while self.running:
            # Обработка событий
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            # Обновление игры
            self.handle_input()
            self.update_enemies()
            self.update_timers()

            # Увеличиваем счетчик анимации
            self.animation_timer += 1

            # Отрисовка
            self.render()

            # Ограничение FPS
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


class Player:
    """Класс игрока Pacman"""

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.direction = Direction.RIGHT


class Enemy:
    """Класс призрака-врага"""

    def __init__(self, x: int, y: int, color: int = 0):
        self.x = x
        self.y = y
        self.color = color
        self.direction = Direction.RIGHT
        self.timer = 0
        self.chase_mode = False
        self.stuck_timer = 0

    def update(self, game_map: List[List[str]], player, map_width: int,
               map_height: int):
        """Обновление поведения призрака"""
        self.timer += 1

        # Определяем режим преследования
        distance = abs(self.x - player.x) + abs(self.y - player.y)
        self.chase_mode = distance <= 7

        # Двигаемся каждые 20 кадров (медленнее игрока)
        if self.timer % 20 == 0:
            old_x, old_y = self.x, self.y

            if self.chase_mode:
                self._chase_player(game_map, player, map_width, map_height)
            else:
                self._wander(game_map, map_width, map_height)

            # Проверка на застревание
            if old_x == self.x and old_y == self.y:
                self.stuck_timer += 1
                if self.stuck_timer > 2:
                    self._force_move(game_map, map_width, map_height)
                    self.stuck_timer = 0
            else:
                self.stuck_timer = 0

    def _chase_player(self, game_map: List[List[str]], player,
                      map_width: int, map_height: int):
        """Преследование игрока"""
        directions = [Direction.UP, Direction.DOWN,
                      Direction.LEFT, Direction.RIGHT]
        best_direction = None
        min_distance = float('inf')

        i = 0
        while i < len(directions):
            direction = directions[i]
            new_x = self.x + direction.value[0]
            new_y = self.y + direction.value[1]

            if self._is_valid_move(new_x, new_y, game_map,
                                   map_width, map_height):
                distance = abs(new_x - player.x) + abs(new_y - player.y)
                if distance < min_distance:
                    min_distance = distance
                    best_direction = direction
            i += 1

        if best_direction:
            self.x += best_direction.value[0]
            self.y += best_direction.value[1]
            self.direction = best_direction

    def _wander(self, game_map: List[List[str]], map_width: int,
                map_height: int):
        """Случайное блуждание"""
        # Пробуем продолжить в текущем направлении
        new_x = self.x + self.direction.value[0]
        new_y = self.y + self.direction.value[1]

        if self._is_valid_move(new_x, new_y, game_map, map_width, map_height):
            # 70% шанс продолжить прямо
            if random.random() < 0.7:
                self.x = new_x
                self.y = new_y
                return

        # Иначе выбираем случайное направление
        directions = [Direction.UP, Direction.DOWN,
                      Direction.LEFT, Direction.RIGHT]
        valid_directions = []

        i = 0
        while i < len(directions):
            direction = directions[i]
            new_x = self.x + direction.value[0]
            new_y = self.y + direction.value[1]

            if self._is_valid_move(new_x, new_y, game_map,
                                   map_width, map_height):
                valid_directions.append(direction)
            i += 1

        if valid_directions:
            chosen_direction = valid_directions[
                random.randint(0, len(valid_directions) - 1)]
            self.x += chosen_direction.value[0]
            self.y += chosen_direction.value[1]
            self.direction = chosen_direction

    def _force_move(self, game_map: List[List[str]], map_width: int,
                    map_height: int):
        """Принудительное движение при застревании"""
        directions = [Direction.UP, Direction.DOWN,
                      Direction.LEFT, Direction.RIGHT]

        i = 0
        while i < len(directions):
            direction = directions[i]
            new_x = self.x + direction.value[0]
            new_y = self.y + direction.value[1]

            if self._is_valid_move(new_x, new_y, game_map,
                                   map_width, map_height):
                self.x = new_x
                self.y = new_y
                self.direction = direction
                break
            i += 1

    def _is_valid_move(self, x: int, y: int, game_map: List[List[str]],
                       map_width: int, map_height: int) -> bool:
        """Проверяет валидность хода"""
        if x < 0 or x >= map_width or y < 0 or y >= map_height:
            return False
        return game_map[y][x] != TileType.WALL.value


def main():
    """Основная функция"""
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"Ошибка в игре: {e}")
        pygame.quit()
        sys.exit(1)


if __name__ == "__main__":
    main()
