"""
pedidos.py.

Se encarga de la aparición de los pedidos
en el mapa del juego.
"""

from clases import Pedido
from collections import deque


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

            # Si el punto está bloqueado o ya ocupado, buscar nuevo lugar.
            if mapa[y0][x0] == "B" or (x0, y0) in ocupadas:
                visitados = set()
                cola = deque([(x0, y0)])
                encontrado = False

                while cola and not encontrado:
                    x, y = cola.popleft()

                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy

                        if 0 <= nx < len(mapa[0]) and 0 <= ny < len(mapa):
                            if (nx, ny) in visitados:
                                continue

                            visitados.add((nx, ny))
                            libre = mapa[ny][nx] != "B"

                            # Verificar separación mínima
                            if libre:
                                for sx in range(-separacion, separacion + 1):
                                    for sy in range(-separacion,
                                                    separacion + 1):
                                        tx, ty = nx + sx, ny + sy
                                        if (
                                                0 <= tx < len(mapa[0])
                                                and 0 <= ty < len(mapa)
                                                and (tx, ty) in ocupadas
                                        ):
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
            else:
                ocupadas.add((x0, y0))


def crear_objetos_pedidos(pedidos_data):
    """Crea y retorna los pedidos tomándolos de la API."""
    return [Pedido(p["pickup"], p["dropoff"],
                   p.get("weight", 1), p.get("priority", 0),
                   p.get("payout", 100)) for p in pedidos_data]
    # Los .get toman los valores del archivo .json.
