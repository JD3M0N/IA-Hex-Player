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


class MCTSNode:
    def __init__(self, board: HexBoard, parent, move: tuple, player_turn: int):
        """
        :param board: Estado del tablero en este nodo.
        :param parent: Nodo padre.
        :param move: Movimiento que llevó a este nodo (None para la raíz).
        :param player_turn: El jugador que tiene el turno en este nodo.
        """
        self.board = board
        self.parent = parent
        self.move = move
        self.player_turn = player_turn  # Quién mueve en este nodo
        self.children = []
        self.untried_moves = board.get_possible_moves()  # Movimientos aún no explorados
        self.visits = 0
        self.wins = 0.0

    def is_terminal(self):
        # Un nodo es terminal si algún jugador ha ganado o no hay más movimientos.
        return self.board.check_connection(1) or self.board.check_connection(2) or (len(self.untried_moves) == 0)

    def is_fully_expanded(self):
        return len(self.untried_moves) == 0

    def add_child(self, child_node):
        self.children.append(child_node)
        if child_node.move in self.untried_moves:
            self.untried_moves.remove(child_node.move)

    def best_child(self, c_param):
        best_score = float('-inf')
        best_node = None
        for child in self.children:
            # Si el hijo no ha sido visitado, le damos prioridad
            if child.visits == 0:
                score = float('inf')
            else:
                # Puntuación UCT: media de victorias + bonus de exploración
                score = (child.wins / child.visits) + c_param * math.sqrt(math.log(self.visits) / child.visits)
            if score > best_score:
                best_score = score
                best_node = child
        return best_node

    def __repr__(self):
        return f"MCTSNode(move={self.move}, visits={self.visits}, wins={self.wins}, untried_moves={len(self.untried_moves)})"


