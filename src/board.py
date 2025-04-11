class HexBoard:
    def __init__(self, size: int):
        """
        Inicializa el tablero NxN.
        :param size: Tamaño N del tablero.
        """
        self.size = size
        self.board = [[0 for _ in range(size)] for _ in range(size)]
    
    def clone(self) -> "HexBoard":
        """
        Retorna una copia profunda del tablero.
        :return: Una nueva instancia de HexBoard con el estado actual del tablero.
        """
        new_board = HexBoard(self.size)
        # Copia profunda de la matriz
        new_board.board = [row[:] for row in self.board]
        return new_board

    def place_piece(self, row: int, col: int, player_id: int) -> bool:
        """
        Coloca una ficha en la posición (row, col) si la casilla está vacía.
        :param row: Índice de la fila.
        :param col: Índice de la columna.
        :param player_id: Identificador del jugador (1 o 2).
        :return: True si la jugada es válida y se realizó la colocación, False de lo contrario.
        """
        if self.board[row][col] != 0:
            return False
        self.board[row][col] = player_id
        return True

    def get_possible_moves(self) -> list:
        """
        Obtiene la lista de movimientos válidos (casillas vacías).
        :return: Lista de tuplas (fila, columna) de casillas vacías.
        """
        moves = []
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == 0:
                    moves.append((i, j))
        return moves

    def _get_neighbors(self, row: int, col: int) -> list:
            """
            Devuelve la lista de vecinos utilizando las siguientes direcciones para cualquier (i, j):
            - (0, -1)   → Izquierda
            - (0, 1)    → Derecha
            - (-1, 0)   → Arriba
            - (1, 0)    → Abajo
            - (-1, 1)   → Arriba derecha
            - (1, -1)   → Abajo izquierda
            """
            directions = [
                (0, -1),   # Izquierda
                (0, 1),    # Derecha
                (-1, 0),   # Arriba
                (1, 0),    # Abajo
                (-1, 1),   # Arriba derecha
                (1, -1)    # Abajo izquierda
            ]
            neighbors = []
            for dr, dc in directions:
                r, c = row + dr, col + dc
                if 0 <= r < self.size and 0 <= c < self.size:
                    neighbors.append((r, c))
            return neighbors

    def check_connection(self, player_id: int) -> bool:
        """
        Verifica si el jugador con `player_id` ha conectado sus dos lados.
          - Jugador 1 (id = 1): Conecta columna 0 con columna N-1.
          - Jugador 2 (id = 2): Conecta fila 0 con fila N-1.
        Se utiliza una búsqueda en profundidad (DFS) para explorar el tablero.
        
        :param player_id: Identificador del jugador (1 o 2).
        :return: True si se encuentra una conexión válida, False de lo contrario.
        """
        visited = set()
        stack = []

        if player_id == 1:
            # Inicia desde todas las celdas de la columna izquierda con ficha del jugador 1.
            for i in range(self.size):
                if self.board[i][0] == 1:
                    stack.append((i, 0))
                    visited.add((i, 0))
            # Condición de victoria: llegar a la columna derecha.
            target_condition = lambda pos: pos[1] == self.size - 1

        elif player_id == 2:
            # Inicia desde todas las celdas de la fila superior con ficha del jugador 2.
            for j in range(self.size):
                if self.board[0][j] == 2:
                    stack.append((0, j))
                    visited.add((0, j))
            # Condición de victoria: llegar a la fila inferior.
            target_condition = lambda pos: pos[0] == self.size - 1

        else:
            # Si el player_id no es 1 o 2, retorna False.
            return False

        # Búsqueda en profundidad (DFS)
        while stack:
            current = stack.pop()
            if target_condition(current):
                return True
            for neighbor in self._get_neighbors(current[0], current[1]):
                if neighbor not in visited and self.board[neighbor[0]][neighbor[1]] == player_id:
                    visited.add(neighbor)
                    stack.append(neighbor)
        return False
