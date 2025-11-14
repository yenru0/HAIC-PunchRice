import random
import copy

model = None

def init():
    pass

# -----------------------------------------------------------------
# << 헬퍼 함수 섹션 >>
# (V4.1과 동일)
# -----------------------------------------------------------------

def get_all_empty_moves(board_lines, xsize, ysize):
    """(V1/V2 공통) 빈 선의 목록을 반환합니다."""
    empty_moves = []
    for x in range(xsize):
        for y in range(ysize + 1):
            if board_lines[x][y][0] == 0: empty_moves.append([x, y, 0])
    for x in range(xsize + 1):
        for y in range(ysize):
            if board_lines[x][y][1] == 0: empty_moves.append([x, y, 1])
    return empty_moves

def get_adjacent_box_side_counts(move, board_lines, xsize, ysize):
    """(V1 헬퍼) '탐욕법' (초반 전략)에 사용됩니다."""
    x, y, z = move
    counts = []
    if z == 0:  # 가로선
        if y > 0: counts.append(board_lines[x][y - 1][0] + board_lines[x][y - 1][1] + board_lines[x + 1][y - 1][1])
        if y < ysize: counts.append(board_lines[x][y + 1][0] + board_lines[x][y][1] + board_lines[x + 1][y][1])
    else:  # 세로선
        if x > 0: counts.append(board_lines[x - 1][y][1] + board_lines[x - 1][y][0] + board_lines[x - 1][y + 1][0])
        if x < xsize: counts.append(board_lines[x + 1][y][1] + board_lines[x][y][0] + board_lines[x][y + 1][0])
    return counts

def count_box_sides(board, x, y):
    """(V2 헬퍼) (x, y) 상자의 변 개수를 셉니다."""
    return board[x][y][0] + board[x][y + 1][0] + board[x][y][1] + board[x + 1][y][1]

def get_completed_boxes_count(board, move, xsize, ysize):
    """(V2 헬퍼) 'move'를 두기 *전*을 기준으로, 해당 move로 완성되는 상자 개수를 셉니다."""
    x, y, z = move
    completed = 0
    if z == 0:  # 가로선
        if y > 0 and count_box_sides(board, x, y - 1) == 3: completed += 1
        if y < ysize and count_box_sides(board, x, y) == 3: completed += 1
    else:  # 세로선
        if x > 0 and count_box_sides(board, x - 1, y) == 3: completed += 1
        if x < xsize and count_box_sides(board, x, y) == 3: completed += 1
    return completed

def evaluate_heuristic(board, xsize, ysize):
    """(V2 헬퍼) 휴리스틱 평가 함수."""
    score = 0
    for x in range(xsize):
        for y in range(ysize):
            sides = count_box_sides(board, x, y)
            if sides == 3: score += 100
            elif sides == 2: score -= 50
    return score

def get_move_score(move, board, xsize, ysize):
    """(V4 헬퍼) '수순 정렬(Move Ordering)'을 위한 점수 계산."""
    side_counts = get_adjacent_box_side_counts(move, board, xsize, ysize)
    is_winning_move = 3 in side_counts
    is_unsafe_move = 2 in side_counts
    
    if is_winning_move: return 100
    if is_unsafe_move: return -100
    return 0

def negamax_undo(board, depth, alpha, beta, xsize, ysize):
    """(V4 헬퍼) 최적화된 Negamax (보드 복사 X, '수 되돌리기' O)"""
    
    if depth == 0:
        return evaluate_heuristic(board, xsize, ysize)

    available_moves = get_all_empty_moves(board, xsize, ysize)
    
    if not available_moves:
        return 0 

    available_moves.sort(key=lambda m: get_move_score(m, board, xsize, ysize), reverse=True)
    
    max_eval = -float('inf')

    for move in available_moves:
        x, y, z = move
        boxes_completed = get_completed_boxes_count(board, move, xsize, ysize)
        board[x][y][z] = 1 # 수 두기
        
        eval_score = 0
        
        if boxes_completed > 0:
            eval_score = boxes_completed + negamax_undo(board, depth - 1, alpha, beta, xsize, ysize)
        else:
            eval_score = -negamax_undo(board, depth - 1, -beta, -alpha, xsize, ysize)

        board[x][y][z] = 0 # 수 되돌리기
        
        max_eval = max(max_eval, eval_score)
        alpha = max(alpha, max_eval)
        if alpha >= beta:
            break
            
    return max_eval