class IAPlayer(Player):
    def __init__(self, player_id: int, time_limit: float = 1.0, c_param: float = 1.4, parallel_rollouts: bool = True, num_threads: int = 4):
        """
        :param player_id: Identificador del jugador (1 o 2).
        :param time_limit: Tiempo (en segundos) asignado a la búsqueda MCTS.
        :param c_param: Constante de exploración en la fórmula UCT.
        :param parallel_rollouts: Si True, se ejecutarán rollouts en paralelo.
        :param num_threads: Número de hilos a usar en paralelización.
        """
        super().__init__(player_id)
        self.time_limit = time_limit
        self.c_param = c_param
        self.parallel_rollouts = parallel_rollouts
        self.num_threads = num_threads
        self.opponent_id = 3 - player_id
        self.root = None  # Raíz del árbol MCTS

    def play(self, board: HexBoard, possible_moves) -> tuple:
        # Reutiliza el árbol si es posible
        if self.root is not None:
            self.root = self._reuse_tree(self.root, board)
        else:
            self.root = MCTSNode(board=board.clone(), parent=None, move=None, player_turn=self.player_id)

        end_time = time.time() + self.time_limit

        if self.parallel_rollouts:
            with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
                futures = []
                while time.time() < end_time:
                    node = self._tree_policy(self.root)
                    futures.append(executor.submit(self._default_policy, node))
                    if len(futures) >= self.num_threads:
                        for future in as_completed(futures):
                            result = future.result()
                            self._backup(node, result)
                        futures = []
                for future in as_completed(futures):
                    result = future.result()
                    self._backup(node, result)
        else:
            while time.time() < end_time:
                node = self._tree_policy(self.root)
                result = self._default_policy(node)
                self._backup(node, result)

        if self.root.children:
            best_child = max(self.root.children, key=lambda child: child.visits)
        else:
            best_child = None

        if best_child is None:
            # Por seguridad, si no hay nodos hijos, se elige un movimiento aleatorio
            return random.choice(possible_moves)

        # Se actualiza la raíz para el siguiente turno
        self.root = best_child
        self.root.parent = None
        return best_child.move

    def _tree_policy(self, node: MCTSNode) -> MCTSNode:
        """
        Recorre el árbol usando la estrategia UCT hasta llegar a un nodo que no esté completamente expandido
        o a uno terminal.
        """
        while not node.is_terminal():
            if not node.is_fully_expanded():
                return self._expand(node)
            else:
                node = node.best_child(self.c_param)
        return node

    def _expand(self, node: MCTSNode) -> MCTSNode:
        """
        Expande el nodo probando uno de los movimientos no explorados.
        """
        move = random.choice(node.untried_moves)
        new_board = node.board.clone()
        new_board.place_piece(move[0], move[1], node.player_turn)
        next_player = 3 - node.player_turn
        child = MCTSNode(board=new_board, parent=node, move=move, player_turn=next_player)
        node.add_child(child)
        return child

    def _default_policy(self, node: MCTSNode) -> int:
        """
        Simulación (rollout) desde el nodo dado. Se juega de forma aleatoria hasta terminar el juego.
        Retorna 1 si gana la IA, -1 si gana el oponente, o 0 en caso de empate.
        """
        board_clone = node.board.clone()
        current_player = node.player_turn
        while True:
            if board_clone.check_connection(self.player_id):
                return 1
            if board_clone.check_connection(self.opponent_id):
                return -1
            moves = board_clone.get_possible_moves()
            if not moves:
                return 0
            move = random.choice(moves)
            board_clone.place_piece(move[0], move[1], current_player)
            current_player = 3 - current_player

    def _backup(self, node: MCTSNode, result: int):
        """
        Retropropagación de la simulación: se actualizan visitas y victorias en cada nodo hasta la raíz.
        Se invierte el resultado en cada nivel (operador de min-max típico en MCTS).
        """
        while node is not None:
            node.visits += 1
            node.wins += result
            result = -result
            node = node.parent

    def _reuse_tree(self, old_root: MCTSNode, current_board: HexBoard) -> MCTSNode:
        """
        Intenta encontrar en los hijos del nodo raíz uno que corresponda al estado actual.
        Si no se encuentra, se crea un nuevo nodo raíz.
        """
        for child in old_root.children:
            if child.board.board == current_board.board:
                return child
        return MCTSNode(board=current_board.clone(), parent=None, move=None, player_turn=self.player_id)


