import pygame
from settings import *


class Overlay:
    def __init__(self, player):
        self.dispay_surface = pygame.display.get_surface()
        self.player = player

        overlay_path = "../assets/textures/overlay/"
        self.tools_surf = {
            tool: pygame.image.load(f"{overlay_path}{tool}.png").convert_alpha() for tool in player.tools}
        self.seeds_surf = {
            seed: pygame.image.load(f"{overlay_path}{seed}.png").convert_alpha() for seed in player.seeds}

    def display(self):
        tool_surf = self.tools_surf[self.player.selected_tool]
        tool_rect = tool_surf.get_rect(midbottom=OVERLAY_POSITION["tool"])
        self.dispay_surface.blit(tool_surf, tool_rect)

        seed_surf = self.seeds_surf[self.player.selected_seed]
        seed_rect = seed_surf.get_rect(midbottom=OVERLAY_POSITION["seed"])
        self.dispay_surface.blit(seed_surf, seed_rect)
