import random

from models.DotsBoxModel import DotsBoxModel


class V4b(DotsBoxModel):
    """V4.2 model (Negamax + greedy phase) ported from `main.py`.

    Early/Mid game: greedy heuristic avoiding giving boxes.
    Late game (<=20% moves left): depth-limited negamax with undo.
    """

    def __init__(self, search_depth: int = 4) -> None:
        self.SEARCH_DEPTH = search_depth

    def init(self) -> None:  # override base
        pass

    # ---------------- Helper methods (from main.py) ----------------
    def _get_all_empty_moves(
        self, board: list[list[list[int]]], xsize: int, ysize: int
    ) -> list[list[int]]:
        empty: list[list[int]] = []
        for x in range(xsize):
            for y in range(ysize + 1):
                if board[x][y][0] == 0:
                    empty.append([x, y, 0])
        for x in range(xsize + 1):
            for y in range(ysize):
                if board[x][y][1] == 0:
                    empty.append([x, y, 1])
        return empty

    def _get_adjacent_box_side_counts(
        self, move: list[int], board: list[list[list[int]]], xsize: int, ysize: int
    ) -> list[int]:
        x, y, z = move
        counts: list[int] = []
        if z == 0:  # horizontal
            if y > 0:
                counts.append(
                    board[x][y - 1][0] + board[x][y - 1][1] + board[x + 1][y - 1][1]
                )
            if y < ysize:
                counts.append(board[x][y + 1][0] + board[x][y][1] + board[x + 1][y][1])
        else:  # vertical
            if x > 0:
                counts.append(
                    board[x - 1][y][1] + board[x - 1][y][0] + board[x - 1][y + 1][0]
                )
            if x < xsize:
                counts.append(board[x + 1][y][1] + board[x][y][0] + board[x][y + 1][0])
        return counts

    def _count_box_sides(self, board: list[list[list[int]]], x: int, y: int) -> int:
        return board[x][y][0] + board[x][y + 1][0] + board[x][y][1] + board[x + 1][y][1]

    def _get_completed_boxes_count(
        self, board: list[list[list[int]]], move: list[int], xsize: int, ysize: int
    ) -> int:
        x, y, z = move
        completed = 0
        if z == 0:
            if y > 0 and self._count_box_sides(board, x, y - 1) == 3:
                completed += 1
            if y < ysize and self._count_box_sides(board, x, y) == 3:
                completed += 1
        else:
            if x > 0 and self._count_box_sides(board, x - 1, y) == 3:
                completed += 1
            if x < xsize and self._count_box_sides(board, x, y) == 3:
                completed += 1
        return completed

    def _evaluate_heuristic(
        self, board: list[list[list[int]]], xsize: int, ysize: int
    ) -> int:
        score = 0
        for x in range(xsize):
            for y in range(ysize):
                sides = self._count_box_sides(board, x, y)
                if sides == 3:
                    score += 100
                elif sides == 2:
                    score -= 50
        return score

    def _get_move_score(
        self, move: list[int], board: list[list[list[int]]], xsize: int, ysize: int
    ) -> int:
        counts = self._get_adjacent_box_side_counts(move, board, xsize, ysize)
        if 3 in counts:
            return 100
        if 2 in counts:
            return -100
        return 0

    def _negamax_undo(
        self,
        board: list[list[list[int]]],
        depth: int,
        alpha: float,
        beta: float,
        xsize: int,
        ysize: int,
    ) -> float:
        if depth == 0:
            return self._evaluate_heuristic(board, xsize, ysize)
        moves = self._get_all_empty_moves(board, xsize, ysize)
        if not moves:
            return 0
        moves.sort(
            key=lambda m: self._get_move_score(m, board, xsize, ysize), reverse=True
        )
        best = -float("inf")
        for mv in moves:
            x, y, z = mv
            completed = self._get_completed_boxes_count(board, mv, xsize, ysize)
            board[x][y][z] = 1
            if completed > 0:
                val = completed + self._negamax_undo(
                    board, depth - 1, alpha, beta, xsize, ysize
                )
            else:
                val = -self._negamax_undo(board, depth - 1, -beta, -alpha, xsize, ysize)
            board[x][y][z] = 0
            if val > best:
                best = val
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return best

    # ------------------------ Public API --------------------------
    def run(
        self, board_lines: list[list[list[int]]], xsize: int, ysize: int
    ) -> list[int]:
        moves = self._get_all_empty_moves(board_lines, xsize, ysize)
        if not moves:
            return [0, 0, 0]
        total_possible = (xsize * (ysize + 1)) + (ysize * (xsize + 1))
        # Greedy phase (>20% moves left)
        if len(moves) > total_possible * 0.2:
            winning: list[list[int]] = []
            safe: list[list[int]] = []
            unsafe: list[list[int]] = []
            for mv in moves:
                counts = self._get_adjacent_box_side_counts(
                    mv, board_lines, xsize, ysize
                )
                if 3 in counts:
                    winning.append(mv)
                elif 2 in counts:
                    unsafe.append(mv)
                else:
                    safe.append(mv)
            if winning:
                x, y, z = random.choice(winning)
                return [x, y, z]
            if safe:
                x, y, z = random.choice(safe)
                return [x, y, z]
            if unsafe:
                x, y, z = random.choice(unsafe)
                return [x, y, z]
            x, y, z = random.choice(moves)
            return [x, y, z]
        # Late game: Negamax search
        board_copy = [[[v for v in z] for z in y] for y in board_lines]
        moves.sort(
            key=lambda m: self._get_move_score(m, board_lines, xsize, ysize),
            reverse=True,
        )
        best_move = moves[0]
        best_eval = -float("inf")
        alpha = -float("inf")
        beta = float("inf")
        for mv in moves:
            x, y, z = mv
            completed = self._get_completed_boxes_count(board_copy, mv, xsize, ysize)
            board_copy[x][y][z] = 1
            if completed > 0:
                val = completed + self._negamax_undo(
                    board_copy, self.SEARCH_DEPTH - 1, alpha, beta, xsize, ysize
                )
            else:
                val = -self._negamax_undo(
                    board_copy, self.SEARCH_DEPTH - 1, -beta, -alpha, xsize, ysize
                )
            board_copy[x][y][z] = 0
            if val > best_eval:
                best_eval = val
                best_move = mv
            alpha = max(alpha, best_eval)
        return best_move