class IAPlayer3(Player):
    def __init__(self, player_id: int, time_limit: float = 0.9, c_param: float = 1.4):
        super().__init__(player_id)
        self.time_limit = time_limit
        self.c_param = c_param  # Constante de exploración configurable
        self.opponent_id = 3 - player_id
        self.mcts_root = None  # Para persistir el árbol entre turnos

    def play(self, board: HexBoard, possible_moves) -> tuple:
        # Para integrar el tree reuse, actualiza el árbol si existe una raíz previa
        if self.mcts_root is not None:
            # Intenta encontrar el subárbol correspondiente al último movimiento del oponente,
            # de lo contrario se reinicia el árbol.
            self.mcts_root = self._reuse_tree(self.mcts_root, board)
        else:
            self.mcts_root = MCTSNode(board=board.clone(), parent=None, move=None, player_id=self.player_id)

        end_time = time.time() + self.time_limit
        # Ejecutar simulaciones desde la raíz hasta que se agote el tiempo:
        while time.time() < end_time:
            node = self._mcts_select(self.mcts_root)
            if not node.is_terminal() and not node.is_fully_expanded():
                node = self._mcts_expand(node)
            result = self._mcts_simulate(node)
            self._mcts_backpropagate(node, result)

        # Seleccionar la mejor jugada basada en el número de visitas
        best_child = max(self.mcts_root.children, key=lambda child: child.visits)
        # Actualizar la raíz para el próximo turno:
        self.mcts_root = best_child
        self.mcts_root.parent = None
        return best_child.move

    def _best_uct_child(self, node):
        best_score = float('-inf')
        best_child = None
        for child in node.children:
            if child.visits == 0:
                score = float('inf')
            else:
                exploit = child.wins / child.visits
                explore = math.sqrt(math.log(node.visits) / child.visits)
                score = exploit + self.c_param * explore
            if score > best_score:
                best_score = score
                best_child = child
        return best_child

    # ... (mantén o ajusta los métodos _mcts_select, _mcts_expand, _mcts_simulate y _mcts_backpropagate)
    
    def _mcts_select(self, node):
        while not node.is_terminal() and node.is_fully_expanded():
            node = self._best_uct_child(node)
        return node
    
    def _mcts_expand(self, node):
        moves = node.board.get_possible_moves()
        for move in moves:
            if move not in node.tried_moves:
                new_board = node.board.clone()
                player_to_move = node.player_id if node.move is None else (3 - node.player_id)
                new_board.place_piece(move[0], move[1], player_to_move)
                
                child = MCTSNode(
                    board=new_board,
                    parent=node,
                    move=move,
                    player_id=3 - player_to_move
                )
                node.add_child(child, move)
                return child
        return node
    
    def _mcts_simulate(self, node):
        current_board = node.board.clone()
        current_player = node.player_id
        
        while not current_board.check_connection(1) and not current_board.check_connection(2):
            possible_moves = current_board.get_possible_moves()
            if not possible_moves:
                break
            
            move = random.choice(possible_moves)
            current_board.place_piece(move[0], move[1], current_player)
            current_player = 3 - current_player
        
        if current_board.check_connection(self.player_id):
            return 1
        elif current_board.check_connection(self.opponent_id):
            return -1
        else:
            return 0
        
    def _mcts_backpropagate(self, node, result):
        while node is not None:
            node.visits += 1
            if node.player_id == self.player_id:
                node.wins += result
            else:
                node.wins -= result
            node = node.parent

    def _reuse_tree(self, old_root, current_board):
        # Este método busca en los hijos de old_root el nodo que coincide
        # con el estado actual (current_board). Si se encuentra, se retorna ese subárbol;
        # si no, se reinicia el árbol.
        for child in old_root.children:
            # Aquí puedes comparar de forma simple, por ejemplo, comparando la matriz del tablero:
            if child.board.board == current_board.board:
                return child
        return MCTSNode(board=current_board.clone(), parent=None, move=None, player_id=self.player_id)