# -----------------------------------------------------------------
# << 메인 실행 함수 (V4.2 - 속도 튜닝 완료) >>
# -----------------------------------------------------------------

def run(board_lines, xsize, ysize):
    """
    V4.2: 'Undo Move' 최적화 및 '속도 튜닝' 적용
    """
    
    # --- 튜닝 포인트 1: 수읽기 깊이 (Depth) ---
    # [변경됨] 시간 초과를 확실히 피하기 위해 '3'으로 설정.
    # (Depth 2보다는 훨씬 강력하고, Depth 4보다는 수십 배 빠름)
    SEARCH_DEPTH = 3 
    
    all_empty_moves = get_all_empty_moves(board_lines, xsize, ysize)
    
    if not all_empty_moves:
        return [0, 0, 0]
        
    # --- 튜닝 포인트 2: 초반/중반 전환 시점 ---
    total_moves_possible = (xsize * (ysize+1)) + (ysize * (xsize+1))
    
    # [변경됨] 남은 수가 20% 이하일 때만 Minimax를 사용 (게임의 80%는 탐욕법)
    if len(all_empty_moves) > total_moves_possible * 0.2:
        
        # [초반/중반 전략: V1 탐욕법] (안전하고 빠름)
        winning_moves = []
        safe_moves = []
        unsafe_moves = []
        for move in all_empty_moves:
            side_counts = get_adjacent_box_side_counts(move, board_lines, xsize, ysize)
            is_winning_move = 3 in side_counts
            is_unsafe_move = 2 in side_counts
            if is_winning_move: winning_moves.append(move)
            elif is_unsafe_move: unsafe_moves.append(move)
            else: safe_moves.append(move)
        
        if winning_moves: return random.choice(winning_moves)
        if safe_moves: return random.choice(safe_moves)
        if unsafe_moves: return random.choice(unsafe_moves)
        return random.choice(all_empty_moves)


    # --- [후반부 전략: V4 Negamax] ---
    best_move = all_empty_moves[0]
    best_eval = -float('inf')
    
    alpha = -float('inf')
    beta = float('inf')

    # 수순 정렬
    all_empty_moves.sort(key=lambda m: get_move_score(m, board_lines, xsize, ysize), reverse=True)

    # V4에서는 'negamax_undo'가 보드를 직접 수정하므로,
    # 'run' 함수 레벨에서만 '복사본'을 딱 한 번 만듭니다.
    board_copy = [[[v for v in z] for z in y] for y in board_lines]

    for move in all_empty_moves:
        
        # 1. '수 두기' (복사본 보드에)
        x, y, z = move
        boxes_completed = get_completed_boxes_count(board_copy, move, xsize, ysize)
        board_copy[x][y][z] = 1 
        
        eval_score = 0
        
        # [V4.1 버그 수정 적용됨]
        # 이미 1-ply를 진행했으므로, (SEARCH_DEPTH - 1)을 넘깁니다.
        if boxes_completed > 0:
            eval_score = boxes_completed + negamax_undo(board_copy, SEARCH_DEPTH - 1, alpha, beta, xsize, ysize)
        else:
            eval_score = -negamax_undo(board_copy, SEARCH_DEPTH - 1, -beta, -alpha, xsize, ysize)
            
        # 2. '수 되돌리기' (복사본 보드에)
        board_copy[x][y][z] = 0 
            
        # 3. 최고 점수 갱신
        if eval_score > best_eval:
            best_eval = eval_score
            best_move = move
            
        alpha = max(alpha, best_eval)
            
    return best_move