import random
import copy

model = None


def init():
    pass


# -----------------------------------------------------------------
# << 헬퍼 함수 섹션 >>
# -----------------------------------------------------------------


def get_all_empty_moves(board_lines, xsize, ysize):
    """
    (V1/V2 공통)
    현재 보드에서 그을 수 있는 모든 '빈' 선의 목록을 반환합니다.
    """
    empty_moves = []

    # 1. 가로선 (z = 0) 탐색
    # x는 0부터 xsize-1까지, y는 0부터 ysize까지
    for x in range(xsize):
        for y in range(ysize + 1):
            if board_lines[x][y][0] == 0:
                empty_moves.append([x, y, 0])

    # 2. 세로선 (z = 1) 탐색
    # x는 0부터 xsize까지, y는 0부터 ysize-1까지
    for x in range(xsize + 1):
        for y in range(ysize):
            if board_lines[x][y][1] == 0:
                empty_moves.append([x, y, 1])

    return empty_moves


# --- (V1 '탐욕법' 전략을 위한 헬퍼) ---


def get_adjacent_box_side_counts(move, board_lines, xsize, ysize):
    """
    (V1의 헬퍼 함수 - 초반 전략에 사용됨)
    특정 'move'를 그었을 때, 인접한 1개 또는 2개의 상자가
    'move'를 제외하고 각각 몇 개의 변을 가지고 있는지 계산합니다.

    반환값: [box1_sides, box2_sides] (예: [2, 1] 또는 [3])
    """
    x, y, z = move
    counts = []

    if z == 0:  # 가로선 (Horizontal)
        if y > 0:  # 위쪽 상자
            sides = (
                board_lines[x][y - 1][0]
                + board_lines[x][y - 1][1]
                + board_lines[x + 1][y - 1][1]
            )
            counts.append(sides)
        if y < ysize:  # 아래쪽 상자
            sides = (
                board_lines[x][y + 1][0]
                + board_lines[x][y][1]
                + board_lines[x + 1][y][1]
            )
            counts.append(sides)
    else:  # 세로선 (Vertical, z = 1)
        if x > 0:  # 왼쪽 상자
            sides = (
                board_lines[x - 1][y][1]
                + board_lines[x - 1][y][0]
                + board_lines[x - 1][y + 1][0]
            )
            counts.append(sides)
        if x < xsize:  # 오른쪽 상자
            sides = (
                board_lines[x + 1][y][1]
                + board_lines[x][y][0]
                + board_lines[x][y + 1][0]
            )
            counts.append(sides)

    return counts


# --- (V2 'Negamax' 전략을 위한 헬퍼) ---


def count_box_sides(board, x, y):
    """
    (V2의 헬퍼 함수 - Negamax에 사용됨)
    (x, y) 위치의 상자(Box)가 몇 개의 변을 가졌는지 반환합니다.
    """
    # (x, y)는 상자의 좌상단 좌표
    top = board[x][y][0]
    bottom = board[x][y + 1][0]
    left = board[x][y][1]
    right = board[x + 1][y][1]
    return top + bottom + left + right


def get_completed_boxes_count(board, move, xsize, ysize):
    """
    (V2의 헬퍼 함수 - Negamax에 사용됨)
    'move'를 두었을 때 완성되는 상자(3면 -> 4면)의 개수를 반환합니다. (0, 1, 또는 2)
    이 함수는 'move'를 두기 *전*의 board를 기준으로 계산합니다.
    """
    x, y, z = move
    completed = 0

    if z == 0:  # 가로선
        if y > 0 and count_box_sides(board, x, y - 1) == 3:  # 위쪽 상자
            completed += 1
        if y < ysize and count_box_sides(board, x, y) == 3:  # 아래쪽 상자
            completed += 1
    else:  # 세로선
        if x > 0 and count_box_sides(board, x - 1, y) == 3:  # 왼쪽 상자
            completed += 1
        if x < xsize and count_box_sides(board, x, y) == 3:  # 오른쪽 상자
            completed += 1

    return completed


def evaluate_heuristic(board, xsize, ysize):
    """
    (V2의 헬퍼 함수 - Negamax의 '깊이 한계' 도달 시 사용)
    현재 보드 상태를 '지금 턴인 플레이어' 입장에서 평가합니다.

    전략:
    1. (승리) 3면인 상자(즉시 획득 가능)는 매우 높은 점수를 줍니다.
    2. (패배) 2면인 상자(상대에게 기회를 줌)는 매우 높은 감점을 줍니다.
    """
    score = 0
    for x in range(xsize):
        for y in range(ysize):
            sides = count_box_sides(board, x, y)

            if sides == 3:
                score += 100  # P1: 즉시 1점 + 1턴 (매우 높게 평가)
            elif sides == 2:
                score -= 50  # P3: 상대에게 3면을 만들어줌 (매우 낮게 평가)
            # 0, 1면인 상자(P2: 안전한 수)는 0점 (중립)

    return score


