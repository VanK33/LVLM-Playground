import json
import os.path as osp
import re

import numpy as np


class Metric:
    MATRIX_CONFIG = {
        'tictactoe': {
            'size': 3,
            'count': 9,
            'valid_range': [-1, 0, 1]
        },
        'sudoku': {
            'size': 9,
            'count': 81,
            'valid_range': list(range(10))
        },
        'chess': {
            'size': 8,
            'count': 64,
            'valid_range': list(range(-6, 7))
        },
        'gomoku': {
            'size': 15,
            'count': 225,
            'valid_range': [0, 1, 2]
        },
        'minesweeper': {
            'size': 8,
            'count': 64,
            'valid_range': [-1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        },
        'reversi': {
            'size': 8,
            'count': 64,
            'valid_range': [0, 1, 2]
        }
    }

    RULE_FORMATS = {
        'tictactoe': r'(?:Movement:\s*)?([A-Ca-c][1-3]|[1-3][A-Ca-c])',
        'sudoku': r'(?:Movement:\s*)?([A-Ia-i][1-9]\s[1-9])',
        'chess':
        r'(?:Movement:\s*)?([a-hA-H][1-8][a-hA-H][1-8]|[a-hA-H][1-8]|O-O|O-O-O|(?:N|B|R|Q|K)?[a-hA-H]?[1-8]?x?[a-hA-H][1-8](?:=[QRNB])?|(?:N|B|R|Q|K)[a-hA-H][1-8])',  # noqa
        'gomoku':
        r'(?:Movement:\s*)?([A-Oa-o](?:[1-9]|1[0-5])|(?:[1-9]|1[0-5])[A-Oa-o])',  # noqa
        'minesweeper': r'(?:Movement:\s*)?([A-Ha-h][1-8]|[1-8][A-Ha-h])',
        'reversi': r'(?:Movement:\s*)?([A-Ha-h][1-8]|[1-8][A-Ha-h])'
    }

    TASK_ABILITIES = {
        'perceive': ['Perception'],
        'qa': ['Perception', 'Reasoning'],
        'rule': ['Perception', 'Reasoning', 'Decision'],
        'e2e': ['Perception', 'Reasoning', 'Decision', 'Adversary']
    }

    GAME_RATINGS = {
        'tictactoe': {
            'Perception': 0.5,
            'Reasoning': 0.5,
            'Decision': 0.5,
            'Adversary': 0.5
        },
        'reversi': {
            'Perception': 1.5,
            'Reasoning': 1.5,
            'Decision': 2.5,
            'Adversary': 2.5
        },
        'sudoku': {
            'Perception': 3.5,
            'Reasoning': 2.0,
            'Decision': 2.0,
            'Adversary': 0
        },
        'minesweeper': {
            'Perception': 4.0,
            'Reasoning': 5.0,
            'Decision': 3.0,
            'Adversary': 0
        },
        'gomoku': {
            'Perception': 5.0,
            'Reasoning': 4.0,
            'Decision': 3.5,
            'Adversary': 4.0
        },
        'chess': {
            'Perception': 3.5,
            'Reasoning': 3.0,
            'Decision': 5.0,
            'Adversary': 5.0
        }
    }

    def __init__(self, record_path, annotation_dir):
        self.record_path = record_path
        self.annotation_dir = annotation_dir
        with open(self.record_path, 'r') as f:
            self.record = json.load(f)
        self.debug_results = {}
        self.scores = {}
        self.weighted_summary = {}


    def parse_perceive(self, lmm_output, game_name):
        if not lmm_output:
            return None, "No output provided"

        target_content = lmm_output
        if "Game State:" in lmm_output:
            target_content = lmm_output.split("Game State:")[-1]

        # 定义 Python 列表和 LaTeX 矩阵的匹配模式
        python_pattern = r'(\[\s*\[.*?\]\s*\])'
        latex_pattern = r'(\\begin\{bmatrix\}.*?\\end\{bmatrix\})'
        
        combined_pattern = f"{python_pattern}|{latex_pattern}"
        
        iterator = re.finditer(combined_pattern, target_content, re.DOTALL)
        matches = [m.group(0) for m in iterator]

        # 如果在 target_content 没找到，尝试在全文找
        if not matches and target_content != lmm_output:
            iterator = re.finditer(combined_pattern, lmm_output, re.DOTALL)
            matches = [m.group(0) for m in iterator]
        
        if not matches:
            return None, "No matrix pattern found"
        
        # 过滤掉显然是代码逻辑的部分
        valid_matches = [m for m in matches if "int(" not in m and "board[" not in m]
        
        if not valid_matches:
            return None, "Only code logic found, no concrete data matrix"
        
        final_matrix_str = valid_matches[-1]

        # ================= 修复部分开始 =================
        # 1. 先清理 LaTeX 命令。
        # 正则解释：匹配以 \ 开头的单词，后面可选跟着 {...} 结构。
        # 这会把 \begin{bmatrix}, \end{bmatrix}, \hline 等全部删掉。
        # 这样 'bmatrix' 这个词就被移除了，里面的 'x' 不会干扰后续替换。
        clean_str = re.sub(r'\\[a-zA-Z]+(\{.*?\})?', '', final_matrix_str)

        # 2. 清理常见干扰字符
        clean_str = clean_str.replace("'", "").replace('"', "")

        # 3. 进行棋子替换 (现在可以安全地把 x 换成 1 了)
        clean_str = clean_str.replace("X", "1").replace("x", "1")
        clean_str = clean_str.replace("O", "0").replace("o", "0")
        # ================= 修复部分结束 =================

        numbers = re.findall(r'-?\d+', clean_str)
        
        config = self.MATRIX_CONFIG.get(game_name)
        if not config:
            return None, f"Unknown game config: {game_name}"
            
        if len(numbers) != config['count']:
            return None, f"Number count mismatch: expected {config['count']}, got {len(numbers)}. Parsed string: {final_matrix_str}"

        try:
            matrix_flat = [int(num) for num in numbers]
            if not all(num in config['valid_range'] for num in matrix_flat):
                    return None, f"Numbers out of range {config['valid_range']}"

            matrix = [
                matrix_flat[i:i + config['size']]
                for i in range(0, config['count'], config['size'])
            ]
            return matrix, None
        except ValueError as e:
            return None, f'Conversion error: {e}'

    def parse_rule(self, lmm_output, game_name):
        if lmm_output is None:
            return None, 'No valid output found.'
        pattern = self.RULE_FORMATS.get(game_name)
        if not pattern:
            return None, 'No pattern defined for this game'
        match = re.search(pattern, lmm_output, re.IGNORECASE)
        if match:
            move = match.group(1)
            if game_name in ['tictactoe', 'gomoku', 'minesweeper', 'reversi'
                             ] and move[0].isdigit():
                move = move[1:] + move[0]
            return move.upper(), None
        return None, 'Move format not matched'

    def parse_qa(self, lmm_output, _):
        if lmm_output is None:
            return None, 'No valid output found.'
        patterns = [
            r'(?:Final\s+Answer[:\s]*(?:\\boxed{)?\s*)([A-Da-d])(?:\s*})?',
            r'Answer[:\s]+([A-Da-d])(?:\s*\d)?', r'\[([A-Da-d])\]'
        ]
        for pattern in patterns:
            match = re.search(pattern, lmm_output, re.IGNORECASE)
            if match:
                return match.group(1).upper(), None

        match = re.search(r'([A-Da-d])(?:\s*\]|\.|$|\s)', lmm_output,
                          re.IGNORECASE)
        if match:
            return match.group(1).upper(), None

        return None, 'Answer format not matched (expected [A-D])'

    def evaluate_perceive(self, game_name, annotation):
        results = self.record['perceive'][game_name]
        accuracies = []
        debug_data = []

        verification_data = []

        # Evaluate each result
        error_states = {
            'empty_as_piece': 0, # empty cell(-1) interpreted as O/X(0/1)
            'piece_as_empty': 0, # O/X(0/1) interpreted as empty cell(-1)
            'wrong_piece': 0,     # O interpreted as X or vice versa
            'correct':0,
            'total_cells':0
        }
        for i, result in enumerate(results):
            if result is None or 'raw' not in result:
                debug_data.append({
                    'index': i,
                    'raw': None,
                    'parsed': None,
                    'reason': 'No raw output provided'
                })
                accuracies.append(0)
                continue

            lmm_output = result['raw']
            gt = annotation['annotations'][i]['gt']
            parsed_matrix, reason = self.parse_perceive(lmm_output, game_name)
            entry = {'index': i, 'raw': lmm_output, 'parsed': parsed_matrix}
            if reason:
                entry['reason'] = reason
            debug_data.append(entry)
            if parsed_matrix is None:
                accuracies.append(0)
                verification_data.append({
                    'index': i, 'parsed': f"Parse Error: {reason}", 'gt': gt, 'score': 0, 'raw': lmm_output
                })
            else:
                gt_np = np.array(gt)
                matrix_np = np.array(parsed_matrix)
                accuracy = np.sum(gt_np == matrix_np) / gt_np.size
                accuracies.append(accuracy)

                error_detail = self._analyze_perceive_errors(gt_np, matrix_np)
                entry['error_analysis'] = error_detail

                for key in error_states:
                    error_states[key] += error_detail.get(key, 0)

                debug_data.append(entry)

                verification_data.append({
                    'index': i, 'parsed': parsed_matrix, 'gt': gt, 'score': accuracy, 'raw': lmm_output
                })
        
        self.log_verification('perceive', game_name, verification_data)

        # Calculate error percentages
        total_cells = error_states['total_cells']
        if total_cells > 0:
            error_percentages = {
                'empty_as_piece':round(error_states['empty_as_piece']/total_cells * 100, 2),
                'piece_as_empty':round(error_states['piece_as_empty']/total_cells * 100, 2),
                'wrong_piece':round(error_states['wrong_piece']/total_cells * 100, 2),
                'correct':round(error_states['correct']/total_cells * 100, 2)
            }
        else:
            error_percentages = {k: 0 for k in ['empty_as_piece', 'piece_as_empty', 'wrong_piece', 'correct']}
       
        if 'perceive' not in self.debug_results:
            self.debug_results['perceive'] = {}
        self.debug_results['perceive'][game_name] = debug_data
        avg_score = round(sum(accuracies) /
                          len(accuracies), 3) if accuracies else 0
        if 'perceive' not in self.scores:
            self.scores['perceive'] = {}

        # Store both average score and error analysis
        self.scores['perceive'][game_name] = {
            'average_accuracy': avg_score,
            'error_percentages': error_percentages,
            'error_states': error_states
        }
        return avg_score
    
    def _analyze_perceive_errors(self, gt_np, matrix_np):
        error_details = {
            'empty_as_piece': 0,
            'piece_as_empty': 0,
            'wrong_piece': 0,
            'correct': 0,
            'total_cells': gt_np.size
        }

        empty_value = -1
        piece_values = [0,1]

        for gt_val, pred_val in zip(gt_np.flat, matrix_np.flat):
            if gt_val == pred_val:
                error_details['correct'] += 1
            elif gt_val == empty_value and pred_val in piece_values:
                error_details['empty_as_piece'] += 1
            elif gt_val in piece_values and pred_val == empty_value:
                error_details['piece_as_empty'] += 1
            elif gt_val in piece_values and pred_val in piece_values and gt_val != pred_val:
                error_details['wrong_piece'] += 1

        return error_details

    def evaluate_qa(self, game_name, annotation):
        results = self.record['qa'][game_name]
        accuracies = []
        debug_data = []
        for i, result in enumerate(results):
            if result is None or 'raw' not in result:
                debug_data.append({
                    'index': i,
                    'raw': None,
                    'parsed': None,
                    'reason': 'No raw output provided'
                })
                accuracies.append(0)
                continue
            lmm_output = result['raw']
            gt = annotation['annotations'][i]['gt']['answer']
            parsed_answer, reason = self.parse_qa(lmm_output, game_name)
            entry = {'index': i, 'raw': lmm_output, 'parsed': parsed_answer}
            if reason:
                entry['reason'] = reason
            debug_data.append(entry)
            accuracy = 1 if parsed_answer == gt else 0
            accuracies.append(accuracy)
        if 'qa' not in self.debug_results:
            self.debug_results['qa'] = {}
        self.debug_results['qa'][game_name] = debug_data
        avg_score = round(sum(accuracies) /
                          len(accuracies), 3) if accuracies else 0
        if 'qa' not in self.scores:
            self.scores['qa'] = {}
        self.scores['qa'][game_name] = avg_score
        return avg_score

    def evaluate_rule(self, game_name, annotation):
        results = self.record['rule'][game_name]
        accuracies = []
        debug_data = []
        for i, result in enumerate(results):
            if result is None or 'raw' not in result:
                debug_data.append({
                    'index': i,
                    'raw': None,
                    'parsed': None,
                    'reason': 'No raw output provided'
                })
                accuracies.append(0)
                continue
            lmm_output = result['raw']
            valid_movements = annotation['annotations'][i]['gt'][
                'valid_movements']
            parsed_move, reason = self.parse_rule(lmm_output, game_name)
            entry = {'index': i, 'raw': lmm_output, 'parsed': parsed_move}
            if reason:
                entry['reason'] = reason
            debug_data.append(entry)
            if parsed_move:
                normalized_move = parsed_move.lower()
                normalized_valid_movements = [
                    move.lower() for move in valid_movements
                ]
                accuracy = 1 if normalized_move in normalized_valid_movements else 0  # noqa
            else:
                accuracy = 0
            accuracies.append(accuracy)
        if 'rule' not in self.debug_results:
            self.debug_results['rule'] = {}
        self.debug_results['rule'][game_name] = debug_data
        avg_score = round(sum(accuracies) /
                          len(accuracies), 3) if accuracies else 0
        if 'rule' not in self.scores:
            self.scores['rule'] = {}
        self.scores['rule'][game_name] = avg_score
        return avg_score

    def evaluate_e2e(self, game_name):
        results = self.record['e2e'][game_name]
        scores = []
        debug_data = []
        for i, result in enumerate(results):
            if result is None or not isinstance(result,
                                                dict) or 'score' not in result:
                debug_data.append({
                    'index':
                    i,
                    'parsed':
                    None,
                    'reason':
                    f'Invalid e2e data format: {result}'
                })
                scores.append(0)
            else:
                debug_data.append({
                    'index': i,
                    'parsed': {
                        'score': result['score'],
                        'steps': result.get('steps', 0)
                    }
                })
                scores.append(result['score'])
        if 'e2e' not in self.debug_results:
            self.debug_results['e2e'] = {}
        self.debug_results['e2e'][game_name] = debug_data
        avg_score = round(sum(scores) / len(scores), 3) if scores else 0
        if 'e2e' not in self.scores:
            self.scores['e2e'] = {}
        self.scores['e2e'][game_name] = avg_score
        return avg_score

    def evaluate_all(self):
        if self.scores and self.weighted_summary:
            return self.scores

        self.weighted_summary = {}

        for task in self.record:
            total_weighted_score = 0
            total_weight = 0

            for game in self.record[task]:
                annotation_path = osp.join(self.annotation_dir, task, game,
                                           'annotation.json')
                if task != 'e2e' and osp.exists(annotation_path):
                    with open(annotation_path, 'r') as f:
                        annotation = json.load(f)
                else:
                    annotation = None

                if task == 'perceive':
                    avg_score = self.evaluate_perceive(game, annotation)
                elif task == 'qa':
                    avg_score = self.evaluate_qa(game, annotation)
                elif task == 'rule':
                    avg_score = self.evaluate_rule(game, annotation)
                elif task == 'e2e':
                    avg_score = self.evaluate_e2e(game)

                game_ratings = self.GAME_RATINGS.get(game.lower(), {})
                task_abilities = self.TASK_ABILITIES.get(task, [])
                weight = sum(
                    game_ratings.get(ability, 0) for ability in task_abilities)
                weighted_score = avg_score * weight
                total_weighted_score += weighted_score
                total_weight += weight if weight > 0 else 1

            weighted_avg_score = round(total_weighted_score / total_weight,
                                       3) if total_weight > 0 else 0
            self.weighted_summary[task] = {
                'weighted_average': weighted_avg_score
            }

        return self.scores

    def save_evaluation(self, output_path):
        self.evaluate_all()
        result = {
            'weighted_summary': self.weighted_summary,
            'scores': self.scores,
            'details': self.debug_results,
        }
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=4)
    
    def log_verification(self, task, game_name, log_data):
        # 将日志保存在 record_path 同级目录下
        base_dir = osp.dirname(self.record_path)
        log_file = osp.join(base_dir, f"{game_name}_{task}_verification.json")
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Verification Log for {game_name} - {task}\n")
            f.write(f"Total Records: {len(log_data)}\n")
            f.write("="*50 + "\n")
            
            for entry in log_data:
                f.write(f"Run #: {entry['index']}\n")
                f.write(f"Result from AI (Parsed): {entry['parsed']}\n")
                f.write(f"Ground True: {entry['gt']}\n")
                f.write(f"Evaluator result (Score/Error): {entry['score']}\n")
                f.write(f"Raw AI Output: {repr(entry['raw'])}\n") #以此检查是否因为格式问题导致解析失败
                f.write("-" * 30 + "\n")
        
        print(f"Saved verification log to: {log_file}")