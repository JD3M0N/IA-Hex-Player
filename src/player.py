class Player:
    def __init__(self, player_id: int):
        """
        Inicializa la clase base Player.
        
        :param player_id: Identificador del jugador (1 o 2).
        """
        self.player_id = player_id

    def play(self, board, possible_moves) -> tuple:
        """
        Método abstracto que debe implementar cada jugador.
        
        :param board: Matriz NxN que representa el tablero actual.
        :param possible_moves: Lista de tuplas (fila, columna) con movimientos válidos.
        :return: Tupla (fila, columna) con la jugada seleccionada.
        """
        raise NotImplementedError("¡Implementa este método!")


class ManualPlayer(Player):
    def play(self, board, possible_moves) -> tuple:
        """
        Permite al usuario seleccionar manualmente la jugada.
        Muestra el tablero actual y la lista de movimientos posibles. 
        Se solicita ingresar la fila y la columna, validando la entrada.

        :param board: Matriz NxN que representa el tablero actual.
        :param possible_moves: Lista de jugadas válidas como tuplas (fila, columna).
        :return: Tupla (fila, columna) seleccionada manualmente.
        """
        print("\n--- Jugada Manual ---")
        print("Tablero actual:")
        for row in board:
            print(" ".join(str(cell) for cell in row))
        
        print("\nMovimientos posibles:", possible_moves)

        while True:
            try:
                row = int(input("Ingresa la fila de la jugada: "))
                col = int(input("Ingresa la columna de la jugada: "))
                if (row, col) in possible_moves:
                    return (row, col)
                else:
                    print("Movimiento no válido. Por favor, ingresa un movimiento de la lista.")
            except ValueError:
                print("Entrada inválida. Por favor, ingresa números enteros.")


class IAPlayer(Player):
    def play(self, board, possible_moves) -> tuple:
        """
        Este método está destinado a implementar la estrategia de IA para decidir la jugada.
        Por el momento, se lanza un error indicando que aún no está implementado.
        
        :param board: Matriz NxN que representa el tablero actual.
        :param possible_moves: Lista de jugadas válidas como tuplas (fila, columna).
        :return: Tupla (fila, columna) con la jugada seleccionada.
        """
        raise NotImplementedError("El jugador IA aún no está implementado.")
