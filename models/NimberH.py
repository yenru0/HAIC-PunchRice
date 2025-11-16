import random
from typing import List, Set, Tuple  # 타입 힌트 추가

from models.DotsBoxModel import DotsBoxModel


# -----------------------------------------------------------------
# << 2. V7 (최종 하이브리드) 에이전트 클래스 >>
# -----------------------------------------------------------------
# -----------------------------------------------------------------
# << 2. V7e (최종 하이브리드 - 속도 개선) 에이전트 클래스 >>
# -----------------------------------------------------------------


# -----------------------------------------------------------------
# << 2. V7s (최종 하이브리드 - V4.2 + V6) 에이전트 클래스 >>
# -----------------------------------------------------------------

class NimberH(DotsBoxModel):
    
    # --- V8 튜닝 포인트 (V4.2의 값을 그대로 사용) ---
    
    # 1. Phase 1b(후반 수읽기)에서 사용할 Minimax 깊이
    # V4.2와 동일한 '5'를 사용하여 오프닝에서 밀리지 않음
    SEARCH_DEPTH = 5
    
    # 2. Phase 1a(초반) -> Phase 1b(후반)로 전환할 시점
    # V4.2와 동일한 '0.2'를 사용하여 같은 시점에 수읽기 시작
    MINIMAX_TRANSITION_RATIO = 0.2 
    
    
    def __init__(self):
        super().__init__()
        self.xsize: int = None # type: ignore
        self.ysize: int = None # type: ignore
        self.board_lines: list[list[list[int]]] = None # type: ignore
        self.total_moves_possible: int = 0

    # --- [공통] 기본 헬퍼 메서드들 ---
    
    def get_all_empty_moves(self, board_state: List[List[List[int]]]) -> List[List[int]]:
        empty_moves = []
        for x in range(self.xsize):
            for y in range(self.ysize + 1):
                if board_state[x][y][0] == 0: empty_moves.append([x, y, 0])
        for x in range(self.xsize + 1):
            for y in range(self.ysize):
                if board_state[x][y][1] == 0: empty_moves.append([x, y, 1])
        return empty_moves

    def get_adjacent_box_side_counts(self, move: List[int]) -> List[int]:
        x, y, z = move
        counts = []
        if z == 0:
            if y > 0: counts.append(self.board_lines[x][y - 1][0] + self.board_lines[x][y - 1][1] + self.board_lines[x + 1][y - 1][1])
            if y < self.ysize: counts.append(self.board_lines[x][y + 1][0] + self.board_lines[x][y][1] + self.board_lines[x + 1][y][1])
        else:
            if x > 0: counts.append(self.board_lines[x - 1][y][1] + self.board_lines[x - 1][y][0] + self.board_lines[x - 1][y + 1][0])
            if x < self.xsize: counts.append(self.board_lines[x + 1][y][1] + self.board_lines[x][y][0] + self.board_lines[x][y + 1][0])
        return counts

    def count_box_sides(self, board_state: List[List[List[int]]], x: int, y: int) -> int:
        return board_state[x][y][0] + board_state[x][y + 1][0] + board_state[x][y][1] + board_state[x + 1][y][1]

    # --- [Phase 1b] V4.2 Minimax 헬퍼 메서드들 ---

    def _get_move_score(self, move: List[int]) -> int:
        """'수순 정렬(Move Ordering)'을 위한 점수 계산 (현재 보드 기준)."""
        side_counts = self.get_adjacent_box_side_counts(move)
        if 3 in side_counts: return 100
        if 2 in side_counts: return -100
        return 0

    def _get_completed_boxes_count(self, board_state: List[List[List[int]]], move: List[int]) -> int:
        x, y, z = move
        completed = 0
        if z == 0:
            if y > 0 and self.count_box_sides(board_state, x, y - 1) == 3: completed += 1
            if y < self.ysize and self.count_box_sides(board_state, x, y) == 3: completed += 1
        else:
            if x > 0 and self.count_box_sides(board_state, x - 1, y) == 3: completed += 1
            if x < self.xsize and self.count_box_sides(board_state, x, y) == 3: completed += 1
        return completed

    def _evaluate_heuristic(self, board_state: List[List[List[int]]]) -> int:
        score = 0
        for x in range(self.xsize):
            for y in range(self.ysize):
                sides = self.count_box_sides(board_state, x, y)
                if sides == 3: score += 100
                elif sides == 2: score -= 50
        return score

    def _negamax_undo(self, board_state: List[List[List[int]]], depth: int, alpha: float, beta: float) -> float:
        if depth == 0:
            return self._evaluate_heuristic(board_state)

        available_moves = self.get_all_empty_moves(board_state)
        if not available_moves:
            return 0 
        
        max_eval = -float('inf')

        for move in available_moves:
            x, y, z = move
            boxes_completed = self._get_completed_boxes_count(board_state, move)
            board_state[x][y][z] = 1 # 수 두기
            
            eval_score = 0
            if boxes_completed > 0:
                eval_score = boxes_completed + self._negamax_undo(board_state, depth - 1, alpha, beta)
            else:
                eval_score = -self._negamax_undo(board_state, depth - 1, -beta, -alpha)

            board_state[x][y][z] = 0 # 수 되돌리기
            
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, max_eval)
            if alpha >= beta:
                break
        return max_eval

    # --- [Phase 2] V6 Nimber 헬퍼 메서드들 ---

    def _get_box_side_counts_grid(self) -> List[List[int]]:
        grid = [[0 for _ in range(self.ysize)] for _ in range(self.xsize)]
        for x in range(self.xsize):
            for y in range(self.ysize):
                grid[x][y] = self.count_box_sides(self.board_lines, x, y)
        return grid

    def _dfs_find_component(
        self, 
        x: int, 
        y: int, 
        side_counts_grid: List[List[int]], 
        visited: Set[Tuple[int, int]]
    ) -> Set[Tuple[int, int]]:
        if (x, y) in visited or \
           x < 0 or y < 0 or x >= self.xsize or y >= self.ysize or \
           side_counts_grid[x][y] != 2:
            return set()

        visited.add((x, y))
        component_nodes = {(x, y)}
        
        if y > 0 and self.board_lines[x][y][0] == 1:
            component_nodes.update(self._dfs_find_component(x, y - 1, side_counts_grid, visited))
        if y < self.ysize - 1 and self.board_lines[x][y + 1][0] == 1:
            component_nodes.update(self._dfs_find_component(x, y + 1, side_counts_grid, visited))
        if x > 0 and self.board_lines[x][y][1] == 1:
            component_nodes.update(self._dfs_find_component(x - 1, y, side_counts_grid, visited))
        if x < self.xsize - 1 and self.board_lines[x + 1][y][1] == 1:
            component_nodes.update(self._dfs_find_component(x + 1, y, side_counts_grid, visited))
        return component_nodes

    def _calculate_nim_sum(self) -> int:
        side_counts_grid = self._get_box_side_counts_grid()
        visited = set()
        nim_sum = 0
        
        for x in range(self.xsize):
            for y in range(self.ysize):
                if side_counts_grid[x][y] == 2 and (x, y) not in visited:
                    component_nodes = self._dfs_find_component(x, y, side_counts_grid, visited)
                    component_size = len(component_nodes)
                    if component_size == 0: continue

                    is_a_chain = False
                    for (cx, cy) in component_nodes:
                        neighbors = [(cx, cy - 1), (cx, cy + 1), (cx - 1, cy), (cx + 1, cy)]
                        for (nx, ny) in neighbors:
                            if 0 <= nx < self.xsize and 0 <= ny < self.ysize:
                                if side_counts_grid[nx][ny] == 3:
                                    is_a_chain = True
                                    break
                        if is_a_chain: break
                    
                    g_value = component_size if is_a_chain else 1
                    nim_sum ^= g_value
        return nim_sum

    # --- HAIC가 호출하는 메인 실행 함수 ---

    def run(
        self, board_lines: list[list[list[int]]], xsize: int, ysize: int
    ) -> list[int]:
        """
        V8 (최종 하이브리드)
        V4.2의 튜닝 값 (5, 0.2)와 V6의 님버를 결합합니다.
        """
        
        # 1. [매 턴] 클래스 상태 업데이트
        self.board_lines = board_lines
        
        # 2. [최초 1회] 초기화
        if self.xsize is None:
            self.xsize = xsize
            self.ysize = ysize
            self.total_moves_possible = (xsize * (ysize+1)) + (ysize * (xsize+1))

        # 3. [Phase 감지] 모든 수 분류
        all_empty_moves = self.get_all_empty_moves(self.board_lines)
        num_empty_moves = len(all_empty_moves)
        if num_empty_moves == 0: return [0, 0, 0]

        winning_moves, safe_moves, unsafe_moves = [], [], []
        for move in all_empty_moves:
            side_counts = self.get_adjacent_box_side_counts(move)
            is_winning_move = 3 in side_counts
            is_unsafe_move = 2 in side_counts

            if is_winning_move: winning_moves.append(move)
            elif is_unsafe_move: unsafe_moves.append(move)
            else: safe_moves.append(move)

        # 4. [ V8 분기점 ]
        
        # 4-A. [필승] P1(필승) 수가 있으면 즉시 실행 (가장 빠름)
        if winning_moves:
            return random.choice(winning_moves)

        # 4-B. [Phase 1: "Loony Phase"] P2(안전) 수가 1개라도 존재하는가?
        if safe_moves:
            
            # [V8 속도 개선] 지금이 초반/중반인가?
            if num_empty_moves > self.total_moves_possible * self.MINIMAX_TRANSITION_RATIO:
                # [Phase 1a - 초반/중반] (V4.2와 동일한 전략)
                # -> '무작위' 안전한 수를 둔다 (매우 빠름)
                return random.choice(safe_moves)
            
            else:
                # [Phase 1b - 후반] (V4.2와 동일한 전략)
                # -> Minimax(수읽기)로 '최적의' 안전한 수를 찾는다
                best_move = safe_moves[0]
                best_eval = -float('inf')
                alpha = -float('inf')
                beta = float('inf')
                board_copy = [[[v for v in z] for z in y] for y in self.board_lines]
                
                # 수순 정렬
                safe_moves.sort(key=lambda m: self._get_move_score(m), reverse=True)

                for move in safe_moves:
                    x, y, z = move
                    board_copy[x][y][z] = 1 # 수 두기
                    eval_score = -self._negamax_undo(board_copy, self.SEARCH_DEPTH - 1, -beta, -alpha)
                    board_copy[x][y][z] = 0 # 수 되돌리기
                        
                    if eval_score > best_eval:
                        best_eval = eval_score
                        best_move = move
                    alpha = max(alpha, best_eval)

                return best_move
            
        # 4-C. [Phase 2: "Impartial Phase"]
        # P1, P2가 없음. P3(불리한 수)만 남은 엔드게임.
        else: 
            # -> V6의 '수학(님버)' 계산 시작
            winning_nim_moves = []
            for move in unsafe_moves:
                x, y, z = move
                self.board_lines[x][y][z] = 1
                next_nim_sum = self._calculate_nim_sum()
                self.board_lines[x][y][z] = 0
                
                if next_nim_sum == 0:
                    winning_nim_moves.append(move)

            if winning_nim_moves:
                return random.choice(winning_nim_moves)
            else:
                return random.choice(unsafe_moves)