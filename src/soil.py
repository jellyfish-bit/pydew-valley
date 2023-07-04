import pygame
from settings import *
from pytmx.util_pygame import load_pygame
from support import *
from random import choice


class SoilTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = LAYERS["soil"]


class WaterTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = LAYERS["soil water"]


class Plant(pygame.sprite.Sprite):
    def __init__(self, plant_type, groups, soil, check_watered):
        super().__init__(groups)

        # setup
        self.plant_type = plant_type
        self.frames = import_folder(f"../assets/textures/fruit/{plant_type}")
        self.soil = soil
        self.check_watered = check_watered

        # plant growing
        self.age = 0
        self.max_age = len(self.frames)-1
        self.grow_speed = GROW_SPEED[plant_type]
        self.harvestable = False

        self.image = self.frames[self.age]
        self.y_offset = -16 if plant_type == "corn" else -8
        self.rect = self.image.get_rect(midbottom=soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))
        self.z = LAYERS["ground plant"]

    def grow(self):
        if self.check_watered(self.rect.center):
            self.age += self.grow_speed

            if self.age >= 1:
                self.z = LAYERS["main"]
                # todo may change when collision
                self.hitbox = self.rect.copy().inflate(-26, self.rect.height * -0.4)


            if self.age >= self.max_age:
                self.age = self.max_age
                self.harvestable = True
            self.image = self.frames[int(self.age)]
            self.rect = self.image.get_rect(midbottom=self.soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))


class SoilLayer:
    def __init__(self, all_sprites, collision_spites):
        # sprite groups
        self.all_sprites = all_sprites
        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sprites = pygame.sprite.Group()
        self.collision_spites = collision_spites

        # graphics
        self.soil_surfs = import_folder_dict("../assets/textures/soil/")
        self.water_surfs = import_folder("../assets/textures/soil_water/")

        self.create_soil_grid()
        self.create_hit_reacts()

        self.hoe_sound = pygame.mixer.Sound("../assets/sound/hoe.wav")
        self.hoe_sound.set_volume(0.1)
        self.plant_sound = pygame.mixer.Sound("../assets/sound/plant.wav")
        self.plant_sound.set_volume(0.1)

    def create_soil_grid(self):
        ground = pygame.image.load("../assets/textures/world/ground.png")
        h_tiles, v_tiles = ground.get_width() // TILE_SIZE, ground.get_height() // TILE_SIZE

        self.grid = [
            [
                [] for col in range(h_tiles)
            ] for row in range(v_tiles)
        ]
        for x, y, _ in load_pygame("../assets/data/map.tmx").get_layer_by_name("Farmable").tiles():
            self.grid[y][x].append("F")

    def create_hit_reacts(self):
        self.hit_rects = []
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if "F" in cell:
                    x = index_col * TILE_SIZE
                    y = index_row * TILE_SIZE
                    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    self.hit_rects.append(rect)

    def get_hit(self, point):
        for rect in self.hit_rects:
            if rect.collidepoint(point):
                x = rect.x // TILE_SIZE
                y = rect.y // TILE_SIZE

                if "F" in self.grid[y][x]:
                    self.grid[y][x].append("X")
                    self.create_soil_tiles()
                    if self.raining:
                        self.water_all()

                self.hoe_sound.play()

    def water(self, target_pos):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):
                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE
                self.grid[y][x].append("W")

                WaterTile(soil_sprite.rect.topleft, choice(self.water_surfs), [self.all_sprites, self.water_sprites])

    def water_all(self):
        #todo make percent
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if "X" in cell and "W" not in cell:
                    cell.append("W")
                    x = index_col * TILE_SIZE
                    y = index_row * TILE_SIZE
                    WaterTile((x, y), choice(self.water_surfs), [self.all_sprites, self.water_sprites])

    def remove_water(self):
        for sprite in self.water_sprites.sprites():
            sprite.kill()
        for row in self.grid:
            for cell in row:
                if "W" in cell:
                    cell.remove("W")

    def check_watered(self, pos):
        x = pos[0] // TILE_SIZE
        y = pos[1] // TILE_SIZE
        cell = self.grid[y][x]
        is_watered = "W" in cell
        return is_watered

    def plant_seed(self, targe_pos, seed):
        for soil_spite in self.soil_sprites.sprites():
            if soil_spite.rect.collidepoint(targe_pos):
                x = soil_spite.rect.x // TILE_SIZE
                y = soil_spite.rect.y // TILE_SIZE

                if "P" not in self.grid[y][x]:
                    self.grid[y][x].append("P")
                    Plant(seed, [self.all_sprites, self.plant_sprites, self.collision_spites], soil_spite, self.check_watered)
                self.plant_sound.play()

    def update_plants(self):
        for plant in self.plant_sprites.sprites():
            plant.grow()

    def create_soil_tiles(self):
        self.soil_sprites.empty()
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if "X" in cell:
                    # tile options
                    top = "X" in self.grid[index_row - 1][index_col]
                    bottom = "X" in self.grid[index_row + 1][index_col]
                    right = "X" in row[index_col + 1]
                    left = "X" in row[index_col - 1]
                    tile_type = get_tile_type(top, bottom, right, left)

                    SoilTile((index_col * TILE_SIZE, index_row * TILE_SIZE), self.soil_surfs[tile_type],
                             [self.all_sprites, self.soil_sprites])


def get_tile_type(top, bottom, right, left):
    tile_type = "o"

    # all sides
    if all((top, bottom, right, left)):
        tile_type = "x"

    # horizontal
    if left and not any((right, top, bottom)):
        tile_type = "r"
    if right and not any((left, top, bottom)):
        tile_type = "l"
    if right and left and not any((top, bottom)):
        tile_type = "lr"

    # vertical
    if top and not any((bottom, left, right)):
        tile_type = "b"
    if bottom and not any((top, left, right)):
        tile_type = "t"
    if top and bottom and not any((left, right)):
        tile_type = "tb"

    # cornes
    if left and bottom and not any((top, right)):
        tile_type = "tr"
    if right and bottom and not any((top, left)):
        tile_type = "tl"
    if left and top and not any((bottom, right)):
        tile_type = "br"
    if right and top and not any((bottom, left)):
        tile_type = "bl"

    # T shape
    if all((top, bottom, right)) and not left:
        tile_type = "tbr"
    if all((top, bottom, left)) and not right:
        tile_type = "tbl"
    if all((top, right, left)) and not bottom:
        tile_type = "lrb"
    if all((bottom, right, left)) and not top:
        tile_type = "lrt"

    return tile_type
