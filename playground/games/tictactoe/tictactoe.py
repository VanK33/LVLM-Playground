import random
import re
from random import sample

from PyQt5.QtGui import QFont, QPainter, QPixmap
from PyQt5.QtWidgets import QMainWindow

from playground.games import BaseGame, BaseGameLogic
from playground.games.tictactoe.AI import Minimax
from playground.games.tictactoe.tictactoe_ui import Ui_MainWindow
from playground.registry import GAME_REGISTRY
from playground.state_code import GameStatus


class TicTacToeLogic(BaseGameLogic):
    """Logic for Tic Tac Toe game."""

    def __init__(self, game_cfg):
        self.game_cfg = game_cfg
        self.board = [i + 1 for i in range(9)]
        self.bot = None
        self.opponent = None
        self.winner = None
        self.is_finish = False
        self.status = GameStatus.IN_PROGRESS
        self.moves_history = []
        self._initialize_players()

    def _initialize_players(self):
        players = sample(['X', 'O'], 2)
        self.bot = players[0]
        self.opponent = players[1] if self.game_cfg.player_first else players[
            0]  # noqa
        self.bot = players[0] if self.game_cfg.player_first else players[1]

    def make_move(self, index, player):
        if self.board[index] not in ['X', 'O'] and not self.is_finish:
            self.board[index] = player
            self._check_winner()
            return True
        return False

    def _check_winner(self):
        win_positions = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7),
                         (2, 5, 8), (0, 4, 8), (2, 4, 6)]
        for pos in win_positions:
            if self.board[pos[0]] == self.board[pos[1]] == self.board[pos[2]]:
                self.winner = self.board[pos[0]]
                self.is_finish = True
                self.status = GameStatus.WIN if self.winner == self.opponent else GameStatus.LOSE  # noqa
                return
        if all(cell in ['X', 'O'] for cell in self.board) and not self.winner:
            self.is_finish = True
            self.status = GameStatus.TIE

    def input_move(self, move):
        if self.status != GameStatus.IN_PROGRESS:
            return self.status
        col_map = {'1': 0, '2': 1, '3': 2}
        row_map = {'A': 0, 'B': 1, 'C': 2}
        match = re.match(r'([A-Ca-c])([1-3])|([1-3])([A-Ca-c])', move)
        if match:
            row = match.group(1).upper() if match.group(1) else match.group(
                4).upper()
            col = match.group(2) if match.group(2) else match.group(3)
            index = row_map[row] * 3 + col_map[col]
            if self.make_move(index, self.opponent):
                self.moves_history.append(move)
                return self.status
        self.status = GameStatus.INVALID_MOVE
        return self.status

    def get_game_status(self):
        return self.status

    def reset_board(self):
        self.board = [i + 1 for i in range(9)]
        self.winner = None
        self.is_finish = False
        self.status = GameStatus.IN_PROGRESS
        self.moves_history = []

    def get_random_state(self):
        self.reset_board()
        positions = [1, 0, -1]
        random_state = sample(positions * 3, 9)
        if not any(value == -1 for value in random_state):
            rand_index = random.randint(0, 8)
            random_state[rand_index] = -1
        for i, value in enumerate(random_state):
            if value == 1:
                self.board[i] = 'X'
            elif value == 0:
                self.board[i] = 'O'
        return [random_state[i:i + 3] for i in range(0, 9, 3)]

    def get_rule_state(self):
        self.reset_board()
        while True:
            positions = [-1] * 9
            x_count = random.randint(1, 5)
            o_count = x_count if random.choice([True, False]) else x_count - 1
            if o_count < 0:
                o_count = 0
            if x_count + o_count >= 9:
                continue
            positions[:x_count] = [1] * x_count
            positions[x_count:x_count + o_count] = [0] * o_count
            random.shuffle(positions)
            for i, val in enumerate(positions):
                if val == 1:
                    self.board[i] = 'X'
                elif val == 0:
                    self.board[i] = 'O'
            self._check_winner()
            if self.is_finish:
                self.reset_board()
                continue
            board_state = [positions[i:i + 3] for i in range(0, 9, 3)]
            valid_movements = []
            row_map = {0: 'A', 1: 'B', 2: 'C'}
            col_map = {0: '1', 1: '2', 2: '3'}
            for i, val in enumerate(positions):
                if val == -1:
                    r, c = divmod(i, 3)
                    move_str = row_map[r] + col_map[c]
                    valid_movements.append(move_str)
            return board_state, valid_movements

    def get_rule_state_optimal(self):
        """
        Generate a strictly valid, realistic board state where the NEXT move wins immediately.
        """
        row_map = {0: 'A', 1: 'B', 2: 'C'}
        col_map = {0: '1', 1: '2', 2: '3'}
        
        # All winning patterns
        win_patterns = [
            {0, 1, 2}, {3, 4, 5}, {6, 7, 8}, # Rows
            {0, 3, 6}, {1, 4, 7}, {2, 5, 8}, # Cols
            {0, 4, 8}, {2, 4, 6}             # Diagonals
        ]

        # Priority positions for "Realistic" play (Center > Corners > Edges)
        # This makes the random placement look more like a real game attempt
        strategic_priorities = [4, 0, 2, 6, 8, 1, 3, 5, 7]

        max_attempts = 1000
        for _ in range(max_attempts):
            self.reset_board()
            # board array: 0-8. We use integers for processing: 1=X, -1=O, 0=Empty
            # Note: Using 1/-1 makes math easier, but your system uses 1/0/-1. 
            # Let's stick to your convention: 1=X, 0=O, -1=Empty
            
            # 1. Decide who is about to win (The Attacker)
            # Note: To keep within "Max 3 pieces each" constraint:
            # If X attacks: Board needs X=2, O=2. (X places 3rd piece to win)
            # If O attacks: Board needs X=3, O=2. (O places 3rd piece to win)
            attacker_symbol = random.choice(['X', 'O'])
            attacker_val = 1 if attacker_symbol == 'X' else 0
            defender_val = 1 - attacker_val
            
            # Determine exact piece counts needed on board BEFORE the winning move
            if attacker_symbol == 'X':
                # It's X's turn. Previous turns: X, O, X, O. 
                # Current board: X=2, O=2.
                x_count_target = 2
                o_count_target = 2
            else:
                # It's O's turn. Previous turns: X, O, X, O, X.
                # Current board: X=3, O=2.
                x_count_target = 3
                o_count_target = 2

            attacker_count_needed = x_count_target if attacker_symbol == 'X' else o_count_target
            defender_count_needed = o_count_target if attacker_symbol == 'X' else x_count_target

            temp_board = [-1] * 9
            
            # 2. Pick a winning pattern for the Attacker
            pattern = list(random.choice(win_patterns))
            random.shuffle(pattern)
            
            optimal_pos = pattern[0] # The winning hole
            spot1 = pattern[1]
            spot2 = pattern[2]
            
            # Place the threat
            temp_board[spot1] = attacker_val
            temp_board[spot2] = attacker_val
            
            current_attacker_count = 2
            current_defender_count = 0
            
            # 3. Fill the rest validly and realistically
            # We need to place (attacker_count_needed - 2) more attackers
            # And (defender_count_needed) defenders
            
            remaining_attacker = attacker_count_needed - 2
            remaining_defender = defender_count_needed
            
            # Get empty spots excluding the optimal winning spot
            # (We must keep optimal_pos empty for the solution)
            empty_indices = [i for i in range(9) if temp_board[i] == -1 and i != optimal_pos]
            
            # Sort empty indices by "strategic priority" to simulate realistic play
            # But shuffle slightly to keep randomness
            empty_indices.sort(key=lambda x: (strategic_priorities.index(x) + random.randint(-1, 1)))

            # Try to place remaining pieces
            valid_fill = True
            
            # Place Defenders (Opponent tried to play, maybe blocked something else?)
            for _ in range(remaining_defender):
                if not empty_indices: 
                    valid_fill = False; break
                pos = empty_indices.pop(0) # Pick best available strategic spot
                temp_board[pos] = defender_val
                
            # Place Remaining Attackers (if any)
            for _ in range(remaining_attacker):
                if not empty_indices: 
                    valid_fill = False; break
                # For attacker extra pieces, maybe random is okay, or strategic
                pos = empty_indices.pop(0) 
                temp_board[pos] = attacker_val
                
            if not valid_fill: continue

            # 4. CRITICAL: Safety Check
            # Ensure NO ONE has won yet on this board.
            # If the random placement accidentally created a win for Defender, 
            # or a PRE-EXISTING win for Attacker, discard.
            
            is_invalid_state = False
            
            # Check all lines
            for p in win_patterns:
                p_list = list(p)
                v1, v2, v3 = temp_board[p_list[0]], temp_board[p_list[1]], temp_board[p_list[2]]
                
                # If any line is full of same pieces (not -1)
                if v1 != -1 and v1 == v2 and v2 == v3:
                    is_invalid_state = True
                    break
            
            if is_invalid_state:
                continue

            # 5. Format Output
            # Map temp_board to self.board format
            for i, val in enumerate(temp_board):
                if val == 1: self.board[i] = 'X'
                elif val == 0: self.board[i] = 'O'
                else: self.board[i] = i + 1  # Empty cells are represented by position number (1-9)

            # Prepare returns
            board_state = [temp_board[i:i+3] for i in range(0, 9, 3)] # 3x3 Matrix
            
            optimal_r, optimal_c = divmod(optimal_pos, 3)
            optimal_move_str = row_map[optimal_r] + col_map[optimal_c]
            
            # Identify suboptimal moves (any empty spot that isn't optimal_pos)
            final_empty = [i for i in range(9) if temp_board[i] == -1]
            suboptimal_moves = []
            for idx in final_empty:
                if idx != optimal_pos:
                    r, c = divmod(idx, 3)
                    suboptimal_moves.append(row_map[r] + col_map[c])
            
            if not suboptimal_moves: 
                # Need at least one wrong choice for the benchmark
                continue

            # Explanation
            attacker_name = "X" if attacker_val == 1 else "O"
            explanation = f"Immediate win for {attacker_name}. Placing at {optimal_move_str} completes a line."
            
            return board_state, optimal_move_str, suboptimal_moves, explanation

        # Fallback: If we couldn't generate optimal state after max_attempts, use old method
        print("Warning: Failed to generate optimal state, falling back to old method")
        board_state, valid_movements = self.get_rule_state()
        if valid_movements:
            return board_state, valid_movements[0], valid_movements[1:], "Fallback: any valid move"
        else:
            # Last resort: return empty data (should rarely happen)
            return [[0, 0, 0], [0, 0, 0], [0, 0, 0]], "A1", [], "Error: no valid state generated"

    def calculate_score(self):
        """Calculate score based on steps taken and game outcome."""
        player_steps = len(self.moves_history)
        base_score = player_steps * 10
        bonus_score = 0
        if self.status == GameStatus.WIN:
            bonus_score = 50
        elif self.status == GameStatus.TIE:
            bonus_score = 20
        total_score = base_score + bonus_score
        return total_score

    def parse_e2e(self, lmm_output):
        """Parse e2e output to a move."""
        match = re.search(r'Movement:\s*([A-Ca-c][1-3]|[1-3][A-Ca-c])',
                          lmm_output, re.IGNORECASE)
        if match:
            move = match.group(1).upper()
            if move[0].isdigit():
                move = move[1] + move[0]
            return move
        return GameStatus.INVALID_MOVE


