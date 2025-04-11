# console.py
from .board import HexBoard
from .player import ManualPlayer, IAPlayer

def display_board(board):
    """
    Muestra el tablero en formato de tablero HEX. 
    Usa 'O' para las celdas vacías y aplica una indentación creciente por fila.
    """
    print("\nTablero actual:")
    for i, row in enumerate(board.board):
        # Para la primera fila, sin indent; para las demás, se incrementa la indentación
        indent = " " * (i + 1) if i > 0 else ""
        # Representa cada celda: 'O' si está vacía; de lo contrario, el valor (por ejemplo, 1 o 2)
        line = " ".join("O" if cell == 0 else str(cell) for cell in row)
        print(indent + line)

def start_game(board_size=7, player1=None, player2=None):
    """
    Inicia el juego en consola.
    """
    if player1 is None:
        player1 = ManualPlayer(1)
    if player2 is None:
        player2 = ManualPlayer(2)
        
    board = HexBoard(board_size)
    current_player = player1
    print("=== Comenzando el juego en consola ===")
    
    while True:
        display_board(board)
        
        moves = board.get_possible_moves()
        if not moves:
            print("¡Empate!")
            break
        
        move = current_player.play(board.board, moves)
        if board.place_piece(move[0], move[1], current_player.player_id):
            if board.check_connection(current_player.player_id):
                display_board(board)
                print(f"¡Gana el jugador {current_player.player_id}!")
                break
            # Alterna turno
            current_player = player2 if current_player == player1 else player1
        else:
            print("Movimiento inválido, intenta nuevamente.")

if __name__ == "__main__":
    start_game()
