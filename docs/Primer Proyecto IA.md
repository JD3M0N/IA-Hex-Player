# 🧠 Proyecto de Inteligencia Artificial: Jugador Autónomo para HEX 🎮

## 📜 Descripción del Juego HEX

**HEX** es un juego de estrategia para dos jugadores en un tablero hexagonal de tamaño \( N x N \).  

- **Objetivo**:
  - Jugador 1 (🔴): Conectar los lados izquierdo y derecho (horizontal)
  - Jugador 2 (🔵): Conectar los lados superior e inferior (vertical)
- **Reglas**:  
  1. Los jugadores alternan turnos para colocar su ficha en una casilla vacía.  
  2. El primer jugador en conectar sus lados **gana**.  
  3. Conexiones válidas en las 6 direcciones del hexágono.
- **Detalles de implementación**:
  1. El tablero se modela como una matrix de NxN:
  2. El primer jugador tiene `id = 1` y el segundo `id = 2`
  3. El sistema que se utiliza para modelación de adyacencias para cualquier sea i,j
direcciones = [
    (0, -1),   # Izquierda
    (0, 1),    # Derecha
    (-1, 0),   # Arriba
    (1, 0),    # Abajo
    (-1, 1),   # Arriba derecha
    (1, -1)    # Abajo izquierda
---

## 🛠️ Requerimientos del Proyecto

Desarrollar un jugador autónomo que herede de una clase base `Player` y **decida la mejor jugada** usando IA.

- **Heredar** de la clase base `Player`.  
- **Usar los parámetros de `play()` para decidir la jugada**:  
  - `board`: Matriz NxN que representa una copia del tablero actual (`0` = vacío, `1` = tú, `2` = oponente).  
  - `possible_moves`: Lista de tuplas `(fila, columna)` válidas.
  - `return`: Tupla (fila, columna) con la jugada seleccionada.

### 📋 Estructura de Clase Base (Proporcionada por Profesores)

```python
class Player:
    def __init__(self, player_id: int):
        self.player_id = player_id  # Tu identificador (1 o 2)

    def play(self, board: HexBoard) -> tuple:
        raise NotImplementedError("¡Implementa este método!")
```

```python
class HexBoard:
    def __init__(self, size: int):
        self.size = size  # Tamaño N del tablero (NxN)
        self.board = [[0 for _ in range(size)] for _ in range(size)]  # Matriz NxN (0=vacío, 1=Jugador1, 2=Jugador2)

	def clone(self) -> HexBoard:
		"""Devuelve una copia del tablero actual"""
		pass

    def place_piece(self, row: int, col: int, player_id: int) -> bool:
        """Coloca una ficha si la casilla está vacía."""
        pass

    def get_possible_moves(self) -> list:
        """Devuelve todas las casillas vacías como tuplas (fila, columna)."""
        pass
    
    def check_connection(self, player_id: int) -> bool:
        """Verifica si el jugador ha conectado sus dos lados"""
        pass
```

## 📌 Notas

#### **Entrega Individual**

- Código + Documentación (explicación de la estrategia).
- Se debe crear un issue en el repo general de los proyectos [Repo del primer proyecto de IA](https://github.com/matcom/ai) con la siguiente información:
	- Nombre y Apellidos, grupo y repo de github con la implementación (la implementación debe contener un archivo player.py que contenga el código de su jugador inteligente)

## 🏆 Competición de Jugadores HEX: Reglas y Estructura del Torneo

Los jugadores implementados se enfrentarán en un torneo automatizado con las siguientes reglas:

1. **Emparejamientos Aleatorios**

   - Cada jugador competirá contra **todos los demás** en partidas múltiples.  
   - El orden y los oponentes se asignarán aleatoriamente al inicio.  
2. **Partidas por Enfrentamiento**:  
   - Cada duelo constará de **N partidas** (ej: 10) para reducir el factor suerte.  
   - Los jugadores alternarán quién empieza primero en cada partida. 
   - **¡Cuidado con los tiempos!** Si tu algoritmo tarda mucho por jugada, será descalificado.

## Preparado para la batalla?? ¡Es hora de codear! 👨💻👩💻