class IAPlayer2(Player):
    def __init__(self, player_id: int, time_limit: float = 3.1, method: str = "mcts"):
        """
        Inicializa el jugador IA.
        
        :param player_id: Identificador del jugador (1 o 2)
        :param time_limit: Límite de tiempo en segundos para tomar una decisión
        :param method: Método a utilizar ("minimax", "mcts", "hybrid")
        """
        super().__init__(player_id)
        self.time_limit = time_limit
        self.method = method
        self.opponent_id = 3 - player_id
        
    def play(self, board, possible_moves) -> tuple:
        """
        Decide la mejor jugada según el método seleccionado.
        
        :param board: Tablero actual
        :param possible_moves: Lista de movimientos posibles
        :return: Jugada seleccionada como tupla (fila, columna)
        """
        if not possible_moves:
            return None
            
        # Si solo hay un movimiento posible, hacerlo directamente
        if len(possible_moves) == 1:
            return possible_moves[0]
            
        # Aplicar apertura si el tablero está casi vacío (primeros movimientos)
        if self._is_opening_phase(board):
            return self._play_opening(board, possible_moves)
            
        # Seleccionar método según el tamaño del tablero y fase del juego
        selected_method = self._select_method(board)
        
        # Ejecutar el método seleccionado con límite de tiempo
        start_time = time.time()
        
        if selected_method == "minimax":
            depth = self._calculate_minimax_depth(board.size, len(possible_moves))
            move = self._minimax_play(board, possible_moves, depth)
        elif selected_method == "mcts":
            move = self._mcts_play(board, possible_moves, self.time_limit * 0.95)
        else:  # hybrid
            move = self._hybrid_play(board, possible_moves, self.time_limit * 0.95)
            
        # Verificar tiempo restante y hacer ajustes si es necesario
        elapsed_time = time.time() - start_time
        if elapsed_time > self.time_limit:
            print(f"¡Advertencia! El método {selected_method} excedió el límite de tiempo: {elapsed_time:.4f}s")
            
        return move
    
    def _is_opening_phase(self, board):
        """Determina si estamos en la fase de apertura (primeros movimientos)"""
        piece_count = sum(row.count(1) + row.count(2) for row in board.board)
        return piece_count < 4
    
    def _play_opening(self, board, possible_moves):
        """Estrategia de apertura para los primeros movimientos"""
        size = board.size
        
        # Primera jugada: centro o cerca del centro
        if sum(row.count(1) + row.count(2) for row in board.board) == 0:
            center = size // 2
            if (center, center) in possible_moves:
                return (center, center)
                
        # Respuesta a la primera jugada: jugada espejo
        if self.player_id == 2 and sum(row.count(1) + row.count(2) for row in board.board) == 1:
            for i in range(size):
                for j in range(size):
                    if board.board[i][j] == 1:  # Encontrar jugada del oponente
                        # Jugada espejo (en Hex, la jugada espejo es simétrica respecto al eje)
                        mirror_move = (j, i)
                        if mirror_move in possible_moves:
                            return mirror_move
        
        # Por defecto, usar MCTS con poco tiempo
        return self._mcts_play(board, possible_moves, 0.1)
    
    def _select_method(self, board):
        """Selecciona el método según el estado del juego"""
        size = board.size
        piece_count = sum(row.count(1) + row.count(2) for row in board.board)
        empty_count = size * size - piece_count
        
        # Para tableros pequeños o etapas finales, Minimax puede ser mejor
        if size <= 7 or empty_count < 15:
            return "minimax"
        # Para tableros medianos o fases intermedias, usar método híbrido
        elif size <= 9 or empty_count < 30:
            return "hybrid"
        # Para tableros grandes o inicio de juego, MCTS es más adecuado
        else:
            return "mcts"
            
    def _calculate_minimax_depth(self, board_size, move_count):
        """Calcula la profundidad apropiada para Minimax según el tamaño del tablero"""
        if board_size <= 5:
            return 4
        elif board_size <= 7:
            return 3
        elif board_size <= 9:
            return 2
        else:
            return 1
    
    # === MINIMAX IMPLEMENTATION ===
    def _minimax_play(self, board, possible_moves, depth):
        """Implementación de Minimax con poda Alpha-Beta"""
        best_move = None
        best_value = float('-inf')
        alpha = float('-inf')
        beta = float('inf')
        
        # Paralelizar la evaluación de los movimientos principales
        with ThreadPoolExecutor() as executor:
            # Crear tareas para cada movimiento posible
            futures = []
            for move in possible_moves:
                futures.append(
                    executor.submit(
                        self._evaluate_move, board, move, depth, alpha, beta
                    )
                )
            
            # Recoger resultados y seleccionar el mejor
            for i, future in enumerate(futures):
                move, value = future.result()
                if value > best_value:
                    best_value = value
                    best_move = move
                alpha = max(alpha, best_value)
        
        return best_move
    
    def _evaluate_move(self, board, move, depth, alpha, beta):
        """Evalúa un movimiento usando Minimax"""
        new_board = board.clone()
        new_board.place_piece(move[0], move[1], self.player_id)
        
        value = self._min_value(new_board, depth - 1, alpha, beta)
        return move, value
    
    def _max_value(self, board, depth, alpha, beta):
        # Verificar si el jugador ha ganado
        if board.check_connection(self.player_id):
            return 1
        
        # Verificar si el oponente ha ganado
        if board.check_connection(self.opponent_id):
            return -1
            
        # Si alcanzamos la profundidad máxima o no hay movimientos posibles
        if depth == 0 or not board.get_possible_moves():
            return self._evaluate_board(board)
            
        value = float('-inf')
        for move in board.get_possible_moves():
            new_board = board.clone()
            new_board.place_piece(move[0], move[1], self.player_id)
            
            value = max(value, self._min_value(new_board, depth - 1, alpha, beta))
            
            if value >= beta:
                return value
                
            alpha = max(alpha, value)
            
        return value
    
    def _min_value(self, board, depth, alpha, beta):
        # Verificar si el jugador ha ganado
        if board.check_connection(self.player_id):
            return 1
        
        # Verificar si el oponente ha ganado
        if board.check_connection(self.opponent_id):
            return -1
            
        # Si alcanzamos la profundidad máxima o no hay movimientos posibles
        if depth == 0 or not board.get_possible_moves():
            return self._evaluate_board(board)
            
        value = float('inf')
        for move in board.get_possible_moves():
            new_board = board.clone()
            new_board.place_piece(move[0], move[1], self.opponent_id)
            
            value = min(value, self._max_value(new_board, depth - 1, alpha, beta))
            
            if value <= alpha:
                return value
                
            beta = min(beta, value)
            
        return value
    
    # === MCTS IMPLEMENTATION ===
    def _mcts_play(self, board, possible_moves, simulation_time):
        """Implementación de Monte Carlo Tree Search"""
        root = MCTSNode(board=board.clone(), parent=None, move=None, player_id=self.player_id)
        
        # Ejecutar simulaciones hasta que se agote el tiempo
        end_time = time.time() + simulation_time
        simulation_count = 0
        
        while time.time() < end_time:
            # Fase 1: Selección
            node = self._mcts_select(root)
            
            # Fase 2: Expansión
            if not node.is_terminal() and not node.is_fully_expanded():
                node = self._mcts_expand(node)
                
            # Fase 3: Simulación
            result = self._mcts_simulate(node)
            
            # Fase 4: Retropropagación
            self._mcts_backpropagate(node, result)
            
            simulation_count += 1
            
        # Seleccionar el mejor movimiento basado en la mayor cantidad de visitas
        best_child = max(root.children, key=lambda child: child.visits if child else 0)
        return best_child.move
    
    def _mcts_select(self, node):
        """Selecciona un nodo para expandir usando UCT"""
        while not node.is_terminal() and node.is_fully_expanded():
            node = self._best_uct_child(node)
        return node
    
    def _mcts_expand(self, node):
        """Expande el nodo añadiendo un hijo"""
        moves = node.board.get_possible_moves()
        for move in moves:
            if move not in node.tried_moves:
                new_board = node.board.clone()
                player_to_move = node.player_id if node.move is None else (3 - node.player_id)
                new_board.place_piece(move[0], move[1], player_to_move)
                
                child = MCTSNode(
                    board=new_board,
                    parent=node,
                    move=move,
                    player_id=3 - player_to_move
                )
                node.add_child(child, move)
                return child
        return node
    
    def _mcts_simulate(self, node):
        """Simula un juego desde el nodo actual hasta un estado terminal"""
        current_board = node.board.clone()
        current_player = node.player_id
        
        # Usar una política de simulación mejorada para Hex
        while not current_board.check_connection(1) and not current_board.check_connection(2):
            possible_moves = current_board.get_possible_moves()
            if not possible_moves:
                break
                
            # Política de simulación: 80% al azar, 20% movimientos que conectan piezas existentes
            if random.random() < 0.2:
                move = self._select_connecting_move(current_board, current_player, possible_moves)
                if move is None:
                    move = random.choice(possible_moves)
            else:
                move = random.choice(possible_moves)
                
            current_board.place_piece(move[0], move[1], current_player)
            current_player = 3 - current_player
        
        if current_board.check_connection(self.player_id):
            return 1
        elif current_board.check_connection(self.opponent_id):
            return -1
        else:
            return 0
    
    def _select_connecting_move(self, board, player_id, possible_moves):
        """Selecciona un movimiento que conecte con piezas existentes del mismo jugador"""
        connecting_moves = []
        
        for move in possible_moves:
            # Comprobar si el movimiento conecta con piezas existentes
            neighbors = board._get_neighbors(move[0], move[1])
            for nr, nc in neighbors:
                if board.board[nr][nc] == player_id:
                    connecting_moves.append(move)
                    break
        
        if connecting_moves:
            return random.choice(connecting_moves)
        return None
    
    def _mcts_backpropagate(self, node, result):
        """Retropropaga el resultado de la simulación"""
        while node is not None:
            node.visits += 1
            if node.player_id == self.player_id:
                node.wins += result
            else:
                node.wins -= result
            node = node.parent
    
    def _best_uct_child(self, node):
        """Selecciona el mejor hijo según la fórmula UCT"""
        c_param = 1.4  # Parámetro de exploración
        
        best_score = float('-inf')
        best_child = None
        
        for child in node.children:
            if child is None:
                continue
                
            if child.visits == 0:
                score = float('inf')
            else:
                exploit = child.wins / child.visits
                explore = math.sqrt(math.log(node.visits) / child.visits)
                score = exploit + c_param * explore
                
            if score > best_score:
                best_score = score
                best_child = child
                
        return best_child
    
    # === HYBRID IMPLEMENTATION ===
    def _hybrid_play(self, board, possible_moves, time_limit):
        """
        Método híbrido que combina MCTS con evaluación heurística
        """
        # Usar MCTS pero con simulaciones guiadas por heurísticas
        root = MCTSNode(board=board.clone(), parent=None, move=None, player_id=self.player_id)
        
        end_time = time.time() + time_limit
        while time.time() < end_time:
            # Selección y expansión similar a MCTS estándar
            node = self._mcts_select(root)
            
            if not node.is_terminal() and not node.is_fully_expanded():
                node = self._mcts_expand(node)
                
            # Simulación mejorada con heurísticas
            result = self._hybrid_simulate(node)
            
            # Retropropagación estándar
            self._mcts_backpropagate(node, result)
            
        # Seleccionar mejor movimiento
        best_child = max(root.children, key=lambda child: child.visits if child else 0)
        return best_child.move
    
    def _hybrid_simulate(self, node):
        """Simulación con heurísticas para el método híbrido"""
        current_board = node.board.clone()
        current_player = node.player_id
        depth = 0
        max_depth = 50  # Evitar simulaciones infinitas
        
        # Fase 1: Primeros movimientos parcialmente aleatorios con guía heurística
        while depth < 10 and not current_board.check_connection(1) and not current_board.check_connection(2):
            possible_moves = current_board.get_possible_moves()
            if not possible_moves:
                break
                
            # Usar heurística para elegir movimientos prometedores
            if random.random() < 0.7:  # 70% de probabilidad de usar heurística
                move = self._select_heuristic_move(current_board, current_player, possible_moves)
            else:
                move = random.choice(possible_moves)
                
            current_board.place_piece(move[0], move[1], current_player)
            current_player = 3 - current_player
            depth += 1
        
        # Fase 2: Evaluación rápida si no hay ganador después de algunos movimientos
        if not current_board.check_connection(1) and not current_board.check_connection(2):
            return self._evaluate_board(current_board) * (1 if current_player == self.opponent_id else -1)
        
        # Si hay un ganador claro
        if current_board.check_connection(self.player_id):
            return 1
        elif current_board.check_connection(self.opponent_id):
            return -1
        else:
            return 0
    
    def _select_heuristic_move(self, board, player_id, possible_moves):
        """Selecciona un movimiento usando heurísticas específicas de Hex"""
        # Evaluar cada movimiento posible
        move_scores = []
        
        for move in possible_moves:
            new_board = board.clone()
            new_board.place_piece(move[0], move[1], player_id)
            
            # Calcular puntuación heurística
            score = self._evaluate_move_heuristic(new_board, move, player_id)
            move_scores.append((move, score))
        
        # Ordenar por puntuación y agregar algo de aleatoriedad
        move_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Seleccionar entre los 3 mejores movimientos con preferencia a los mejores
        top_n = min(3, len(move_scores))
        weights = [3, 2, 1][:top_n]
        moves = [move for move, _ in move_scores[:top_n]]
        
        return random.choices(moves, weights=weights, k=1)[0]
    
    def _evaluate_move_heuristic(self, board, move, player_id):
        """Evalúa un movimiento específico usando heurísticas de Hex"""
        score = 0
        row, col = move
        
        # 1. Proximidad a los bordes relevantes
        if player_id == 1:  # Conecta arriba-abajo
            score += (10 - abs(col - board.size // 2)) / 10.0  # Favorecer el centro horizontalmente
        else:  # Conecta izquierda-derecha
            score += (10 - abs(row - board.size // 2)) / 10.0  # Favorecer el centro verticalmente
        
        # 2. Proximidad a piezas propias
        own_neighbors = 0
        for nr, nc in board._get_neighbors(row, col):
            if board.board[nr][nc] == player_id:
                own_neighbors += 1
        score += own_neighbors * 0.2
        
        # 3. Potencial de bloqueo al oponente
        opponent_id = 3 - player_id
        blocking_potential = 0
        for nr, nc in board._get_neighbors(row, col):
            if board.board[nr][nc] == opponent_id:
                blocking_potential += 1
        score += blocking_potential * 0.3
        
        # 4. Valor de conectividad (cuánto ayuda a formar un camino)
        temp_board = board.clone()
        # Este cálculo podría ser costoso, así que lo simplificamos
        score += self._evaluate_connectivity(temp_board, player_id) * 0.4
        
        return score
    
    def _evaluate_connectivity(self, board, player_id):
        """Evalúa la conectividad global para el jugador"""
        # Implementación simplificada
        # Una heurística real podría usar algoritmos de camino más sofisticados
        
        if player_id == 1:  # Arriba-abajo
            top_pieces = sum(1 for j in range(board.size) if board.board[0][j] == player_id)
            bottom_pieces = sum(1 for j in range(board.size) if board.board[board.size-1][j] == player_id)
            return (top_pieces + bottom_pieces) / (2 * board.size)
        else:  # Izquierda-derecha
            left_pieces = sum(1 for i in range(board.size) if board.board[i][0] == player_id)
            right_pieces = sum(1 for i in range(board.size) if board.board[i][board.size-1] == player_id)
            return (left_pieces + right_pieces) / (2 * board.size)
    
    def _evaluate_board(self, board):
        """
        Evalúa el estado actual del tablero para el jugador actual.
        Retorna un valor entre -1 y 1, donde valores positivos favorecen al jugador actual.
        """
        # Implementar varias heurísticas y combinarlas
        
        # 1. Verificar si algún jugador ha ganado
        if board.check_connection(self.player_id):
            return 1.0
        if board.check_connection(self.opponent_id):
            return -1.0
            
        # 2. Heurística de conectividad
        player_connected = self._count_connected_pieces(board, self.player_id)
        opponent_connected = self._count_connected_pieces(board, self.opponent_id)
        
        if player_connected + opponent_connected == 0:
            connectivity_score = 0
        else:
            connectivity_score = (player_connected - opponent_connected) / (player_connected + opponent_connected)
            
        # 3. Heurística de avance hacia objetivo
        progress_score = self._evaluate_progress(board)
        
        # 4. Heurística de control del centro
        center_score = self._evaluate_center_control(board)
        
        # Combinar heurísticas con diferentes pesos
        return 0.5 * connectivity_score + 0.3 * progress_score + 0.2 * center_score
    
    def _count_connected_pieces(self, board, player_id):
        """Cuenta las piezas conectadas del jugador"""
        visited = set()
        count = 0
        
        def dfs(row, col):
            nonlocal count
            visited.add((row, col))
            count += 1
            
            for nr, nc in board._get_neighbors(row, col):
                if (nr, nc) not in visited and board.board[nr][nc] == player_id:
                    dfs(nr, nc)
        
        # Iniciar DFS desde cada pieza no visitada
        for i in range(board.size):
            for j in range(board.size):
                if board.board[i][j] == player_id and (i, j) not in visited:
                    count = 0
                    dfs(i, j)
        
        return count
    
    def _evaluate_progress(self, board):
        """Evalúa el progreso hacia el objetivo"""
        if self.player_id == 1:  # Conectar arriba-abajo
            # Calcular distancia mínima entre piezas del jugador y bordes objetivo
            min_distance_top = float('inf')
            min_distance_bottom = float('inf')
            
            for j in range(board.size):
                # Buscar piezas propias en cada columna
                for i in range(board.size):
                    if board.board[i][j] == self.player_id:
                        min_distance_top = min(min_distance_top, i)
                        min_distance_bottom = min(min_distance_bottom, board.size - 1 - i)
                        break
            
            if min_distance_top == float('inf') or min_distance_bottom == float('inf'):
                return -0.5  # Penalización si no hay piezas cerca de algún borde
                
            # Normalizar y convertir a una puntuación donde más alto es mejor
            normalized_distance = (2 * board.size - min_distance_top - min_distance_bottom) / (2 * board.size)
            return normalized_distance
            
        else:  # Conectar izquierda-derecha
            min_distance_left = float('inf')
            min_distance_right = float('inf')
            
            for i in range(board.size):
                # Buscar piezas propias en cada fila
                for j in range(board.size):
                    if board.board[i][j] == self.player_id:
                        min_distance_left = min(min_distance_left, j)
                        min_distance_right = min(min_distance_right, board.size - 1 - j)
                        break
            
            if min_distance_left == float('inf') or min_distance_right == float('inf'):
                return -0.5
                
            normalized_distance = (2 * board.size - min_distance_left - min_distance_right) / (2 * board.size)
            return normalized_distance
    
    def _evaluate_center_control(self, board):
        """Evalúa el control del centro del tablero"""
        center = board.size // 2
        center_radius = board.size // 3
        
        player_center_pieces = 0
        opponent_center_pieces = 0
        total_center_cells = 0
        
        for i in range(board.size):
            for j in range(board.size):
                # Calcular distancia Manhattan al centro
                dist = abs(i - center) + abs(j - center)
                if dist <= center_radius:
                    total_center_cells += 1
                    if board.board[i][j] == self.player_id:
                        player_center_pieces += 1
                    elif board.board[i][j] == self.opponent_id:
                        opponent_center_pieces += 1
        
        if total_center_cells == 0:
            return 0
            
        player_center_ratio = player_center_pieces / total_center_cells
        opponent_center_ratio = opponent_center_pieces / total_center_cells
        
        return player_center_ratio - opponent_center_ratio

#Implementacion para IAPlayer2
# class MCTSNode:
#     def __init__(self, board, parent, move, player_id=None):
#         self.board = board
#         self.parent = parent
#         self.move = move  # El movimiento que llevó a este nodo
#         self.player_id = player_id  # ID del jugador que debe mover
#         self.children = []
#         self.tried_moves = set()
#         self.visits = 0
#         self.wins = 0
        
#     def add_child(self, child, move):
#         self.children.append(child)
#         self.tried_moves.add(move)
        
#     def is_terminal(self):
#         # Un nodo es terminal si el juego ha terminado
#         return (self.board.check_connection(1) or 
#                 self.board.check_connection(2) or 
#                 not self.board.get_possible_moves())
                
#     def is_fully_expanded(self):
#         possible_moves = self.board.get_possible_moves()
#         return len(self.tried_moves) == len(possible_moves)
