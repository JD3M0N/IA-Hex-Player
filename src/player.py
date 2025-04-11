import numpy as np
import random
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from .board import HexBoard

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
    def __init__(self, player_id: int, time_limit: float = 2.0):
        """
        Inicializa el jugador inteligente con un límite de tiempo para la búsqueda MCTS.
        
        :param player_id: Identificador del jugador (1 o 2).
        :param time_limit: Tiempo (en segundos) asignado a la búsqueda MCTS por jugada.
        """
        super().__init__(player_id)
        self.time_limit = time_limit

    def play(self, board, possible_moves) -> tuple:
        """
        Determina la mejor jugada utilizando MCTS (Monte Carlo Tree Search).
        
        :param board: Matriz NxN actual (representa el estado del juego).
        :param possible_moves: Lista de movimientos posibles (no se utiliza directamente, pero se usa como respaldo).
        :return: Tupla (fila, columna) con la jugada seleccionada.
        """
        move = self.mcts(board, self.player_id, self.time_limit)
        return move

    def mcts(self, board, player, time_limit: float) -> tuple:
        """
        Ejecuta el algoritmo MCTS durante el tiempo especificado y retorna la mejor jugada encontrada.
        
        :param board: Estado actual del tablero.
        :param player: Identificador del jugador que realiza la búsqueda.
        :param time_limit: Tiempo máximo para la búsqueda en segundos.
        :return: La jugada (fila, columna) que maximiza las estadísticas.
        """
        root = self.MCTSNode(board.clone(), move=None, parent=None, player_turn=player)
        start_time = time.time()
        iterations = 0
        while time.time() - start_time < time_limit:
            # Selección y expansión
            leaf = self.tree_policy(root)
            # Simulación
            result = self.default_policy(leaf.board, leaf.player_turn)
            # Retropropagación
            self.backpropagate(leaf, result)
            iterations += 1

        # Selecciona la jugada que llevó al hijo con mayor número de visitas
        if root.children:
            best_child = max(root.children, key=lambda n: n.visits)
            return best_child.move
        else:
            # Si por alguna razón el árbol no tiene hijos, se escoge uno aleatoriamente.
            return random.choice(board.get_possible_moves())

    def tree_policy(self, node):
        """
        Recorre el árbol de búsqueda hasta encontrar un nodo no terminal con movimientos sin explorar.
        
        :param node: Nodo actual en el árbol MCTS.
        :return: Nodo hoja para expandir.
        """
        while not self.is_terminal(node):
            if node.untried_moves:
                return self.expand(node)
            else:
                node = self.best_child(node, c=1.41)  # Coeficiente de exploración
        return node

    def expand(self, node):
        """
        Expande el nodo actual probando uno de sus movimientos aún no explorados.
        
        :param node: Nodo a expandir.
        :return: Nodo hijo resultante de aplicar un movimiento.
        """
        move = node.untried_moves.pop(random.randrange(len(node.untried_moves)))
        new_board = node.board.clone()
        new_board.place_piece(move[0], move[1], node.player_turn)
        child_node = self.MCTSNode(new_board,
                                   move=move,
                                   parent=node,
                                   player_turn=(1 if node.player_turn == 2 else 2))
        node.children.append(child_node)
        return child_node

    def best_child(self, node, c):
        """
        Selecciona el hijo con el mayor valor UCB1.
        
        :param node: Nodo del cual se selecciona el mejor hijo.
        :param c: Constante de exploración.
        :return: Hijo seleccionado.
        """
        best = None
        best_value = -float('inf')
        for child in node.children:
            if child.visits == 0:
                ucb = float('inf')
            else:
                ucb = (child.wins / child.visits) + c * math.sqrt(math.log(node.visits) / child.visits)
            if ucb > best_value:
                best_value = ucb
                best = child
        return best

    def default_policy(self, board, player_turn):
        """
        Realiza una simulación aleatoria (playout) desde el estado actual hasta alcanzar un estado terminal.
        
        :param board: Estado actual del tablero.
        :param player_turn: Jugador que debe mover.
        :return: Identificador del jugador ganador.
        """
        simulation_board = board.clone()
        current_player = player_turn
        moves = simulation_board.get_possible_moves()
        
        # Verifica si el tablero ya muestra una conexión ganadora
        if simulation_board.check_connection(1):
            return 1
        if simulation_board.check_connection(2):
            return 2
        
        while moves:
            move = random.choice(moves)
            simulation_board.place_piece(move[0], move[1], current_player)
            # Si con esta jugada se cumple la condición de victoria, se retorna el ganador.
            if simulation_board.check_connection(current_player):
                return current_player
            current_player = 1 if current_player == 2 else 2
            moves = simulation_board.get_possible_moves()
        # En Hex siempre habrá un ganador (no hay empates)
        return current_player

    def backpropagate(self, node, result):
        """
        Retropropaga el resultado de la simulación actualizando estadísticas en cada nodo de la ruta.
        
        :param node: Nodo hoja en el que terminó la simulación.
        :param result: Identificador del jugador ganador.
        """
        while node is not None:
            node.visits += 1
            # Se acumula la victoria si el jugador en turno en el nodo ganó la simulación.
            if node.player_turn == result:
                node.wins += 1
            node = node.parent

    def is_terminal(self, node):
        """
        Verifica si el nodo actual representa un estado terminal del juego.
        
        :param node: Nodo a evaluar.
        :return: True si se ha alcanzado una posición final, False en caso contrario.
        """
        return (node.board.check_connection(1) or 
                node.board.check_connection(2) or 
                not node.board.get_possible_moves())

    class MCTSNode:
        def __init__(self, board, move, parent, player_turn):
            """
            Nodo del árbol MCTS.
            
            :param board: Estado del tablero asociado al nodo.
            :param move: Movimiento que llevó a este nodo.
            :param parent: Nodo padre en el árbol.
            :param player_turn: Jugador que debe mover en este nodo.
            """
            self.board = board
            self.move = move
            self.parent = parent
            self.player_turn = player_turn
            self.children = []
            self.wins = 0
            self.visits = 0
            self.untried_moves = board.get_possible_moves()
