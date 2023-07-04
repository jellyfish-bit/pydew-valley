import pygame
from settings import *
from timer import Timer
from random import randint, choice


class Generic(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups, z=LAYERS["main"]):
        super().__init__(groups)
        self.z = z
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.2, -self.rect.height * 0.75)


class Interaction(Generic):
    def __init__(self, pos, size, groups, name):
        surf = pygame.Surface(size)
        super().__init__(pos, surf, groups)
        self.name = name


class SleepingOverlay(Generic):
    def __init__(self, pos, surf, groups, z):
        super().__init__(pos, surf, groups, z)
        self.sleeping_att = False



class Water(Generic):
    def __init__(self, pos, frames, groups):
        self.frames = frames
        self.frame_index = 0

        super().__init__(pos, self.frames[self.frame_index], groups, LAYERS["water"])

    def animate(self, dt):
        self.frame_index += 4 * dt
        if self.frame_index > len(self.frames):
            self.frame_index = 0

        self.image = self.frames[int(self.frame_index)]

    def update(self, dt):
        self.animate(dt)


class WildFlower(Generic):
    def __init__(self, pos, surf, groups):
        super().__init__(pos, surf, groups)
        self.hitbox = self.rect.copy().inflate(-20, -self.rect.height * 0.9)


class Tree(Generic):
    def __init__(self, pos, surf, groups, all_sprites, name, player_add):
        super().__init__(pos, surf, groups)
        self.all_sprites = all_sprites

        # tree attributes
        self.health = 5
        self.alive = True
        self.stump_surf = pygame.image.load(f"../assets/textures/stumps/{name.lower()}.png").convert_alpha()

        # apples
        self.apple_surf = pygame.image.load("../assets/textures/fruit/apple.png")
        self.apples_pos = APPLE_POS[name]
        self.apple_sprites = pygame.sprite.Group()
        self.create_fruit()

        self.axe_sound = pygame.mixer.Sound("../assets/sound/axe.mp3")

        self.player_add = player_add

    def create_fruit(self):
        for pos in self.apples_pos:
            if randint(0, 10) < 2:
                x = pos[0] + self.rect.left
                y = pos[1] + self.rect.top

                Generic((x, y), self.apple_surf, [self.all_sprites, self.apple_sprites], LAYERS["fruit"])

    def damage(self):
        self.health -= 1
        self.player_add("wood")

        self.axe_sound.play()

        if len(self.apple_sprites.sprites()) > 0:
            random_apple = choice(self.apple_sprites.sprites())
            Particle(random_apple.rect.topleft, random_apple.image, self.all_sprites, LAYERS["fruit"])
            random_apple.kill()
            self.player_add("apple")

    def check_death(self):
        if self.health <= 0:
            Particle(self.rect.topleft, self.image, self.all_sprites, LAYERS["fruit"], 300)
            self.alive = False
            self.image = self.stump_surf
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)
            self.hitbox = self.rect.copy().inflate(-10, -self.rect.height * 0.6)
            self.player_add("wood", randint(1, 3))

    def update(self, dt):
        if self.alive:
            self.check_death()


class Particle(Generic):
    def __init__(self, pos, surf, groups, z, duration=200):
        super().__init__(pos, surf, groups, z)

        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        mask_surf = pygame.mask.from_surface(self.image)
        new_surf = mask_surf.to_surface()
        new_surf.set_colorkey((0, 0, 0))
        self.image = new_surf

    def update(self, dt):
        current_time = pygame.time.get_ticks()
        if current_time - self.start_time > self.duration:
            self.kill()
