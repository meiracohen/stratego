import math
import random

from game_state import GameState
from constants import Color, Degree, NUM_OF_PLAYER_SOLDIERS, BOARD_SIZE, SOLDIER_COUNT_FOR_EACH_DEGREE, OP_COLOR
from scipy import spatial

# import numpy as np

# from soldier import Color

SUM_DEGREES_OF_PLAYER_FOR_HEURISTIC = sum(
    [SOLDIER_COUNT_FOR_EACH_DEGREE[deg] * deg for deg in Degree if
     deg not in [Degree.BOMB, Degree.THREE, Degree.WATER, Degree.EMPTY]] + [
        SOLDIER_COUNT_FOR_EACH_DEGREE[Degree.BOMB] * 5, SOLDIER_COUNT_FOR_EACH_DEGREE[Degree.THREE] * 5])

MAX_DISTANCE_TO_FLAG = BOARD_SIZE


def null_heuristic(game_state: GameState, color: Color):
    return 0


def random_heuristic(game_state: GameState, color: Color):
    return random.randint(0, 10)


def max_my_soldier_num_heuristic(game_state: GameState, color: Color):
    is_done = math.inf if game_state.done else 0
    if is_done != 0:
        return is_done
    # return len(game_state.soldier_knowledge_base[color]) / NUM_OF_PLAYER_SOLDIERS
    return len(game_state.get_knowledge_base(color).get_living_soldiers()) / NUM_OF_PLAYER_SOLDIERS


def min_opp_soldiers_num_heuristic(game_state: GameState, color: Color):
    is_done = math.inf if game_state.done else 0
    if is_done != 0:
        return is_done
    op_color = Color.RED if color == Color.BLUE else Color.BLUE
    val = 0
    dead_opp = game_state.dead[op_color]
    for i in dead_opp:
        val += dead_opp[i]
    return val / NUM_OF_PLAYER_SOLDIERS


def max_my_soldier_degree_heuristic(game_state: GameState, color: Color):
    is_done = math.inf if game_state.done else 0
    if is_done != 0:
        return is_done
    val = 0
    for s in game_state.get_knowledge_base(color).get_living_soldiers():
        val += s.degree if s.degree != Degree.BOMB and s.degree != Degree.THREE else 5

    return val / SUM_DEGREES_OF_PLAYER_FOR_HEURISTIC


def min_opp_soldier_degree_heuristic(game_state: GameState, color: Color):
    is_done = math.inf if game_state.done else 0
    if is_done != 0:
        return is_done
    op_color = Color.RED if color == Color.BLUE else Color.BLUE
    return 1 - (max_my_soldier_degree_heuristic(game_state, op_color) / SUM_DEGREES_OF_PLAYER_FOR_HEURISTIC)


def opp_distance_to_flag_heuristic(game_state: GameState, color: Color):
    is_done = math.inf if game_state.done else 0
    if is_done != 0:
        return is_done
    op_color = Color.RED if color == Color.BLUE else Color.BLUE
    loc = []
    for s in game_state.get_knowledge_base(op_color).get_living_soldiers():
        loc.append([s.x, s.y])
    my_flag = [s for s in game_state.get_knowledge_base(color).get_living_soldiers() if s.degree == Degree.FLAG]
    if len(my_flag) == 0:
        return -10
    my_flag = my_flag[0]
    distance, index = spatial.KDTree(loc).query([my_flag.x, my_flag.y])
    return 1 - distance / MAX_DISTANCE_TO_FLAG


def distance_to_opp_flag_heuristic(game_state: GameState, color: Color):
    is_done = math.inf if game_state.done else 0
    if is_done != 0:
        return is_done
    op_color = Color.RED if color == Color.BLUE else Color.BLUE
    return 1 - opp_distance_to_flag_heuristic(game_state, op_color)


def small_dist_opp_to_flag_heuristic(game_state: GameState, color: Color):
    is_done = math.inf if game_state.done else 0
    if is_done != 0:
        return is_done
    return -20 if opp_distance_to_flag_heuristic(game_state, color) < 0.15 else 0


def min_of_opp_soldiers_that_are_flag_options_heuristic(game_state: GameState, color: Color):
    is_done = math.inf if game_state.done else 0
    if is_done != 0:
        return is_done
    if game_state.can_op_soldier_be_flag is None:
        return 0
    else:
        val = 0
        op_color = Color.RED if color == Color.BLUE else Color.BLUE
        for s in game_state.get_knowledge_base(op_color).get_living_soldiers():
            val += 1 if game_state.can_op_soldier_be_flag[s] else 0
        return 1 - val / NUM_OF_PLAYER_SOLDIERS


def sum_of_heuristics_heuristic(game_state: GameState, color: Color):
    is_done = math.inf if game_state.done else 0
    if is_done != 0:
        return is_done
    val = 0
    # val += 8 * min_opp_soldiers_num_heuristic(game_state, color)
    val += 6 * min_of_opp_soldiers_that_are_flag_options_heuristic(game_state, color)
    val += 2 * max_my_soldier_degree_heuristic(game_state, color)
    val += small_dist_opp_to_flag_heuristic(game_state, color)
    # val += 8 * distance_to_opp_flag_heuristic(game_state, color)
    return val


# http://users.utcluj.ro/~agroza/papers/2018/stratego.pdf

def better_num_soldiers_difference_heuristic(game_state: GameState, color: Color):
    # pieceW, rankW, moveW, distW = 1, 0.05, 0.03, 0.02
    pieceW, rankW, moveW, distW, flagW = 1.4, 0.045, 0.03, 0.018, 2

    sum = 0
    op_color = OP_COLOR[color]
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            soldier = game_state.board[i][j]
            if soldier.color == color:
                sum += pieceW
                if soldier.show_me:
                    sum -= rankW * soldier.degree
                if i < 6:
                    sum -= distW * (6 - i) ** 2
            elif soldier.color == op_color:
                sum -= pieceW
                if soldier.show_me:
                    sum += rankW * soldier.degree
                if i > 3:
                    sum += distW * (i - 3) ** 2
    return sum


# i-1j-1      i-1j        i-1j+1
# ij-1        ij          ij+1
# i+1j-1      i+1j        i+1j+1
def get_sum_around_soldier(game_state: GameState, i: int, j: int, color: Color) -> float:
    sum: float = 0
    op_color = Color.BLUE if color == Color.RED else Color.RED
    positions = [(i - 1, j - 1, 1), (i - 1, j, 20), (i - 1, j + 1, 1),
                 (i, j - 1, 20), (i, j + 1, 20),
                 (i + 1, j - 1, 1), (i + 1, j, 20), (i + 1, j + 1, 1)]
    for (x, y, w) in positions:
        if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
            continue
        soldier = game_state.board[x][y]
        op = -1 if soldier.color == op_color else 1
        if soldier.degree != Degree.EMPTY:
            sum += flagW * w * soldier.degree * op
        else:
            sum += flagW * w * -9 * op
    # print(f"shira flag sum: {sum}")
    return sum

# try not to reveal 10
# once 10 revealed- it should attack only identified pieces.
# 1 and 9 should be together as long as they can
# if enemy gets close to a piece it can kill- bring a 2 (without him knowing) for it to chase instead
# attack pieces from high to low
# never leave flag unprotected
# start with moving lower pieces and then once enemy's pieces are revealed kill them with higher ranks
