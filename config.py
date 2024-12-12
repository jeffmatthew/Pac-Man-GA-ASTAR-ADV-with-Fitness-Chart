# Constants
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 900
PLAYER_SPEED = 4.5
GHOST_SPEED = 3.5
PLAYER_LAYER = 4
ENEMY_LAYER = 4
BLOCK_LAYER = 5
GROUND_LAYER = 1
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
DARK_RED = (153, 0, 0)
GRAY = (128, 128, 128)

#Tilemap
TILESIZE = 32  # Tile size for the map


class TilemapManager:
    tilemap = [ # 21x21
    "WWWWWWWWWWWWWWWWWWWWW",
    "W........WWW........W",
    "W.WWWWWW.WWW.WWWWWW.W",
    "W...................W",
    "W.WW.W.WWWWWWW.W.WW.W",
    "W....W....W....W....W",
    "WWWW.WWWW.W.WWWW.WWWW",
    "WWWW.W         W.WWWW",
    "WWWW.W WWW WWW W.WWWW",
    "WTP... WIR LCW ... TW",
    "WWWW.W WWWWWWW W.WWWW",
    "WWWW.W         W.WWWW",
    "WWWW.W.WWWWWWW.W.WWWW",
    "W.........W.........W",
    "W.WW.WWWW.W.WWWW.WW.W",
    "W..W.............W..W",
    "WW.W.W.WWWWWWW.W.W.WW",
    "W....W....W....W....W",
    "W.WWWWWWW.W.WWWWWWW.W",
    "W...................W",
    "WWWWWWWWWWWWWWWWWWWWW",
]

# Immutable original tilemap
original_tilemap = [
    "WWWWWWWWWWWWWWWWWWWWW",
    "W........WWW........W",
    "W.WWWWWW.WWW.WWWWWW.W",
    "W...................W",
    "W.WW.W.WWWWWWW.W.WW.W",
    "W....W....W....W....W",
    "WWWW.WWWW.W.WWWW.WWWW",
    "WWWW.W         W.WWWW",
    "WWWW.W WWW WWW W.WWWW",
    "WTP... WIR LCW ... TW",
    "WWWW.W WWWWWWW W.WWWW",
    "WWWW.W         W.WWWW",
    "WWWW.W.WWWWWWW.W.WWWW",
    "W.........W.........W",
    "W.WW.WWWW.W.WWWW.WW.W",
    "W..W.............W..W",
    "WW.W.W.WWWWWWW.W.W.WW",
    "W....W....W....W....W",
    "W.WWWWWWW.W.WWWWWWW.W",
    "W...................W",
    "WWWWWWWWWWWWWWWWWWWWW",
]

# Mutable tilemap (used in gameplay)
tilemap = [list(row) for row in original_tilemap]
