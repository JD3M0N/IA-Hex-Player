# src/player.py

from typing import Tuple
from .board import HexBoard

class Player:
    """
    Clase base para un jugador.
    """

    def __init__(self, player_id: int):
        self.player_id = player_id

    def play(self, board: HexBoard) -> Tuple[int, int]:
        """
        Método abstracto a implementar en subclases.
        """
        raise NotImplementedError("¡Implementa este método!")


class ManualPlayer(Player):
    """
    Jugador manual que solicita la jugada al usuario mediante la entrada por consola.
    """

    def play(self, board: HexBoard) -> Tuple[int, int]:
        while True:
            try:
                entrada = input(f"Jugador {self.player_id}, ingresa tu jugada (fila,columna): ")
                # Se elimina espacios y se separa por coma.
                row_str, col_str = entrada.replace(" ", "").split(",")
                row, col = int(row_str), int(col_str)
                if (row, col) in board.get_possible_moves():
                    return (row, col)
                else:
                    print("Movimiento inválido o casilla ocupada. Intenta de nuevo.")
            except Exception:
                print("Entrada no válida. Por favor, ingresa dos números separados por coma.")
