# src/board.py

from typing import List, Tuple

class HexBoard:
    """
    Clase que representa el tablero del juego HEX.
    """

    def __init__(self, size: int):
        """
        Inicializa el tablero de tamaño NxN.
        :param size: Dimensión del tablero
        """
        self.size: int = size
        self.board: List[List[int]] = [[0 for _ in range(size)] for _ in range(size)]

    def print_board(self) -> None:
        """
        Imprime el tablero en consola con formato hexagonal.
        Las celdas vacías se muestran con ".", 
        el jugador 1 con "🔴" y el jugador 2 con "🔵".
        """
        for i in range(self.size):
            # Se añade espaciado para simular el efecto de tablero hexagonal.
            print(" " * i, end="")
            for j in range(self.size):
                cell = self.board[i][j]
                if cell == 0:
                    symbol = "."
                elif cell == 1:
                    symbol = "🔴"
                elif cell == 2:
                    symbol = "🔵"
                else:
                    symbol = "?"
                print(symbol, end=" ")
            print()  # Salto de línea

    def place_piece(self, row: int, col: int, player_id: int) -> bool:
        """
        Coloca la ficha del jugador en la posición indicada si la casilla está vacía.
        :param row: Fila donde colocar la ficha
        :param col: Columna donde colocar la ficha
        :param player_id: Identificador del jugador (1 o 2)
        :return: True si se coloca la ficha; False en otro caso.
        """
        if 0 <= row < self.size and 0 <= col < self.size:
            if self.board[row][col] == 0:
                self.board[row][col] = player_id
                return True
        return False

    def get_possible_moves(self) -> List[Tuple[int, int]]:
        """
        Retorna una lista de todas las posiciones vacías en el tablero.
        :return: Lista de tuplas (fila, columna)
        """
        moves = []
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == 0:
                    moves.append((i, j))
        return moves

    def get_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        """
        Retorna las celdas vecinas de (row, col) según el sistema "even-r" (filas pares/impares).
        :param row: Fila de la celda
        :param col: Columna de la celda
        :return: Lista de celdas vecinas válidas
        """
        neighbors = []
        if row % 2 == 0:  # Filas pares
            offsets = [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, 1), (1, 1)]
        else:  # Filas impares
            offsets = [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (1, -1)]
        for dr, dc in offsets:
            r, c = row + dr, col + dc
            if 0 <= r < self.size and 0 <= c < self.size:
                neighbors.append((r, c))
        return neighbors

    def check_connection(self, player_id: int) -> bool:
        """
        Verifica si el jugador ha conectado sus dos lados:
          - Jugador 1 (ID 1): conecta la columna 0 con la columna final.
          - Jugador 2 (ID 2): conecta la fila 0 con la última fila.
        Se utiliza una búsqueda en profundidad (DFS) para verificar la conexión.
        
        :param player_id: Identificador del jugador
        :return: True si el jugador gana, False de lo contrario.
        """
        visited = [[False] * self.size for _ in range(self.size)]
        stack = []
        
        if player_id == 1:
            # Para jugador 1, iniciamos en todas las celdas de la primera columna que tengan su ficha.
            for i in range(self.size):
                if self.board[i][0] == player_id:
                    stack.append((i, 0))
                    visited[i][0] = True
            target_col = self.size - 1
            while stack:
                r, c = stack.pop()
                if c == target_col:
                    return True
                for nr, nc in self.get_neighbors(r, c):
                    if not visited[nr][nc] and self.board[nr][nc] == player_id:
                        visited[nr][nc] = True
                        stack.append((nr, nc))
            return False

        elif player_id == 2:
            # Para jugador 2, iniciamos en todas las celdas de la primera fila con su ficha.
            for j in range(self.size):
                if self.board[0][j] == player_id:
                    stack.append((0, j))
                    visited[0][j] = True
            target_row = self.size - 1
            while stack:
                r, c = stack.pop()
                if r == target_row:
                    return True
                for nr, nc in self.get_neighbors(r, c):
                    if not visited[nr][nc] and self.board[nr][nc] == player_id:
                        visited[nr][nc] = True
                        stack.append((nr, nc))
            return False

        return False
