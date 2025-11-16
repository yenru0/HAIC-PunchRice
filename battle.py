import importlib
from dataclasses import dataclass
import time

from models.DotsBoxModel import DotsBoxModel


@dataclass
class BattleResult:
    winner: int
    actions: list[tuple[int, tuple[int, int, int]]]
    time_taken: list[tuple[int, float]]
    flag: int = 0


class Battle:
    def __init__(self, player1: DotsBoxModel, player2: DotsBoxModel):
        self.turn = 0

        self.players = [player1, player2]

        self.xsize = 5
        self.ysize = 5

        self.score = [0, 0]

        self.board = [
            [[0 for _ in [0, 1]] for _ in range((self.ysize))]
            for _ in range(self.xsize)
        ]
        self.BATCH_SIZE = 80

    def start(self):
        print(
            f"Battle started: {self.players[0].__class__.__name__} vs {self.players[1].__class__.__name__}!"
        )

        self.turn = 0
        self.board = [
            [[0 for _ in [0, 1]] for _ in range((self.ysize + 1))]
            for _ in range(self.xsize + 1)
        ]

        self.score = [0, 0]

        while self.is_over() is False:
            current_player = self.players[self.turn]
            print(f"Player {self.turn}'s turn ({current_player.__class__.__name__})")

            move = current_player.run(self.board, self.xsize, self.ysize)

            completed_boxes = self.try_move(move)

            if completed_boxes == -1:
                print(
                    f"Invalid move by Player {self.turn}: {move}. They forfeit the game."
                )
                winner = 1 - self.turn
                print(f"Player {winner} wins!")
                return

            self.score[self.turn] += completed_boxes

            print(
                f"Player {self.turn} played move: {move}, completed boxes: {completed_boxes}"
            )
            print(
                f"Current score: Player 0: {self.score[0]}, Player 1: {self.score[1]}"
            )

            if completed_boxes == 0:
                self.turn = 1 - self.turn

    def battle(self, initial_turn: int) -> BattleResult:
        # clear state
        self.turn = initial_turn
        self.board = [
            [[0 for _ in [0, 1]] for _ in range((self.ysize + 1))]
            for _ in range(self.xsize + 1)
        ]

        self.score = [0, 0]

        # record time taken and moves turn

        time_taken = []
        actions = []

        # battle loop
        while self.is_over() is False:
            current_player = self.players[self.turn]

            delta_t = time.time()
            move = current_player.run(self.board, self.xsize, self.ysize)
            delta_t = time.time() - delta_t
            completed_boxes = self.try_move(move)

            if completed_boxes == -1:
                winner = 1 - self.turn
                return BattleResult(
                    winner=winner, actions=actions, time_taken=time_taken, flag=1
                )

            self.score[self.turn] += completed_boxes

            actions.append((self.turn, move))
            time_taken.append((self.turn, delta_t))

            if completed_boxes == 0:
                self.turn = 1 - self.turn

        if self.score[0] > self.score[1]:
            return BattleResult(winner=0, actions=actions, time_taken=time_taken)
        elif self.score[1] > self.score[0]:
            return BattleResult(winner=1, actions=actions, time_taken=time_taken)
        else:
            return BattleResult(winner=-1, actions=actions, time_taken=time_taken)

    def batch(self) -> list[list[BattleResult]]:

        battle_results = [
            [self.battle(_initial_turn) for _ in range(self.BATCH_SIZE)]
            for _initial_turn in [0, 1]
        ]

        return battle_results

    def is_over(self) -> bool:
        total_boxes = self.xsize * self.ysize
        return self.score[0] + self.score[1] >= total_boxes

    def is_move_valid(self, move: list[int]):
        x, y, z = move
        if 0 <= x <= self.xsize and 0 <= y <= self.ysize and z in [0, 1]:
            if x == self.xsize and z == 0:
                return False
            if y == self.ysize and z == 1:
                return False
            if self.board[x][y][z] != 0:
                return False
            return True
        else:
            return False

    def _count_box_sides(self, x: int, y: int) -> int:
        return (
            self.board[x][y][0]
            + self.board[x][y + 1][0]
            + self.board[x][y][1]
            + self.board[x + 1][y][1]
        )

    def _completed_boxes_count(self, move: list[int]) -> int:
        x, y, z = move
        completed = 0
        if z == 0:
            if y > 0 and self._count_box_sides(x, y - 1) == 3:
                completed += 1
            if y < self.ysize and self._count_box_sides(x, y) == 3:
                completed += 1
        else:
            if x > 0 and self._count_box_sides(x - 1, y) == 3:
                completed += 1
            if x < self.xsize and self._count_box_sides(x, y) == 3:
                completed += 1
        return completed

    def try_move(
        self, move: list[int]
    ) -> int:  # returns -1 if invalid, else completed boxes
        if not self.is_move_valid(move):
            return -1

        x, y, z = move

        completed_boxes = self._completed_boxes_count(move)

        self.board[x][y][z] = 1

        return completed_boxes
