from collections import Counter
from copy import deepcopy, copy

from constants import Color, Degree, BOARD_SIZE, DEGREE_OPTIONS_LIST, NUM_OF_PLAYER_DEGREE_SOLDIERS, UNMOVABLE
# from game_state import GameState
from soldier import Soldier


class KnowledgeBaseContradiction(Exception):
    pass


class KnowledgeBase(object):
    def __init__(self, color: Color, game_state):
        """
        Create a new knowledge base (all options possible) from given game state and color.
        
        Attributes:
            self._color : color of the player this kb is about
            self._soldier_knowledge_base: KB with soldier as keys, degrees as values
            self._degree_knowledge_base : KB with degree as key and soldiers as values
            self._singletons : count how many soldiers are identified for sure as a certain degree
            self._do_update : bool saying if new information that requires updating has been exposed
            self._degrees_to_update : set of degrees that need updating
        """
        self._color = color
        self._soldier_knowledge_base = dict()  # KB with soldier as keys, degrees as values
        self._degree_knowledge_base = {deg: [] for deg in NUM_OF_PLAYER_DEGREE_SOLDIERS}
        self._singletons = Counter()
        self._do_update = False
        self._degrees_to_update = set()
        board = game_state.board
        # init the knowledge base with full options for each opponent soldier:
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if game_state.board[i][j].color == self._color:
                    for deg in NUM_OF_PLAYER_DEGREE_SOLDIERS:
                        self._degree_knowledge_base[deg].append(board[i][j])
                    self._soldier_knowledge_base[board[i][j]] = DEGREE_OPTIONS_LIST.copy()
    
    def update(self, game_state):
        """
        Get the color of a player and update its knowledge base according to game rules constraints, such as total
        number of each type of soldier
        """
        while self._do_update:
            self._do_update = False
            new_degrees_to_update = set()
            for degree in self._degrees_to_update:
                dead_count = game_state.dead[self._color][degree]
                on_board_count = NUM_OF_PLAYER_DEGREE_SOLDIERS[degree] - dead_count
                # if we already detected all the soldiers of this degree
                if on_board_count == self._singletons[degree]:
                    for soldier in self._degree_knowledge_base[degree].copy():
                        if len(self._soldier_knowledge_base[soldier]) > 1:
                            self._soldier_knowledge_base[soldier].remove(degree)
                            self._degree_knowledge_base[degree].remove(soldier)
                            # if by removing the degree from the KB we created a new singleton, run another iteration
                            if len(self._soldier_knowledge_base[soldier]) == 1:
                                new_single_degree = self._soldier_knowledge_base[soldier][0]
                                self._singletons[new_single_degree] += 1
                                self._do_update = True
                                new_degrees_to_update.add(new_single_degree)
                # if the amount of soldiers that can have this degree equals to the total amount
                if len(self._degree_knowledge_base[degree]) == on_board_count:
                    for optional_soldier in self._degree_knowledge_base[degree]:
                        self._soldier_knowledge_base[optional_soldier] = [degree]
                # if the options for the degree are LESS THAN the number we should have on the board, contradiction
                if len(self._degree_knowledge_base[degree]) < on_board_count:
                    raise KnowledgeBaseContradiction(f"Not enough optional soldiers for degree {degree}")
                self._degrees_to_update = new_degrees_to_update
    
    def remove_soldier_from_kb(self, soldier: Soldier):
        """
        Remove a soldier from the KB
        should be called when a soldier dies, since the KB should only contain info for living soldiers.
        """
        self._soldier_knowledge_base.pop(soldier, None)
        for deg in NUM_OF_PLAYER_DEGREE_SOLDIERS:
            if soldier in self._degree_knowledge_base[deg]:
                self._degree_knowledge_base[deg].remove(soldier)
    
    def add_new_singleton(self, soldier: Soldier, deg: Degree):
        """
        Add the info for a new soldier that was detected with certainty
        """
        self._do_update = True
        self._degrees_to_update.add(deg)
        self._soldier_knowledge_base[soldier] = [deg]
        self._singletons[deg] += 1
    
    def record_soldier_movement(self, soldier: Soldier):
        """
        If a soldier has moved, record that it can't be bomb or flag
        """
        for unmovable_degree in UNMOVABLE:
            if unmovable_degree in self._soldier_knowledge_base[soldier]:
                self._degrees_to_update.add(unmovable_degree)
                self._do_update = True
                self._soldier_knowledge_base[soldier].remove(unmovable_degree)
                if soldier in self._degree_knowledge_base[unmovable_degree]:
                    self._degree_knowledge_base[unmovable_degree].remove(soldier)
        # check if we created a singleton as a result of removing options
        if len(self._soldier_knowledge_base[soldier]) == 1:
            self.add_new_singleton(soldier, self._soldier_knowledge_base[soldier][0])
        if len(self._soldier_knowledge_base[soldier]) == 0:
            raise KnowledgeBaseContradiction(f"No options for soldier {soldier}")
    
    def option_count_for_soldier(self, soldier: Soldier):
        return len(self._soldier_knowledge_base[soldier])
    
    def get_options_for_soldier(self, soldier: Soldier):
        return self._soldier_knowledge_base[soldier].copy()
    
    def store_kb(self):
        store_soldier_kb, store_degree_kb = dict(), dict()
        for sol in self._soldier_knowledge_base:
            store_soldier_kb[sol] = copy(self._soldier_knowledge_base[sol])
        for deg in self._degree_knowledge_base:
            store_degree_kb[deg] = copy(self._degree_knowledge_base[deg])
        data = self._color, copy(self._soldier_knowledge_base), copy(self._degree_knowledge_base), \
            copy(self._singletons), self._do_update, set(self._degrees_to_update)
        return data
    
    def restore_kb(self, stored_info):
        (self._color, self._soldier_knowledge_base, self._degree_knowledge_base, self._singletons, self._do_update,
         self._degrees_to_update) = stored_info
