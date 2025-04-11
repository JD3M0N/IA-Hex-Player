import tkinter as tk
from tkinter import messagebox, simpledialog
import math
from .board import HexBoard
from .player import ManualPlayer, IAPlayer

def point_in_polygon(x, y, poly):
    """
    Comprueba si el punto (x,y) está dentro del polígono definido por la lista de pares (x, y).
    Se utiliza el algoritmo de ray-casting.
    """
    inside = False
    n = len(poly)
    p1x, p1y = poly[0]
    for i in range(1, n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    else:
                        xints = p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

class HexGUI:
    def __init__(self, board_size, player1, player2):
        """
        Inicializa la interfaz gráfica del juego, mostrando el tablero como una
        disposición escalonada de hexágonos.
        
        :param board_size: Tamaño del tablero NxN.
        :param player1: Instancia del jugador 1.
        :param player2: Instancia del jugador 2.
        """
        self.board_size = board_size
        self.player1 = player1
        self.player2 = player2
        self.players = [player1, player2]
        self.current_turn = 0
        
        # Parámetros para el dibujo:
        self.margin = 20
        self.cell_size = 60      # Tamaño "diámetro" de la celda
        self.gap = 5             # Espacio entre celdas
        self.indent_per_row = 30 # Desplazamiento horizontal adicional por fila
        
        # Calcular dimensiones aproximadas del canvas:
        canvas_width = self.margin * 2 + board_size * (self.cell_size + self.gap) + (board_size - 1) * self.indent_per_row
        canvas_height = self.margin * 2 + board_size * (self.cell_size + self.gap)
        
        self.window = tk.Tk()
        self.window.title("Juego HEX")
        self.canvas = tk.Canvas(self.window, width=canvas_width, height=canvas_height, bg="white")
        self.canvas.pack()
        
        self.board = HexBoard(board_size)
        # Diccionarios para almacenar los objetos y la geometría de cada celda:
        self.cell_items = {}       # mapping: id del objeto en canvas -> (i, j)
        self.cell_polygons = {}    # mapping: (i, j) -> lista de pares (x,y) con las coordenadas del hexágono
        
        self.draw_board()
        # Asocia el clic en el canvas al manejador general
        self.canvas.bind("<Button-1>", self.handle_click)
    
    def calculate_hexagon(self, cx, cy, radius):
        """
        Calcula los vértices de un hexágono regular centrado en (cx, cy) usando el radio indicado.
        
        :param cx: Coordenada x del centro.
        :param cy: Coordenada y del centro.
        :param radius: Radio del hexágono.
        :return: Lista plana de coordenadas [x1, y1, x2, y2, ..., x6, y6].
        """
        points = []
        for k in range(6):
            angle_deg = 60 * k - 30  # Orientación: lado superior plano
            angle_rad = math.radians(angle_deg)
            x = cx + radius * math.cos(angle_rad)
            y = cy + radius * math.sin(angle_rad)
            points.extend([x, y])
        return points

    def draw_board(self):
        """Dibuja el tablero como una matriz escalonada de hexágonos."""
        self.canvas.delete("all")
        self.cell_items.clear()
        self.cell_polygons.clear()
        
        for i in range(self.board_size):
            indent = i * self.indent_per_row  # Desplazamiento horizontal incremental
            for j in range(self.board_size):
                # Calcular el centro de la celda (i, j)
                radius = self.cell_size / 2
                cx = self.margin + indent + j * (self.cell_size + self.gap) + radius
                cy = self.margin + i * (self.cell_size + self.gap) + radius
                
                # Calcular los vértices del hexágono (forma plana necesaria para draw_polygon)
                poly_flat = self.calculate_hexagon(cx, cy, radius)
                # Convertir la lista plana a lista de pares (para el test de contención)
                poly_pairs = [(poly_flat[k], poly_flat[k+1]) for k in range(0, len(poly_flat), 2)]
                
                # Definir el color y la etiqueta según el estado de la celda:
                cell_value = self.board.board[i][j]
                if cell_value == 0:
                    fill_color = "light grey"
                    text_val = "O"
                elif cell_value == 1:
                    fill_color = "red"
                    text_val = "1"
                elif cell_value == 2:
                    fill_color = "blue"
                    text_val = "2"
                else:
                    fill_color = "white"
                    text_val = ""
                
                # Dibujar el polígono (hexágono)
                poly_id = self.canvas.create_polygon(poly_flat, outline="black", fill=fill_color, width=2)
                # Guardar el id y la geometría del hexágono
                self.cell_items[poly_id] = (i, j)
                self.cell_polygons[(i, j)] = poly_pairs
                # Dibujar el texto centrado en la celda
                self.canvas.create_text(cx, cy, text=text_val, font=("Arial", 14, "bold"))
    
    def handle_click(self, event):
        """
        Maneja el clic en el canvas. Se recorre cada hexágono y se comprueba
        si el clic (event.x, event.y) se encuentra dentro de sus límites.
        """
        clicked_cell = None
        for (i, j), poly in self.cell_polygons.items():
            if point_in_polygon(event.x, event.y, poly):
                clicked_cell = (i, j)
                break
        if clicked_cell is None:
            # No se encontró ninguna celda bajo el clic
            return
        i, j = clicked_cell
        if self.board.board[i][j] != 0:
            return  # La celda ya está ocupada
        
        current_player = self.players[self.current_turn]
        if not isinstance(current_player, ManualPlayer):
            return
        
        if self.board.place_piece(i, j, current_player.player_id):
            self.draw_board()
            if self.board.check_connection(current_player.player_id):
                messagebox.showinfo("Fin del Juego", f"¡Gana el jugador {current_player.player_id}!")
                self.window.destroy()
                return
            self.current_turn = 1 - self.current_turn
            self.window.after(500, self.ia_move)
    
    def ia_move(self):
        """Ejecuta el movimiento del jugador IA (si es el turno de la IA)."""
        current_player = self.players[self.current_turn]
        if isinstance(current_player, ManualPlayer):
            return
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
            if not isinstance(self.players[self.current_turn], ManualPlayer):
                self.window.after(500, self.ia_move)
    
    def start(self):
        self.window.mainloop()

def setup_game():
    """Solicita al usuario el tamaño del tablero y la modalidad mediante diálogos."""
    root = tk.Tk()
    root.withdraw()
    board_size = simpledialog.askinteger("Tamaño del tablero",
                                          "Ingrese el tamaño del tablero (NxN):",
                                          minvalue=3,
                                          initialvalue=7)
    mode = simpledialog.askinteger("Modo de juego",
                                   "Seleccione el modo de juego:\n1. Jugador vs Jugador\n2. Jugador vs IA\n3. IA vs IA",
                                   minvalue=1,
                                   maxvalue=3,
                                   initialvalue=1)
    root.destroy()
    return board_size, mode

def start_game():
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