def negamax(board, depth, alpha, beta, xsize, ysize):
    """
    (V2의 헬퍼 함수 - Negamax 핵심 알고리즘)
    Alpha-Beta Pruning을 포함하여 현재 턴 플레이어 기준 최적의 점수를 반환합니다.
    """

    # 1. 깊이 한계(Depth Limit) 도달 시, 휴리스틱 평가 함수로 현재 상태를 평가
    if depth == 0:
        return evaluate_heuristic(board, xsize, ysize)

    available_moves = get_all_empty_moves(board, xsize, ysize)

    # 2. 게임 종료 (더 둘 곳이 없음)
    if not available_moves:
        return 0  # 무승부 또는 종료 상태

    max_eval = -float("inf")  # 현재까지의 최고 점수 (최악에서 시작)

    for move in available_moves:

        # 3. 이 수를 둠으로써 상자가 완성되는지 확인 (점수 획득 및 턴 유지)
        boxes_completed = get_completed_boxes_count(board, move, xsize, ysize)

        # 4. 가상으로 수 두기 (보드 상태 복사)
        # (3D 리스트는 리스트 컴프리헨션으로 deepcopy)
        next_board = [[[v for v in z] for z in y] for y in board]
        next_board[move[0]][move[1]][move[2]] = 1

        eval_score = 0

        if boxes_completed > 0:
            # 5-A. 턴 유지:
            # 'boxes_completed' 만큼 점수를 얻고, '같은' 플레이어가 한 번 더 둡니다.
            eval_score = boxes_completed + negamax(
                next_board, depth - 1, alpha, beta, xsize, ysize
            )
        else:
            # 5-B. 턴 넘김:
            # '상대방' 차례로 재귀호출하고, 결과에 -1을 곱하여 '나의' 점수로 변환합니다.
            eval_score = -negamax(next_board, depth - 1, -beta, -alpha, xsize, ysize)

        max_eval = max(max_eval, eval_score)  # 최고 점수 갱신

        # 6. Alpha-Beta Pruning
        alpha = max(alpha, max_eval)
        if alpha >= beta:
            break  # 이 경로는 더 탐색할 필요가 없음

    return max_eval


# -----------------------------------------------------------------
# << 메인 실행 함수 (V3 - 버그 수정됨) >>
# -----------------------------------------------------------------


def run(board_lines, xsize, ysize):
    """
    에이전트의 차례가 될 때마다 실행되는 함수입니다.
    초반에는 '탐욕법', 중후반에는 'Negamax'를 사용합니다.
    """

    # --- 튜닝 포인트 1: 수읽기 깊이 (Depth) ---
    # HAIC의 제한 시간 내에서 가능한 가장 큰 값으로 설정하세요. (예: 4~7)
    SEARCH_DEPTH = 3

    all_empty_moves = get_all_empty_moves(board_lines, xsize, ysize)

    if not all_empty_moves:
        return [0, 0, 0]  # 게임 종료

    # --- 튜닝 포인트 2: 초반/중반 전환 시점 ---
    # 남은 수가 전체의 60% 이상이면 V1 '탐욕법' 사용 (탐색 시간 절약)
    total_moves_possible = (xsize * (ysize + 1)) + (ysize * (xsize + 1))

    if len(all_empty_moves) > total_moves_possible * 0.6:

        winning_moves = []  # [P1] 내가 점수를 얻는 수
        safe_moves = []  # [P2] 상대에게 점수를 주지 않는 수
        unsafe_moves = []  # [P3] 어쩔 수 없이 상대에게 점수를 주는 수

        for move in all_empty_moves:
            # V1의 헬퍼 함수를 사용하여 '안전성' 검사
            side_counts = get_adjacent_box_side_counts(move, board_lines, xsize, ysize)

            is_winning_move = 3 in side_counts
            is_unsafe_move = 2 in side_counts  # 2면을 만들어주면 '불리한 수'

            if is_winning_move:
                winning_moves.append(move)
            elif is_unsafe_move:
                unsafe_moves.append(move)
            else:
                safe_moves.append(move)

        # V1의 3단계 우선순위 적용
        if winning_moves:
            return random.choice(winning_moves)
        if safe_moves:
            return random.choice(safe_moves)
        if unsafe_moves:
            return random.choice(unsafe_moves)

        # (예외 처리)
        return random.choice(all_empty_moves)

    # --- 게임 중후반: Negamax 탐색 시작 ---
    best_move = all_empty_moves[0]
    best_eval = -float("inf")

    # Negamax의 Alpha-Beta Pruning을 위해 초깃값 설정
    alpha = -float("inf")
    beta = float("inf")

    # (성능 향상 팁: alpha-beta pruning 효율을 높이려면
    #  all_empty_moves를 winning_moves -> safe_moves -> unsafe_moves 순으로 정렬하는 것이 좋습니다.)
    #  여기서는 단순화를 위해 순차 탐색합니다.
    random.shuffle(
        all_empty_moves
    )  # 순서를 섞어주면 평균적으로 가지치기 성능이 향상될 수 있습니다.

    for move in all_empty_moves:

        boxes_completed = get_completed_boxes_count(board_lines, move, xsize, ysize)

        # 3D 리스트 복사
        next_board = [[[v for v in z] for z in y] for y in board_lines]
        next_board[move[0]][move[1]][move[2]] = 1

        eval_score = 0

        if boxes_completed > 0:
            # 턴 유지 (미래 점수 + 현재 점수)
            eval_score = boxes_completed + negamax(
                next_board, SEARCH_DEPTH, alpha, beta, xsize, ysize
            )
        else:
            # 턴 넘김 (미래 점수의 반대)
            eval_score = -negamax(next_board, SEARCH_DEPTH, -beta, -alpha, xsize, ysize)

        # 가장 높은 평가 점수를 받은 'move'를 저장
        if eval_score > best_eval:
            best_eval = eval_score
            best_move = move

        # (Alpha-Beta Pruning의 Alpha 값 갱신)
        alpha = max(alpha, best_eval)

    return best_move
