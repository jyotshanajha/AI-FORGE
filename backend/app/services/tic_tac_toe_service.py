from dataclasses import dataclass


WINNING_LINES: tuple[tuple[int, int, int], ...] = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


@dataclass
class TicTacToeState:
    board: list[str]
    ai_move: int | None
    winner: str | None
    status: str
    next_turn: str | None


class TicTacToeService:
    @staticmethod
    def _validate_board(board: list[str]) -> list[str]:
        if len(board) != 9:
            raise ValueError("Board must contain exactly 9 cells.")

        normalized = [cell.strip().upper() if isinstance(cell, str) else "" for cell in board]
        for cell in normalized:
            if cell not in {"", "X", "O"}:
                raise ValueError("Board values must be X, O, or empty string.")

        return normalized

    @staticmethod
    def _winner(board: list[str]) -> str | None:
        for a, b, c in WINNING_LINES:
            if board[a] and board[a] == board[b] == board[c]:
                return board[a]
        return None

    @staticmethod
    def _is_draw(board: list[str]) -> bool:
        return all(cell in {"X", "O"} for cell in board) and TicTacToeService._winner(board) is None

    @staticmethod
    def _minimax(board: list[str], ai_symbol: str, human_symbol: str, maximizing: bool) -> tuple[int, int | None]:
        winner = TicTacToeService._winner(board)
        if winner == ai_symbol:
            return 10, None
        if winner == human_symbol:
            return -10, None
        if TicTacToeService._is_draw(board):
            return 0, None

        best_score = -10_000 if maximizing else 10_000
        best_move: int | None = None

        for idx, cell in enumerate(board):
            if cell:
                continue

            board[idx] = ai_symbol if maximizing else human_symbol
            score, _ = TicTacToeService._minimax(board, ai_symbol, human_symbol, not maximizing)
            board[idx] = ""

            # Prefer faster wins and slower losses.
            adjusted = score - 1 if maximizing else score + 1

            if maximizing and adjusted > best_score:
                best_score = adjusted
                best_move = idx
            if not maximizing and adjusted < best_score:
                best_score = adjusted
                best_move = idx

        return best_score, best_move

    @staticmethod
    def play_turn(board: list[str], player_move: int, player_symbol: str = "X") -> TicTacToeState:
        normalized = TicTacToeService._validate_board(board)

        player = player_symbol.upper()
        if player not in {"X", "O"}:
            raise ValueError("Player symbol must be X or O.")

        ai = "O" if player == "X" else "X"

        if normalized[player_move]:
            raise ValueError("That cell is already occupied.")

        normalized[player_move] = player
        winner = TicTacToeService._winner(normalized)
        if winner:
            return TicTacToeState(board=normalized, ai_move=None, winner=winner, status="finished", next_turn=None)
        if TicTacToeService._is_draw(normalized):
            return TicTacToeState(board=normalized, ai_move=None, winner=None, status="draw", next_turn=None)

        _, ai_move = TicTacToeService._minimax(normalized, ai, player, maximizing=True)
        if ai_move is None:
            return TicTacToeState(board=normalized, ai_move=None, winner=None, status="draw", next_turn=None)

        normalized[ai_move] = ai
        winner = TicTacToeService._winner(normalized)
        if winner:
            return TicTacToeState(board=normalized, ai_move=ai_move, winner=winner, status="finished", next_turn=None)
        if TicTacToeService._is_draw(normalized):
            return TicTacToeState(board=normalized, ai_move=ai_move, winner=None, status="draw", next_turn=None)

        return TicTacToeState(board=normalized, ai_move=ai_move, winner=None, status="in_progress", next_turn=player)
