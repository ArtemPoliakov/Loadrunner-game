from enum import Enum, auto

# REFACTORED (Напрямок та верт/гор в константи або інакше)

class MoveAxis(Enum):
    HORIZONTAL = auto()
    VERTICAL = auto()

class Direction(Enum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3
    UP_LEFT = 4
    UP_RIGHT = 5

# REFACTORED (dict для напрямку → dx, dy)

DIR_OFFSETS = {
    Direction.UP:       (-1,  0),
    Direction.RIGHT:    ( 0,  1),
    Direction.DOWN:     ( 1,  0),
    Direction.LEFT:     ( 0, -1),
    Direction.UP_LEFT:  (-1, -1),
    Direction.UP_RIGHT: (-1,  1),
}