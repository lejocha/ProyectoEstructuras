# pedidos.py



"""
pedidos.py.

Se encarga de la aparición de los pedidos
en el mapa del juego.
"""

from collections import deque
from clases import Pedido
import random


def obtener_casillas_libres(mapa, ocupadas=None):
    """
    Retorna una lista de todas las casillas libres (no bloqueadas) del mapa.
    """
    if ocupadas is None:
        ocupadas = set()

    casillas_libres = []
    for y in range(len(mapa)):
        for x in range(len(mapa[0])):
            if mapa[y][x] != "B" and (x, y) not in ocupadas:
                casillas_libres.append((x, y))
    return casillas_libres


def asignar_posicion_aleatoria(mapa, ocupadas, separacion=4):
    """
    Asigna una posición aleatoria libre respetando la separación mínima.

    Returns:
        [x, y] si encuentra posición, None si no hay espacio
    """
    casillas_libres = obtener_casillas_libres(mapa, ocupadas)
    random.shuffle(casillas_libres)  # Mezclar para obtener posiciones aleatorias

    for nx, ny in casillas_libres:
        # Verificar si cumple separación
        libre = True
        for sx in range(-separacion, separacion + 1):
            for sy in range(-separacion, separacion + 1):
                tx, ty = nx + sx, ny + sy
                if 0 <= tx < len(mapa[0]) and 0 <= ty < len(mapa):
                    if (tx, ty) in ocupadas:
                        libre = False
                        break
            if not libre:
                break

        if libre:
            ocupadas.add((nx, ny))
            return [nx, ny]

    return None


def reubicar_pedidos(pedidos, mapa, ocupadas=None, separacion=4):
    """Reubica los pedidos.

        Al hacerlo evita casillas bloqueadas u ocupadas,
        con separación mínima de 4.

        Args:
            pedidos (list): Lista de dicts con claves "pickup" y "dropoff".
            mapa (list): Matriz del mapa.
            ocupadas (set): Conjunto de tuplas (x, y) de casillas ocupadas.
            separacion (int): Número mínimo de
            casillas alrededor que deben estar libres.
        """
    if ocupadas is None:
        ocupadas = set()

    for p in pedidos:
        for punto in ["pickup", "dropoff"]:
            x0, y0 = p[punto]

            # Si el punto está bloqueado o ocupado, buscamos un lugar libre
            if mapa[y0][x0] == "B" or (x0, y0) in ocupadas:
                visitados = set()
                cola = deque([(x0, y0)])
                encontrado = False
                intentos = 0
                max_intentos = len(mapa) * len(mapa[0])  # Evitar bucles infinitos

                while cola and not encontrado and intentos < max_intentos:
                    intentos += 1
                    x, y = cola.popleft()
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < len(mapa[0]) and 0 <= ny < len(mapa):
                            if (nx, ny) not in visitados:
                                visitados.add((nx, ny))

                                # Verificar si cumple separación
                                libre = mapa[ny][nx] != "B" and (nx, ny) not in ocupadas
                                if libre and separacion > 0:
                                    for sx in range(-separacion, separacion + 1):
                                        for sy in range(-separacion, separacion + 1):
                                            tx, ty = nx + sx, ny + sy
                                            if 0 <= tx < len(mapa[0]) and 0 <= ty < len(mapa):
                                                if (tx, ty) in ocupadas:
                                                    libre = False
                                                    break
                                        if not libre:
                                            break

                                if libre:
                                    p[punto] = [nx, ny]
                                    ocupadas.add((nx, ny))
                                    encontrado = True
                                    break
                                else:
                                    cola.append((nx, ny))

                # Si no se encontró lugar, al menos mover a una casilla no bloqueada cercana
                if not encontrado:
                    for dx in range(-3, 4):
                        for dy in range(-3, 4):
                            nx, ny = x0 + dx, y0 + dy
                            if 0 <= nx < len(mapa[0]) and 0 <= ny < len(mapa):
                                if mapa[ny][nx] != "B":
                                    p[punto] = [nx, ny]
                                    ocupadas.add((nx, ny))
                                    encontrado = True
                                    break
                        if encontrado:
                            break
            else:
                ocupadas.add((x0, y0))

def crear_objetos_pedidos(pedidos_data):
    """Crea y retorna los pedidos tomándolos de la API."""

    return [Pedido(p["pickup"], p["dropoff"], p.get("weight", 1), p.get("priority", 0), p.get("payout", 100)) for p in
            pedidos_data]

