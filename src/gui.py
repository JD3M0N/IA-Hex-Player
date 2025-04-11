# gui.py
import tkinter as tk
from tkinter import messagebox, simpledialog
import math
from .board import HexBoard
from .player import ManualPlayer, IAPlayer

class HexGUI:
    def __init__(self, board_size, player1, player2, hex_size=30):
        """
        Inicializa la interfaz gráfica del juego.
        
        :param board_size: Tamaño del tablero NxN.
        :param player1: Instancia del jugador 1.
        :param player2: Instancia del jugador 2.
        :param hex_size: Tamaño del radio del hexágono.
        """
        self.board_size = board_size
        self.player1 = player1
        self.player2 = player2
        self.players = [player1, player2]
        self.current_turn = 0  # 0: turno de player1, 1: turno de player2
        self.hex_size = hex_size
        self.margin = 10
        self.board = HexBoard(board_size)
        
        self.window = tk.Tk()
        self.window.title("Juego HEX")
        # Calcular el tamaño del canvas en función del tamaño del tablero
        hex_width = math.sqrt(3) * hex_size
        hex_height = 2 * hex_size
        width = self.margin * 2 + board_size * hex_width + hex_width/2
        height = self.margin * 2 + board_size * (hex_height * 0.75) + hex_size
        self.canvas = tk.Canvas(self.window, width=width, height=height, bg="white")
        self.canvas.pack()
        
        # Diccionario para mapear los id de los hexágonos a su posición (fila, columna)
        self.hexagons = {}
        self.draw_board()
    
    def draw_board(self):
        """Dibuja el tablero, generando un hexágono para cada celda y coloreándolo según su estado."""
        self.canvas.delete("all")
        hex_size = self.hex_size
        hex_width = math.sqrt(3) * hex_size
        hex_height = 2 * hex_size
        
        for i in range(self.board_size):
            for j in range(self.board_size):
                # Usamos un desplazamiento en x para las filas pares (sistema even-r)
                if i % 2 == 0:
                    cx = self.margin + j * hex_width + hex_width/2
                else:
                    cx = self.margin + j * hex_width
                cy = self.margin + i * (hex_height * 0.75)
                vertices = self.calculate_hexagon(cx, cy, hex_size)
                
                # Determinar el color de la celda
                cell_value = self.board.board[i][j]
                if cell_value == 1:
                    fill_color = "red"
                elif cell_value == 2:
                    fill_color = "blue"
                else:
                    fill_color = "light grey"
                    
                # Crear el polígono y guardar el id junto con la posición
                hex_id = self.canvas.create_polygon(vertices, outline="black", fill=fill_color, width=2)
                self.hexagons[hex_id] = (i, j)
                self.canvas.tag_bind(hex_id, "<Button-1>", self.handle_click)
    
    def calculate_hexagon(self, cx, cy, size):
        """
        Calcula los vértices de un hexágono centrado en (cx, cy).
        
        :param cx: Coordenada x del centro.
        :param cy: Coordenada y del centro.
        :param size: Tamaño del radio.
        :return: Lista de coordenadas [x1, y1, x2, y2, ..., x6, y6].
        """
        points = []
        for k in range(6):
            angle_deg = 60 * k - 30  # Ajusta la orientación para que tenga la parte plana arriba
            angle_rad = math.radians(angle_deg)
            x = cx + size * math.cos(angle_rad)
            y = cy + size * math.sin(angle_rad)
            points.extend([x, y])
        return points

    def handle_click(self, event):
        """Callback que se ejecuta al hacer click en un hexágono."""
        clicked_items = self.canvas.find_withtag("current")
        if not clicked_items:
            return
        hex_id = clicked_items[0]
        if hex_id not in self.hexagons:
            return
        row, col = self.hexagons[hex_id]
        # Si la celda ya está ocupada, no se procesa nada
        if self.board.board[row][col] != 0:
            return
        
        current_player = self.players[self.current_turn]
        # Solo se permite el movimiento manual si el jugador es ManualPlayer
        if not isinstance(current_player, ManualPlayer):
            return
        
        if self.board.place_piece(row, col, current_player.player_id):
            self.draw_board()
            if self.board.check_connection(current_player.player_id):
                messagebox.showinfo("Fin del Juego", f"¡Gana el jugador {current_player.player_id}!")
                self.window.destroy()
                return
            self.current_turn = 1 - self.current_turn
            # Si el siguiente turno corresponde a un jugador IA, se programa su movimiento
            self.window.after(500, self.ia_move)
    
    def ia_move(self):
        """Ejecuta el movimiento del jugador IA (si es su turno)."""
        current_player = self.players[self.current_turn]
        if isinstance(current_player, ManualPlayer):
            return  # No se actúa si es turno manual
        
        moves = self.board.get_possible_moves()
        if not moves:
            messagebox.showinfo("Fin del Juego", "¡Empate!")
            self.window.destroy()
            return
        try:
            move = current_player.play(self.board.board, moves)
        except NotImplementedError:
            messagebox.showinfo("Información", "La IA aún no está implementada.")
            return
        
        if move not in moves:
            messagebox.showerror("Error", "La jugada de la IA no es válida.")
            return
        
        if self.board.place_piece(move[0], move[1], current_player.player_id):
            self.draw_board()
            if self.board.check_connection(current_player.player_id):
                messagebox.showinfo("Fin del Juego", f"¡Gana el jugador {current_player.player_id}!")
                self.window.destroy()
                return
            self.current_turn = 1 - self.current_turn
            # Si el siguiente turno también es IA, se programa la siguiente jugada
            if not isinstance(self.players[self.current_turn], ManualPlayer):
                self.window.after(500, self.ia_move)
    
    def start(self):
        """Inicia el mainloop de Tkinter."""
        self.window.mainloop()

def setup_game():
    """
    Muestra dos diálogos para solicitar el tamaño del tablero y la modalidad de juego.
    
    :return: Una tupla (board_size, mode) donde mode es 1, 2 o 3.
    """
    root = tk.Tk()
    root.withdraw()  # Oculta la ventana principal mientras se preguntan los parámetros
    board_size = simpledialog.askinteger(
        "Tamaño del tablero", 
        "Ingrese el tamaño del tablero (NxN):", 
        minvalue=3, 
        initialvalue=7
    )
    mode = simpledialog.askinteger(
        "Modo de juego", 
        "Seleccione el modo de juego:\n1. Jugador vs Jugador\n2. Jugador vs IA\n3. IA vs IA", 
        minvalue=1, 
        maxvalue=3, 
        initialvalue=1
    )
    root.destroy()
    return board_size, mode

def start_game():
    """
    Función pública para iniciar el juego gráfico.
    Solicita el tamaño del tablero y la modalidad de juego mediante diálogos,
    crea los jugadores correspondientes y arranca la interfaz gráfica.
    """
    board_size, mode = setup_game()
    
    if mode == 1:
        p1, p2 = ManualPlayer(1), ManualPlayer(2)
    elif mode == 2:
        p1, p2 = ManualPlayer(1), IAPlayer(2)
    elif mode == 3:
        p1, p2 = IAPlayer(1), IAPlayer(2)
    else:
        p1, p2 = ManualPlayer(1), ManualPlayer(2)
    
    gui_instance = HexGUI(board_size, p1, p2)
    gui_instance.start()

if __name__ == "__main__":
    start_game()
