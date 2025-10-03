"""
mapa.py.

Se encarga de cargar el mapa directamente
de la API, y dibujarlo en la pantalla.
"""

import pygame


def cargar_mapa(api):
    """Recibe el mapa de la api por parámetro."""
    ciudad_data = api.obtener_mapa()["data"]
    return ciudad_data["tiles"]


def dibujar_mapa(screen, tiles, colors, cam_x,
                 cam_y, tile_size, view_width,
                 view_height, imagenes=None):
    """Dibuja el mapa en la pantalla."""
    for y in range(cam_y, cam_y + view_height):
        for x in range(cam_x, cam_x + view_width):
            tile = tiles[y][x]

            screen_x = (x - cam_x) * tile_size
            screen_y = (y - cam_y) * tile_size

            if imagenes and tile in imagenes:
                screen.blit(imagenes[tile], (screen_x, screen_y))
            else:
                pygame.draw.rect(
                    screen, colors.get(tile, (255, 0, 0)),
                    (screen_x, screen_y, tile_size, tile_size))
