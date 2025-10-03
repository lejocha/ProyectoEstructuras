"""
clases.py.

Se crea la clase "Pedido" y se crea la clase
"ColaPedidos" que será utilizada mediante un
heap para ordenar los pedidos por prioridad.
"""

import heapq


class Pedido:
    """Clase para crear un objeto pedido."""

    def __init__(self, pickup, dropoff, weight=1, priority=0, payout=100):
        """Construye el objeto Pedido."""
        self.pickup = pickup
        self.dropoff = dropoff
        self.weight = weight
        self.priority = priority  # entre más alto, más urgente
        self.payout = payout

    def __lt__(self, other):
        """Prioridad más alta primero."""
        return self.priority > other.priority


class ColaPedidos:
    """Clase para crear la cola de pedidos del jugador."""

    def __init__(self, lista_pedidos):
        """Construye la cola de pedidos hace uso de heapq."""
        self.cola = []
        for p in lista_pedidos:
            pedido = Pedido(
                p["pickup"],
                p["dropoff"],
                p.get("weight", 1),
                p.get("priority", 0),
                p.get("payout", 100)
            )
            heapq.heappush(self.cola, pedido)

    def agregar_pedido(self, pedido):
        """Agrega un pedido al heap."""
        heapq.heappush(self.cola, pedido)

    def obtener_siguiente(self):
        """Obtiene el siguiente elemento en orden de prioridad."""
        if self.cola:
            return heapq.heappop(self.cola)  # sale el de mayor prioridad
        return None
