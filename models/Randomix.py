import random

from models.DotsBoxModel import DotsBoxModel

class Randomix(DotsBoxModel):
    """Random move model."""

    def run(
        self, board_lines: list[list[list[int]]], xsize: int, ysize: int
    ) -> list[int]:
        empty_moves: list[list[int]] = []
        for x in range(xsize):
            for y in range(ysize + 1):
                if board_lines[x][y][0] == 0:
                    empty_moves.append([x, y, 0])
        for x in range(xsize + 1):
            for y in range(ysize):
                if board_lines[x][y][1] == 0:
                    empty_moves.append([x, y, 1])
        return random.choice(empty_moves)