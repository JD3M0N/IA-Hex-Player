# src/game.py

from .board import HexBoard
from .player import ManualPlayer

def main():
    print("Bienvenido al juego de HEX")

    # Solicitar tamaño del tablero al usuario.
    while True:
        try:
            size = int(input("Ingresa el tamaño del tablero (N): "))
            if size < 2:
                print("El tamaño debe ser al menos 2.")
                continue
            break
        except ValueError:
            print("Por favor, ingresa un número válido.")

    board = HexBoard(size)

    # Crear jugadores manuales.
    player1 = ManualPlayer(1)
    player2 = ManualPlayer(2)
    current_player = player1

    move_counter = 0
    total_moves = size * size

    # Ciclo principal del juego.
    while move_counter < total_moves:
        board.print_board()
        print(f"Turno del jugador {current_player.player_id}")

        move = current_player.play(board)
        board.place_piece(move[0], move[1], current_player.player_id)
        move_counter += 1

        # Verificar si el jugador actual ha ganado.
        if board.check_connection(current_player.player_id):
            board.print_board()
            print(f"¡Felicidades! El jugador {current_player.player_id} ha ganado.")
            return

        # Alternar turno.
        current_player = player2 if current_player == player1 else player1

    board.print_board()
    print("Empate: el tablero está lleno sin un ganador.")

if __name__ == "__main__":
    main()
