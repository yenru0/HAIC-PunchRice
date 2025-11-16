import random
import copy
from typing import List, Set, Tuple  # 타입 힌트 추가

from models.DotsBoxModel import DotsBoxModel

# --- 2. V5 (님버 하이브리드) 에이전트 클래스 ---


class Nimber(DotsBoxModel):

    def __init__(self):
        super().__init__()
        self.xsize: int = None  # type: ignore
        self.ysize: int = None  # type: ignore
        self.board_lines: list[list[list[int]]] = None  # type: ignore

    # --- [Phase 1] V1/V4의 헬퍼 메서드들 ---

    def get_all_empty_moves(self) -> List[List[int]]:
        """현재 그을 수 있는 모든 '빈' 선의 목록을 반환합니다."""
        empty_moves = []
        for x in range(self.xsize):
            for y in range(self.ysize + 1):
                if self.board_lines[x][y][0] == 0:
                    empty_moves.append([x, y, 0])
        for x in range(self.xsize + 1):
            for y in range(self.ysize):
                if self.board_lines[x][y][1] == 0:
                    empty_moves.append([x, y, 1])
        return empty_moves

    def get_adjacent_box_side_counts(self, move: List[int]) -> List[int]:
        """'move'를 그었을 때 인접한 상자(들)의 3면 상태를 반환."""
        x, y, z = move
        counts = []
        if z == 0:  # 가로선
            if y > 0:
                counts.append(
                    self.board_lines[x][y - 1][0]
                    + self.board_lines[x][y - 1][1]
                    + self.board_lines[x + 1][y - 1][1]
                )
            if y < self.ysize:
                counts.append(
                    self.board_lines[x][y + 1][0]
                    + self.board_lines[x][y][1]
                    + self.board_lines[x + 1][y][1]
                )
        else:  # 세로선
            if x > 0:
                counts.append(
                    self.board_lines[x - 1][y][1]
                    + self.board_lines[x - 1][y][0]
                    + self.board_lines[x - 1][y + 1][0]
                )
            if x < self.xsize:
                counts.append(
                    self.board_lines[x + 1][y][1]
                    + self.board_lines[x][y][0]
                    + self.board_lines[x][y + 1][0]
                )
        return counts

    def count_box_sides(self, x: int, y: int) -> int:
        """(x, y) 상자의 채워진 변 개수를 셉니다."""
        return (
            self.board_lines[x][y][0]
            + self.board_lines[x][y + 1][0]
            + self.board_lines[x][y][1]
            + self.board_lines[x + 1][y][1]
        )

    # --- [Phase 2] V6 님버 헬퍼 메서드들 (버그 수정됨) ---

    def _get_box_side_counts_grid(self) -> List[List[int]]:
        """모든 상자(box)의 현재 변(side) 개수를 2D 배열로 만들어 반환."""
        grid = [[0 for _ in range(self.ysize)] for _ in range(self.xsize)]
        for x in range(self.xsize):
            for y in range(self.ysize):
                grid[x][y] = self.count_box_sides(x, y)
        return grid

    def _dfs_find_component(
        self,
        x: int,
        y: int,
        side_counts_grid: List[List[int]],
        visited: Set[Tuple[int, int]],
    ) -> Set[Tuple[int, int]]:
        """
        [V6 수정] DFS로 '2면' 상자 컴포넌트에 속한 모든 노드(상자)의
        좌표 집합(Set)을 반환합니다.
        """
        # (x, y)가 방문했거나, 보드 밖이거나, 2면이 아니면 탐색 중지
        if (
            (x, y) in visited
            or x < 0
            or y < 0
            or x >= self.xsize
            or y >= self.ysize
            or side_counts_grid[x][y] != 2
        ):
            return set()

        visited.add((x, y))
        component_nodes = {(x, y)}

        # 닫힌 '선'을 통해서만 2면체 이웃으로 이동
        # 위쪽 (x, y-1)
        if y > 0 and self.board_lines[x][y][0] == 1:  # 위쪽 선(Top)이 닫혀있음
            component_nodes.update(
                self._dfs_find_component(x, y - 1, side_counts_grid, visited)
            )

        # 아래쪽 (x, y+1)
        if (
            y < self.ysize - 1 and self.board_lines[x][y + 1][0] == 1
        ):  # 아래쪽 선(Bottom)이 닫혀있음
            component_nodes.update(
                self._dfs_find_component(x, y + 1, side_counts_grid, visited)
            )

        # 왼쪽 (x-1, y)
        if x > 0 and self.board_lines[x][y][1] == 1:  # 왼쪽 선(Left)이 닫혀있음
            component_nodes.update(
                self._dfs_find_component(x - 1, y, side_counts_grid, visited)
            )

        # 오른쪽 (x+1, y)
        if (
            x < self.xsize - 1 and self.board_lines[x + 1][y][1] == 1
        ):  # 오른쪽 선(Right)이 닫혀있음
            component_nodes.update(
                self._dfs_find_component(x + 1, y, side_counts_grid, visited)
            )

        return component_nodes

    def _calculate_nim_sum(self) -> int:
        """
        [V6 재설계]
        현재 'self.board_lines' 상태에서 '루프'와 '체인'을
        정확히 구별하여 '님 합(Nim-Sum)'을 계산합니다.
        """
        side_counts_grid = self._get_box_side_counts_grid()
        visited = set()
        nim_sum = 0

        for x in range(self.xsize):
            for y in range(self.ysize):
                # '2면'을 가졌고, 아직 방문하지 않은 컴포넌트의 시작점 발견
                if side_counts_grid[x][y] == 2 and (x, y) not in visited:

                    # 1. 이 컴포넌트에 속한 모든 상자(노드)를 찾음
                    component_nodes = self._dfs_find_component(
                        x, y, side_counts_grid, visited
                    )
                    component_size = len(component_nodes)

                    if component_size == 0:
                        continue

                    # 2. [핵심] 이 컴포넌트가 '체인'인지 '루프'인지 판별
                    #    컴포넌트의 노드 중 하나라도 '3면' 상자와 인접하면 '체인'
                    is_a_chain = False
                    for cx, cy in component_nodes:
                        # (cx, cy) 상자의 4방향 이웃 상자 확인
                        neighbors = [
                            (cx, cy - 1),
                            (cx, cy + 1),
                            (cx - 1, cy),
                            (cx + 1, cy),
                        ]
                        for nx, ny in neighbors:
                            # 이웃이 보드 범위 내에 있고
                            if 0 <= nx < self.xsize and 0 <= ny < self.ysize:
                                # 이웃이 '3면' 상자라면
                                if side_counts_grid[nx][ny] == 3:
                                    is_a_chain = True
                                    break
                        if is_a_chain:
                            break

                    # 3. 올바른 님버(g-value) 할당
                    g_value = 0
                    if is_a_chain:
                        g_value = component_size  # 체인(길이 N) -> 님버 N
                    else:
                        g_value = 1  # 루프(길이 N) -> 님버 1

                    # 4. XOR 연산
                    nim_sum ^= g_value

        return nim_sum

    # --- HAIC가 호출하는 메인 실행 함수 ---

    def run(
        self, board_lines: list[list[list[int]]], xsize: int, ysize: int
    ) -> list[int]:
        """
        V6 (하이브리드) 에이전트.
        'Phase'를 감지하고, V1(탐욕법) 또는 V6(님버) 전략을 선택합니다.
        """

        # 1. [매 턴] 클래스 상태 업데이트
        self.board_lines = board_lines

        # 2. [최초 1회] 초기화
        if self.xsize is None:
            self.xsize = xsize
            self.ysize = ysize

        # 3. [Phase 1 감지] V1 탐욕법 로직으로 모든 수 분류
        all_empty_moves = self.get_all_empty_moves()

        if not all_empty_moves:
            return [0, 0, 0]  # 게임 종료

        winning_moves = []  # [P1] 내가 점수를 얻는 수
        safe_moves = []  # [P2] 상대에게 점수를 주지 않는 수
        unsafe_moves = []  # [P3] 어쩔 수 없이 상대에게 점수를 주는 수

        for move in all_empty_moves:
            side_counts = self.get_adjacent_box_side_counts(move)
            is_winning_move = 3 in side_counts
            is_unsafe_move = 2 in side_counts

            if is_winning_move:
                winning_moves.append(move)
            elif is_unsafe_move:
                unsafe_moves.append(move)
            else:
                safe_moves.append(move)

        # 4. [ V6 분기점 ]

        # 4-1. [Phase 1: "Loony Phase"]
        # P1(필승) 또는 P2(안전) 수가 1개라도 존재하는가?
        if winning_moves or safe_moves:
            # -> 예: 탐욕법으로 대응
            if winning_moves:
                return random.choice(winning_moves)
            else:  # safe_moves
                return random.choice(safe_moves)

        # 4-2. [Phase 2: "Impartial Phase"]
        # -> 아니오: 모든 수가 P3(불리한 수)뿐입니다.
        # -> V6의 '수학(님버)' 계산 시작

        winning_nim_moves = []  # '님 합'을 0으로 만드는 필승의 수

        for move in unsafe_moves:

            # 가상으로 수 두기 (self.board_lines를 직접 수정)
            x, y, z = move
            self.board_lines[x][y][z] = 1

            # 수를 둔 *다음* 상태의 [V6] '님 합' 계산
            next_nim_sum = self._calculate_nim_sum()

            # 님 합이 0이 되는 수를 찾았는가?
            if next_nim_sum == 0:
                winning_nim_moves.append(move)

            # 가상으로 둔 수 되돌리기
            self.board_lines[x][y][z] = 0

        # 4-3. 결과 반환
        if winning_nim_moves:
            # "필승의 수"가 1개 이상 존재. 그 중 하나를 둔다.
            return random.choice(winning_nim_moves)
        else:
            # "필승의 수"가 없음. (현재 상태가 P-Position, 즉 '패배' 상태)
            # 어차피 지게 되므로, 아무 수나 둔다.
            # (개선: 이 중 '가장 적은' 체인을 넘겨주는 수를 둬야 함)
            return random.choice(unsafe_moves)