class TicTacToeRenderer(QMainWindow):
    """Renderer for Tic Tac Toe UI."""

    def __init__(self, logic):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.logic = logic
        self.select_font = QFont()
        self.select_font.setPointSize(35)
        self._update_ui()

    def _update_ui(self):
        color_map = {'X': 'red', 'O': 'blue'}
        color = color_map.get(self.logic.opponent, 'black')
        self.ui.label_2.setText(
            f'You are playing as <span style="color:{color}">{self.logic.opponent}</span>'  # noqa
        )
        for i, cell in enumerate(self.logic.board):
            button = self.ui.buttons[i]
            if cell in ['X', 'O']:
                button.setFont(self.select_font)
                button.setText(cell)
                button.setStyleSheet('color:blue' if cell ==
                                     'O' else 'color:red')
            else:
                button.setText('')
                button.setStyleSheet('')

    def get_screenshot(self):
        board_width = 500
        board_height = 600
        screenshot = QPixmap(board_width, board_height)
        painter = QPainter(screenshot)
        self.render(painter)
        painter.end()
        return screenshot


@GAME_REGISTRY.register('tictactoe')
class TicTacToe(BaseGame):
    AI_component = True

    def __init__(self, game_cfg):
        super().__init__(game_cfg)
        self.logic = TicTacToeLogic(game_cfg)
        self.renderer = None
        self.minimax = Minimax(
            self.logic.bot,
            self.logic.opponent) if game_cfg.player_first else None
        if not game_cfg.player_first:
            self.ai_move()

    def get_screenshot(self):
        if self.renderer is None:
            self.renderer = TicTacToeRenderer(self.logic)
        self.renderer._update_ui()
        return self.renderer.get_screenshot()

    def input_move(self, move):
        return self.logic.input_move(move)

    def get_game_status(self):
        return self.logic.get_game_status()

    def get_random_state(self):
        return self.logic.get_random_state()

    def get_rule_state(self):
        return self.logic.get_rule_state()

    def get_rule_state_optimal(self):
        return self.logic.get_rule_state_optimal()

    def ai_move(self):
        if not self.AI_component or self.logic.is_finish:
            return None
        game_match = self.minimax.generate_2d(self.logic.board)
        move_index = self.minimax.find_best_move(game_match)
        if self.logic.make_move(move_index, self.logic.bot):
            return f'{chr(65 + move_index // 3)}{move_index % 3 + 1}'
        return None

    def calculate_score(self):
        return self.logic.calculate_score()

    def parse_e2e(self, lmm_output):
        return self.logic.parse_e2e(lmm_output)
