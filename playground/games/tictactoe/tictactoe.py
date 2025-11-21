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
        Generate a realistic board state with an optimal winning move.

        Requirements:
        1. Board simulates realistic gameplay (both players attempting to win)
        2. X and O each have at most 3 pieces
        3. There exists an optimal move that leads to immediate victory
        4. There are suboptimal moves (other legal moves that don't win)

        Returns:
            board_state: 3x3 matrix representing the game state
            optimal_move: The winning move (string like "A1")
            suboptimal_moves: List of legal but non-winning moves
            explanation: Why the optimal move wins
        """
        self.reset_board()
        row_map = {0: 'A', 1: 'B', 2: 'C'}
        col_map = {0: '1', 1: '2', 2: '3'}

        # All winning patterns (row, col, diagonal)
        win_patterns = [
            (0, 1, 2),  # Row A
            (3, 4, 5),  # Row B
            (6, 7, 8),  # Row C
            (0, 3, 6),  # Col 1
            (1, 4, 7),  # Col 2
            (2, 5, 8),  # Col 3
            (0, 4, 8),  # Diagonal \
            (2, 4, 6),  # Diagonal /
        ]

        max_attempts = 1000
        for attempt in range(max_attempts):
            self.reset_board()
            positions = [-1] * 9

            # Step 1: Choose a random winning pattern and attacker
            winning_pattern = random.choice(win_patterns)
            attacker = random.choice([1, 0])  # 1=X, 0=O
            defender = 1 - attacker

            # Step 2: Place 2 attacker pieces in the winning pattern, leave 1 empty
            pattern_positions = list(winning_pattern)
            random.shuffle(pattern_positions)
            optimal_pos = pattern_positions[0]  # This will be the winning move
            positions[pattern_positions[1]] = attacker
            positions[pattern_positions[2]] = attacker

            # Step 3: Place defender pieces (1-3 pieces) strategically
            # Ensure defender doesn't have a winning threat
            defender_count = random.randint(1, 3)
            attacker_count = 2  # We already placed 2

            # Adjust counts to follow game rules (X goes first, so X >= O)
            if attacker == 0:  # If O is attacker
                # O can only have same or one less than X
                if defender_count < attacker_count:
                    defender_count = attacker_count
            else:  # If X is attacker
                # X should have same or one more than O
                if defender_count > attacker_count:
                    defender_count = attacker_count

            # Find empty positions (excluding optimal_pos)
            available_positions = [i for i in range(9)
                                 if positions[i] == -1 and i != optimal_pos]

            if len(available_positions) < defender_count:
                continue

            # Place defender pieces, avoiding creating their own winning threat
            placed_defender = 0
            random.shuffle(available_positions)

            for pos in available_positions:
                if placed_defender >= defender_count:
                    break

                # Try placing defender here
                positions[pos] = defender

                # Check if this creates a winning threat for defender
                defender_has_threat = False
                for pattern in win_patterns:
                    count = sum(1 for p in pattern if positions[p] == defender)
                    empty = sum(1 for p in pattern if positions[p] == -1)
                    if count == 2 and empty == 1:
                        # Defender has a winning threat
                        defender_has_threat = True
                        break

                if defender_has_threat:
                    positions[pos] = -1  # Undo
                else:
                    placed_defender += 1

            # Verify we placed enough defender pieces
            if placed_defender < 1:  # Need at least 1 defender piece
                continue

            # Step 4: Verify there are suboptimal moves
            empty_positions = [i for i in range(9) if positions[i] == -1]
            if len(empty_positions) < 2:  # Need at least 2 empty (optimal + suboptimal)
                continue

            # Step 5: Build board and verify
            for i, val in enumerate(positions):
                if val == 1:
                    self.board[i] = 'X'
                elif val == 0:
                    self.board[i] = 'O'

            # Check game is not finished
            self._check_winner()
            if self.is_finish:
                continue

            # Step 6: Generate moves and explanation
            board_state = [positions[i:i + 3] for i in range(0, 9, 3)]

            optimal_r, optimal_c = divmod(optimal_pos, 3)
            optimal_move = row_map[optimal_r] + col_map[optimal_c]

            suboptimal_moves = []
            for i in empty_positions:
                if i != optimal_pos:
                    r, c = divmod(i, 3)
                    suboptimal_moves.append(row_map[r] + col_map[c])

            # Generate explanation
            attacker_symbol = 'X' if attacker == 1 else 'O'
            pattern_names = {
                (0, 1, 2): "row A",
                (3, 4, 5): "row B",
                (6, 7, 8): "row C",
                (0, 3, 6): "column 1",
                (1, 4, 7): "column 2",
                (2, 5, 8): "column 3",
                (0, 4, 8): "main diagonal",
                (2, 4, 6): "anti-diagonal"
            }
            pattern_name = pattern_names.get(winning_pattern, "line")
            explanation = f"Playing {optimal_move} completes {pattern_name} with three {attacker_symbol}'s, winning immediately."

            return board_state, optimal_move, suboptimal_moves, explanation

        # Fallback to old method if we couldn't generate optimal state
        board_state, valid_movements = self.get_rule_state()
        return board_state, valid_movements[0], valid_movements[1:], "No optimal strategy found."

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
