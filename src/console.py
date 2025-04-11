# console.py
from board import HexBoard
from player import ManualPlayer, IAPlayer

def start_game(board_size=7, player1=None, player2=None):
    """
    Función para iniciar el juego en consola.
    
    :param board_size: Tamaño del tablero (NxN).
    :param player1: Instancia del jugador 1 (por defecto ManualPlayer).
    :param player2: Instancia del jugador 2 (por defecto ManualPlayer).
    """
    if player1 is None:
        player1 = ManualPlayer(1)
    if player2 is None:
        player2 = ManualPlayer(2)
        
    board = HexBoard(board_size)
    current_player = player1
    print("=== Comenzando el juego en consola ===")
    
    while True:
        print("\nTablero actual:")
        for row in board.board:
            print(" ".join(str(cell) for cell in row))
            
        moves = board.get_possible_moves()
        if not moves:
            print("¡Empate!")
            break
        
        move = current_player.play(board.board, moves)
        if board.place_piece(move[0], move[1], current_player.player_id):
            if board.check_connection(current_player.player_id):
                print(f"¡Gana el jugador {current_player.player_id}!")
                break
            # Alterna turno
            current_player = player2 if current_player == player1 else player1
        else:
            print("Movimiento inválido, intenta nuevamente.")

if __name__ == "__main__":
    start_game()
