display = False
save_path = 'experiments/game_history'
maximum_trials = 3
device = 'cuda:0'
make_video = True

# benchmark_setting = dict(
#     games=['tictactoe', 'gomoku', 'minesweeper', 'reversi', 'sudoku', 'chess'],
#     sample_size=2000,
#     e2e_round=100,
#     offline_task=['perceive', 'qa', 'rule'],
#     benchmark_path='benchmark'
# )
# duplicate, preserve old for references
benchmark_setting = dict(
    games=['tictactoe'],
    sample_size=100,  # Generate 100 optimal rule-based test cases
    e2e_round=100,
    offline_task=['rule'],  # Only generate rule-based tests with optimal moves
    benchmark_path='benchmark'
)