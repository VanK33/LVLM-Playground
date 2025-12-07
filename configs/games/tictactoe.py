from playground.games import TicTacToeQuestionAnswering

_base_ = ['configs/base.py']

game_name = 'tictactoe'
game_description = dict(
    e2e=('Tic Tac Toe is played on a 3x3 grid. Players take turns placing X '
         'or O in the cells. The goal is to be the first to form an unbroken '
         'line of three marks horizontally, vertically, or diagonally. The '
         'game starts with an empty board, and the O player goes first. The '
         'grid is labeled with rows A to C and columns 1 to 3. You are '
         'playing as O, aiming to win by placing marks strategically. Each '
         'position can only be occupied by one mark, so do not choose a spot '
         'that is already taken. Based on the board state screenshots, please '
         'first observe the current situation, then carefully think and '
         'explain your strategy briefly, and finally output your movement for '
         'this status. Please strictly follow the following format:\n'
         'Observation: <observation>\n'
         'Strategy: <strategy>\n'
         'Movement: <position>\n'
         'where the observation should briefly summarize the current '
         'situation, the strategy is a brief explanation of how you plan to '
         'win the game, and the position can be any combination of rows A to '
         'C and columns 1 to 3, for example, A1, 2B, or c3.'),
    #Original version
    # perceive=(
    #     'Tic Tac Toe is a game played on a 3x3 grid where players take turns '
    #     'placing X or O in the cells. Given a screenshot of the game board, '
    #     'please determine the current game state using a 3x3 matrix. In this '
    #     'matrix, an empty cell should be represented by -1, X should be '
    #     'represented by 1, and O should be represented by 0. Please strictly '
    #     'follow the format:\n'
    #     'Game State: <boardmatrix>\n'
    #     'where <boardmatrix> is a 3x3 matrix. For example,\n'
    #     'Game State: [[-1, -1, -1], [-1, -1, -1], [-1, -1, -1]]\n'
    #     'represents an empty board.'),

    # Cot
    # perceive = (
    #     'Please analyze the 3x3 Tic Tac Toe grid in the given image. You must follow a two-step process to generate the final game state matrix.'
    #     '\n\nSTEP 1: PERCEPTION (Internal Check)'
    #     '\nFirst, identify the content of each cell, reading from top-left to bottom-right (row by row). For this step, use the characters \'X\', \'O\', or \'E\' (to represent an Empty cell). List the results.'
    #     '\n\nSTEP 2: MAPPING and FINAL OUTPUT'
    #     '\nBased on the results of STEP 1, strictly convert the state into a 3x3 matrix using the following numerical mapping:'
    #     '\n- E (Empty cell) MUST be represented by -1.'
    #     '\n- X cell MUST be represented by 1.'
    #     '\n- O cell MUST be represented by 0.'
    #     '\n\nSTRICT FINAL OUTPUT FORMAT (You must include both sections):'
    #     '\n<STEP 1 Output - List the rows/contents here>'
    #     '\nGame State: <3x3 matrix>'
    # ), 


# # in context learning
#     perceive=(
#         'Tic Tac Toe is a game played on a 3x3 grid where players take turns '
#         'placing X or O in the cells. Your task is to determine the current game state '
#         'using a 3x3 matrix where:\n'
#         '- Empty cell = -1\n'
#         '- X = 1\n'
#         '- O = 0\n\n'
        
#         '=== EXAMPLE ===\n'
#         'The first image shows an example Tic Tac Toe board. '
#         'The correct game state for this example board is:\n'
#         'Game State: [[0, -1, -1], [0, 1, 1], [0, 1, -1]]\n\n'
        
#         '=== YOUR TASK ===\n'
#         'Now, analyze the second image (the test board). '
#         'Determine its game state following the same format.\n'
#         'Please strictly output:\n'
#         'Game State: <boardmatrix>\n'
#         'where <boardmatrix> is a 3x3 matrix representing the second image only.'),

      # # in context learning with chain of thought
      # perceive=(
      #       'Tic Tac Toe is a game played on a 3x3 grid where players take turns '
      #       'placing X or O in the cells. Your task is to determine the current game state '
      #       'using a 3x3 matrix where:\n'
      #       '- Empty cell = -1\n'
      #       '- X = 1\n'
      #       '- O = 0\n\n'
            
      #       '=== EXAMPLE ===\n'
      #       'Image 1 Analysis:\n'
      #       'Row 1: [O, Empty, Empty] -> [0, -1, -1]\n'
      #       'Row 2: [O, X, X] -> [0, 1, 1]\n'
      #       'Row 3: [O, X, Empty] -> [0, 1, -1]\n'
      #       'Game State: [[0, -1, -1], [0, 1, 1], [0, 1, -1]]\n\n'
            
      #       '=== YOUR TASK ===\n'
      #       'Now, analyze the second image (the test board).\n'
      #       'Step 1: List the content of each row (X, O, or Empty).\n'
      #       'Step 2: Convert to the matrix format.\n\n'
      #       'Output the final matrix at the end in this format:\n'
      #       'Game State: <boardmatrix>'
      #   ),


# ict v2
      perceive=(
        'Tic Tac Toe is a game played on a 3x3 grid where players take turns '
        'placing X or O in the cells. Given a screenshot of the game board, '
        'please determine the current game state using a 3x3 matrix. In this '
        'matrix, an empty cell should be represented by -1, X should be '
        'represented by 1, and O should be represented by 0. Please strictly '
        'follow the format:\n'
        'Game State: <boardmatrix>\n'
        'where <boardmatrix> is a 3x3 matrix. For example,\n'
        'Game State: [[-1, -1, -1], [-1, -1, -1], [-1, -1, -1]]\n'
        'represents an empty board.'
        'Now here is an example\n'
        'The first image shows an example Tic Tac Toe board. '
        'The correct game state for this example board is:\n'
        'Game State: [[0, -1, -1], [0, 1, 1], [0, 1, -1]]\n\n'
        'Now, analyze the second image (the test board). '),

    rule=(
        'Tic Tac Toe is played on a 3x3 grid. Players take turns placing X or '
        'O in the cells. The game starts with an empty board. The grid is '
        'labeled with rows A to C and columns 1 to 3. Each position can only '
        'be occupied by one mark. Based on the board state, '
        'please find an empty cell where you can place your next stone.\n'
        'Please strictly follow the following format:\n'
        'Movement: <position>\n'
        'where the position can be any combination of rows A to C and columns '
        '1 to 3, for example, A1, B2, or C3.'
    ),

    qa=(
        'Tic Tac Toe is a game played on a 3x3 grid where two players take '
        'turns placing X or O in the cells. The goal is to form a horizontal, '
        'vertical, or diagonal line with three of your own marks. The grid is '
        'labeled with rows A to C and columns 1 to 3. Please answer the '
        'following question based on the provided screenshot of the current '
        'game state:\n'
        '{question}\n'
        'Answer: <answer>\n'
        'where <answer> should be one of A, B, C, or D.'
    ),


    # forward_dynamics=(
    # 'You will see 5 images of a Tic Tac Toe game:\n'
    # 'IMAGE 1: Initial state\n'
    # 'IMAGE 2-5: Four possible next states (choices 0-3)\n\n'
    # 'Action taken: {action}\n\n'
    # 'Which choice shows the correct state after this action?\n'
    # 'Answer: <number>')

  # forward_dynamics=(
  #     'You will see 5 images of Tic Tac Toe boards.\n\n'
  #     'Image-1 shows the INITIAL board state.\n'
  #     'Images 2-5 show four POSSIBLE next states (labeled as choices 0, 1, 2, 3).\n\n'
  #     'An action was taken: {action}\n\n'
  #     'Task: Determine which of the four choices (0, 1, 2, or 3) correctly shows '
  #     'the board state after taking action {action} on the initial board.\n\n'
  #     'Important:\n'
  #     '- If action {action} places a mark on an EMPTY cell, the board changes\n'
  #     '- If action {action} tries to place on an OCCUPIED cell, the board stays the same (invalid move)\n\n'
  #     'Think step by step:\n'
  #     '1. Look at Image-1 (initial state)\n'
  #     '2. Check if action {action} is valid (is that cell empty?)\n'
  #     '3. If valid: find the choice that shows a new mark at {action}\n'
  #     '4. If invalid: find the choice that looks identical to Image-1\n\n'
  #     'Respond with ONLY the number 0, 1, 2, or 3.\n'
  #     'Answer:'
  # )

    forward_dynamics=(
      'You see 5 Tic Tac Toe boards:\n'
      'Image-1 = Initial state\n'
      'Image-2 = Choice 0\n'
      'Image-3 = Choice 1\n'
      'Image-4 = Choice 2\n'
      'Image-5 = Choice 3\n\n'
      'Action attempted: {action}\n\n'
      'First, briefly describe what you see in Image-1.\n'
      'Then, determine which choice (0/1/2/3) correctly shows the result after action {action}.\n\n'
      'Think step-by-step:\n'
      '1. Is cell {action} empty or occupied in Image-1?\n'
      '2. If empty: which choice shows a new mark at {action}?\n'
      '3. If occupied: which choice is identical to Image-1?\n\n'
      'Final Answer (just the number):'
  )

)

player_first = True
qa = TicTacToeQuestionAnswering
