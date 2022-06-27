import pygame
import random
import cv2

GREY = (150, 150, 150)
DARK_GREY = (80, 80, 80)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (255, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
BROWN = (120, 60, 0)
BLACK = (0, 0, 0)
DARK_GREEN = (0, 160, 0)
BACKGROUND = GREY

SIZE = (800, 600)
CHART_SIZE = (600, 600)
BOX_SIZE = (40, 40)
STARTING_AREA_RADIUS = (1, 1)

pygame.font.init()
FONT = pygame.font.SysFont("monospace", 20, True)
MINE, FLAG, OPENED, UNOPENED = (pygame.transform.scale(pygame.image.load(path),BOX_SIZE) for path in ("images/mine.png", "images/flag.png", "images/opened.png", "images/unopened.png"))

FPS = 60
MINE_COUNT = 30
END_DELAY = 2

GAME_OVER = -1
YOU_WIN = 1


class Box(pygame.sprite.Sprite):
    mine_colors = BLUE, GREEN, RED, PURPLE, YELLOW, CYAN, BROWN, BLACK

    def __init__(self, y, x):
        self.image = pygame.Surface(BOX_SIZE,pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.mined = False
        self.opened = False
        self.flagged = False
        self.mines_around = 0

    def fill_the_image(self, image):
        self.image.blit(image,(0,0))

    def update(self):
        if self.opened and self.mined:
            self.fill_the_image(OPENED)
            self.fill_the_image(MINE)
        elif self.opened:
            self.fill_the_image(OPENED)
            self.print_mines_around_count()
        elif self.flagged:
            self.fill_the_image(UNOPENED)
            self.fill_the_image(FLAG)
        else:
            self.fill_the_image(UNOPENED)

    def is_clicked(self, mouse_pos):
        if mouse_pos is None:
            return False  # for avoiding errors
        if self.rect.collidepoint(*mouse_pos):
            return True
        return False

    def open(self):
        self.opened = True

    def print_mines_around_count(self):
        if not self.mines_around:
            return
        text = FONT.render(str(self.mines_around), True,
                           self.mine_colors[self.mines_around - 1])
        rect = text.get_rect()
        rect.center = BOX_SIZE[0]//2, BOX_SIZE[1]//2
        self.image.blit(text, rect)


class Chart(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.chart = [[Box(y, x) for x in range(0, CHART_SIZE[0], BOX_SIZE[0])]
                      for y in range(0, CHART_SIZE[1], BOX_SIZE[1])]
        self.image = pygame.Surface(CHART_SIZE)
        self.rect = self.image.get_rect()
        self.rect.x = self.rect.y = 0
        self.first_click = True
        self.flags = MINE_COUNT

    def place_mines(self, y, x):
        boxes = [box for y in self.chart for box in y if not box.opened]
        for _y in range(-STARTING_AREA_RADIUS[1], STARTING_AREA_RADIUS[1]+1):
            for _x in range(-STARTING_AREA_RADIUS[0], STARTING_AREA_RADIUS[0]+1):
                if not 0 <= y+_y < len(self.chart) or not 0 <= x+_x < len(self.chart[0]):
                    continue
                boxes.remove(self.chart[y+_y][x+_x])
        for _ in range(MINE_COUNT):
            box = random.choice(boxes)
            boxes.remove(box)
            box.mined = True

    def update(self, mouse_pos, mouse_btn):
        self.you_win()
        if mouse_pos is not None:
            x = mouse_pos[0] // BOX_SIZE[0]
            y = mouse_pos[1] // BOX_SIZE[1]
            if self.first_click:
                self.first_click = False
                self.start(y, x)
            elif mouse_btn == pygame.BUTTON_LEFT:
                self.open(y, x)
            elif mouse_btn == pygame.BUTTON_RIGHT:
                self.flag(y, x)
        for y, line in enumerate(self.chart):
            for x, box in enumerate(line):
                box.update()
                self.image.blit(self.chart[y][x].image, self.chart[y][x].rect)

    def you_win(self):
        global game_result
        if not self.flags and all([box.mined for y in self.chart for box in y if box.flagged]) or all([box.mined for y in self.chart for box in y if not box.opened]):
            game_result = YOU_WIN
            for y in self.chart:
                for box in y:
                    if not box.mined:
                        box.open()

    def check_mines_around(self, y, x):
        counter = 0
        for _y in range(-1, 2):
            for _x in range(-1, 2):
                if not 0 <= y+_y < len(self.chart) or not 0 <= x+_x < len(self.chart[0]):
                    continue
                if self.chart[y+_y][x+_x].mined:
                    counter += 1
        return counter

    def start(self, y, x):
        self.place_mines(y, x)
        for _y, line in enumerate(self.chart):
            for _x, box in enumerate(line):
                count = self.check_mines_around(_y, _x)
                box.mines_around = count
        self.open(y, x)

    def flag(self, y, x):
        box = self.chart[y][x]
        if not box.flagged and self.flags:
            box.flagged = True
            self.flags -= 1
        else:
            box.flagged = False
            self.flags += 1

    def open(self, y, x):
        global game_result
        box = self.chart[y][x]
        if box.flagged:
            return
        if box.opened:
            return
        if box.mined:
            game_result = GAME_OVER
            for box in [box for y in self.chart for box in y if box.mined]:
                box.opened = True
        box.opened = True
        if not box.mines_around:
            for _y in range(-1, 2):
                for _x in range(-1, 2):
                    if not 0 <= y+_y < len(self.chart) or not 0 <= x+_x < len(self.chart[0]):
                        continue
                    if _y == _x == 0:
                        continue
                    self.open(y+_y, x+_x)


def show_flags_and_mines(chart: Chart, display: pygame.Surface):
    text_mines = f"Mines : {MINE_COUNT}"
    text_flags = f"Flags : {chart.flags}"
    mines = FONT.render(text_mines, True, BLACK)
    flags = FONT.render(text_flags, True, BLACK)
    display.blit(mines, (CHART_SIZE[0], 0))
    display.blit(flags, (CHART_SIZE[0], mines.get_size()[1]))


def blur(image: pygame.Surface):
    kernel = (100, 100)
    imgdata = pygame.surfarray.array3d(image)
    blured = cv2.blur(imgdata, kernel)
    image = pygame.surfarray.make_surface(blured)
    return image


def main():
    global game_result
    game_result = None
    clock = pygame.time.Clock()
    active = True
    display = pygame.display.set_mode(SIZE)
    chart = Chart()
    mouse_pos = None
    mouse_btn = None
    blurred_background = None
    counter = 0
    pygame.display.set_caption("MINESWEEPER")
    while active:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                active = False
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = ev.pos
                mouse_btn = ev.button
            else:
                mouse_pos = mouse_btn = None
        chart.update(mouse_pos, mouse_btn)
        display.fill(BACKGROUND)
        show_flags_and_mines(chart, display)
        display.blit(chart.image, chart.rect)
        if game_result:
            if counter != END_DELAY * FPS:
                counter += 1
            elif blurred_background is None:
                blurred_background = blur(display)
                if game_result == GAME_OVER:
                    text = "GAME OVER"
                elif game_result == YOU_WIN:
                    text = "YOU WIN"
                text1 = FONT.render(text, True, BLACK)
                text2 = FONT.render("Click to restart", True, BLACK)
                rect1 = text1.get_rect()
                rect1.center = SIZE[0]//2, SIZE[1]//2 - 50
                rect2 = text2.get_rect()
                rect2.center = SIZE[0]//2, SIZE[1]//2 + 50
                blurred_background.blit(text1, rect1)
                blurred_background.blit(text2, rect2)
            elif mouse_btn:
                chart = Chart()
                counter = 0
                blurred_background = None
                game_result = None
            else:
                display.blit(blurred_background, (0, 0))
        mouse_pos = None
        pygame.display.update()


main()
