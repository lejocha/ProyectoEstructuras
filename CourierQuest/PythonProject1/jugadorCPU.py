"""
jugador_cpu.py.

Implementa la clase base para jugadores CPU con
diferentes niveles de dificultad para competir
contra el jugador humano en Courier Quest.
"""

import random
import time
from collections import deque
from jugador import Jugador


class JugadorCPU(Jugador):
    """Clase base para jugadores controlados por IA."""

    def __init__(self, x, y, dificultad='facil', capacidad=10):
        """
        Construye un jugador CPU.

        Args:
            x (int): Posición inicial X
            y (int): Posición inicial Y
            dificultad (str): 'facil', 'medio', o 'dificil'
            capacidad (int): Capacidad de carga máxima
        """
        super().__init__(x, y, capacidad)
        self.dificultad = dificultad
        self.es_cpu = True
        self.objetivo_actual = None
        self.tipo_objetivo = None  # 'pickup' o 'dropoff'
        self.ultimo_cambio_objetivo = time.time()
        self.tiempo_cambio_objetivo = 5  # Cambiar objetivo cada 5 segundos
        self.ultimo_movimiento = time.time()
        self.intervalo_movimiento = 0.3  # Segundos entre movimientos

    def actualizar(self, pedidos_activos, mapa, clima_mult, consumo_clima):
        """
        Actualiza el estado del CPU y ejecuta su lógica de decisión.

        Args:
            pedidos_activos (list): Lista de pedidos disponibles
            mapa (list): Matriz del mapa
            clima_mult (float): Multiplicador del clima
            consumo_clima (float): Consumo extra por clima
        """
        ahora = time.time()

        # Recuperar resistencia
        self.recuperar()

        # Verificar si puede moverse
        if self.bloqueado:
            return

        # Control de velocidad de movimiento
        if ahora - self.ultimo_movimiento < self.intervalo_movimiento:
            return

        # Decidir y ejecutar acción según dificultad
        if self.dificultad == 'facil':
            self._comportamiento_facil(
                pedidos_activos, mapa, clima_mult, consumo_clima)
        elif self.dificultad == 'medio':
            self._comportamiento_medio(
                pedidos_activos, mapa, clima_mult, consumo_clima)
        elif self.dificultad == 'dificil':
            self._comportamiento_dificil(
                pedidos_activos, mapa, clima_mult, consumo_clima)

        self.ultimo_movimiento = ahora

    def _comportamiento_facil(
            self, pedidos_activos, mapa, clima_mult, consumo_clima):
        """
        Implementa comportamiento aleatorio (dificultad fácil).

        - Elige trabajos al azar
        - Se mueve aleatoriamente evitando edificios
        - Cambia objetivo después de tiempo límite
        """
        ahora = time.time()

        # Verificar si necesita nuevo objetivo
        if (self.objetivo_actual is None or
                ahora - self.ultimo_cambio_objetivo >
                self.tiempo_cambio_objetivo):
            self._elegir_objetivo_aleatorio(pedidos_activos)
            self.ultimo_cambio_objetivo = ahora

        # Verificar recolección automática
        self._verificar_recoleccion(pedidos_activos)

        # Verificar entrega automática
        self._verificar_entrega()

        # Movimiento aleatorio
        direcciones_validas = self._obtener_direcciones_validas(mapa)
        if direcciones_validas:
            dx, dy = random.choice(direcciones_validas)
            self.mover(dx, dy, mapa, clima_mult, consumo_clima)

    def _comportamiento_medio(
            self, pedidos_activos, mapa, clima_mult, consumo_clima):
        """
        Implementa búsqueda greedy con evaluación heurística.

        - Evalúa movimientos futuros (2-3 pasos adelante)
        - Usa función de puntaje: score = α*payout - β*distance - γ*weather
        - Selecciona movimiento con máxima puntuación
        """
        # Verificar recolección y entrega
        self._verificar_recoleccion(pedidos_activos)
        self._verificar_entrega()

        # Si no tiene objetivo, elegir el mejor según heurística
        if self.objetivo_actual is None:
            self._elegir_mejor_objetivo(pedidos_activos, mapa)

        # Si tiene objetivo, moverse hacia él con evaluación greedy
        if self.objetivo_actual:
            mejor_movimiento = self._evaluar_mejor_movimiento(
                mapa, clima_mult, consumo_clima)
            if mejor_movimiento:
                dx, dy = mejor_movimiento
                self.mover(dx, dy, mapa, clima_mult, consumo_clima)
        else:
            # Sin objetivo válido, movimiento aleatorio
            direcciones_validas = self._obtener_direcciones_validas(mapa)
            if direcciones_validas:
                dx, dy = random.choice(direcciones_validas)
                self.mover(dx, dy, mapa, clima_mult, consumo_clima)

    def _comportamiento_dificil(
            self, pedidos_activos, mapa, clima_mult, consumo_clima):
        """
        Implementa búsqueda de ruta óptima con algoritmos de grafos.

        - Usa A* o Dijkstra para encontrar rutas óptimas
        - Considera costos de superficie y clima
        - Replanifica dinámicamente según condiciones
        - Optimiza secuencia de entregas
        """
        # Verificar recolección y entrega
        self._verificar_recoleccion(pedidos_activos)
        self._verificar_entrega()

        # Elegir mejor objetivo con planificación a largo plazo
        if self.objetivo_actual is None:
            self._elegir_objetivo_optimo(pedidos_activos, mapa, clima_mult)

        # Moverse según ruta calculada con A*
        if self.objetivo_actual:
            siguiente_paso = self._calcular_siguiente_paso_astar(
                mapa, clima_mult)
            if siguiente_paso:
                dx = siguiente_paso[0] - self.x
                dy = siguiente_paso[1] - self.y
                self.mover(dx, dy, mapa, clima_mult, consumo_clima)
        else:
            # Sin objetivo, buscar el más cercano
            direcciones_validas = self._obtener_direcciones_validas(mapa)
            if direcciones_validas:
                dx, dy = random.choice(direcciones_validas)
                self.mover(dx, dy, mapa, clima_mult, consumo_clima)

    def _elegir_objetivo_aleatorio(self, pedidos_activos):
        """Elige un objetivo aleatorio de los pedidos disponibles."""
        if self.inventario and random.random() < 0.7:
            # 70% prioridad a entregar si tiene pedidos
            pedido = random.choice(list(self.inventario))
            self.objetivo_actual = tuple(pedido.dropoff)
            self.tipo_objetivo = 'dropoff'
        elif pedidos_activos:
            # Recoger nuevo pedido
            pedido = random.choice(pedidos_activos)
            self.objetivo_actual = tuple(pedido.pickup)
            self.tipo_objetivo = 'pickup'
        else:
            self.objetivo_actual = None

    def _elegir_mejor_objetivo(self, pedidos_activos, mapa):
        """
        Elige objetivo usando heurística greedy.

        Considera: distancia, pago, prioridad, clima.
        """
        mejor_score = float('-inf')
        mejor_objetivo = None
        mejor_tipo = None

        # Evaluar entregas pendientes
        for pedido in self.inventario:
            distancia = self._calcular_distancia(
                self.x, self.y, pedido.dropoff[0], pedido.dropoff[1])
            score = (pedido.payout * 1.5 - distancia * 10 -
                     pedido.priority * 20)

            if score > mejor_score:
                mejor_score = score
                mejor_objetivo = tuple(pedido.dropoff)
                mejor_tipo = 'dropoff'

        # Evaluar pedidos disponibles
        if len(self.inventario) < self.capacidad:
            for pedido in pedidos_activos:
                if self.peso_total() + pedido.weight <= self.capacidad:
                    distancia = self._calcular_distancia(
                        self.x, self.y, pedido.pickup[0], pedido.pickup[1])
                    score = (pedido.payout - distancia * 5 -
                             pedido.priority * 15)

                    if score > mejor_score:
                        mejor_score = score
                        mejor_objetivo = tuple(pedido.pickup)
                        mejor_tipo = 'pickup'

        self.objetivo_actual = mejor_objetivo
        self.tipo_objetivo = mejor_tipo

    def _elegir_objetivo_optimo(self, pedidos_activos, mapa, clima_mult):
        """
        Elige objetivo optimizando secuencia de entregas.

        Usa planificación a largo plazo considerando
        múltiples entregas futuras.
        """
        if self.inventario:
            # Calcular secuencia óptima de entregas
            mejor_secuencia = self._calcular_mejor_secuencia_entregas(
                mapa, clima_mult)
            if mejor_secuencia:
                self.objetivo_actual = mejor_secuencia[0]
                self.tipo_objetivo = 'dropoff'
                return

        # Si no hay secuencia o inventario vacío, buscar mejor pickup
        if len(self.inventario) < self.capacidad and pedidos_activos:
            mejor_pedido = self._evaluar_mejor_pedido(
                pedidos_activos, mapa, clima_mult)
            if mejor_pedido:
                self.objetivo_actual = tuple(mejor_pedido.pickup)
                self.tipo_objetivo = 'pickup'

    def _evaluar_mejor_movimiento(self, mapa, clima_mult, consumo_clima):
        """
        Evalúa y retorna el mejor movimiento usando búsqueda greedy.

        Returns:
            tuple: (dx, dy) del mejor movimiento o None
        """
        if not self.objetivo_actual:
            return None

        direcciones_validas = self._obtener_direcciones_validas(mapa)
        if not direcciones_validas:
            return None

        mejor_movimiento = None
        menor_distancia = float('inf')

        for dx, dy in direcciones_validas:
            nueva_x = self.x + dx
            nueva_y = self.y + dy

            distancia = self._calcular_distancia(
                nueva_x, nueva_y,
                self.objetivo_actual[0], self.objetivo_actual[1])

            if distancia < menor_distancia:
                menor_distancia = distancia
                mejor_movimiento = (dx, dy)

        return mejor_movimiento

    def _calcular_siguiente_paso_astar(self, mapa, clima_mult):
        """
        Calcula el siguiente paso usando algoritmo A*.

        Returns:
            tuple: (x, y) del siguiente paso o None
        """
        if not self.objetivo_actual:
            return None

        ruta = self._astar(
            (self.x, self.y), self.objetivo_actual, mapa, clima_mult)

        if ruta and len(ruta) > 1:
            return ruta[1]  # Retornar el siguiente paso
        return None

    def _astar(self, inicio, objetivo, mapa, clima_mult):
        """
        Implementa algoritmo A* para encontrar ruta óptima.

        Args:
            inicio (tuple): Posición inicial (x, y)
            objetivo (tuple): Posición objetivo (x, y)
            mapa (list): Matriz del mapa
            clima_mult (float): Multiplicador del clima

        Returns:
            list: Lista de posiciones (x, y) de la ruta o None
        """
        from heapq import heappush, heappop

        def heuristica(pos):
            return abs(pos[0] - objetivo[0]) + abs(pos[1] - objetivo[1])

        def costo_movimiento(pos):
            x, y = pos
            if not (0 <= x < len(mapa[0]) and 0 <= y < len(mapa)):
                return float('inf')
            if mapa[y][x] == 'B':
                return float('inf')

            # Costo base según tipo de tile
            costos = {'C': 1.0, 'P': 0.95, 'B': float('inf')}
            costo_base = costos.get(mapa[y][x], 1.0)

            # Ajustar por clima
            return costo_base / max(0.1, clima_mult)

        frontera = []
        heappush(frontera, (0, inicio))
        vino_de = {inicio: None}
        costo_hasta = {inicio: 0}

        while frontera:
            _, actual = heappop(frontera)

            if actual == objetivo:
                # Reconstruir ruta
                ruta = []
                while actual:
                    ruta.append(actual)
                    actual = vino_de[actual]
                return list(reversed(ruta))

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                vecino = (actual[0] + dx, actual[1] + dy)

                if not (0 <= vecino[0] < len(mapa[0]) and
                        0 <= vecino[1] < len(mapa)):
                    continue

                if mapa[vecino[1]][vecino[0]] == 'B':
                    continue

                nuevo_costo = (costo_hasta[actual] +
                               costo_movimiento(vecino))

                if vecino not in costo_hasta or nuevo_costo < costo_hasta[vecino]:
                    costo_hasta[vecino] = nuevo_costo
                    prioridad = nuevo_costo + heuristica(vecino)
                    heappush(frontera, (prioridad, vecino))
                    vino_de[vecino] = actual

        return None  # No se encontró ruta

    def _calcular_mejor_secuencia_entregas(self, mapa, clima_mult):
        """
        Calcula secuencia óptima de entregas (aproximación TSP).

        Returns:
            list: Lista de posiciones objetivo ordenadas
        """
        if not self.inventario:
            return []

        # Enfoque greedy: entregar más cercano primero
        secuencia = []
        pendientes = [tuple(p.dropoff) for p in self.inventario]
        actual = (self.x, self.y)

        while pendientes:
            mejor_siguiente = None
            menor_distancia = float('inf')

            for pos in pendientes:
                distancia = self._calcular_distancia(
                    actual[0], actual[1], pos[0], pos[1])
                if distancia < menor_distancia:
                    menor_distancia = distancia
                    mejor_siguiente = pos

            if mejor_siguiente:
                secuencia.append(mejor_siguiente)
                pendientes.remove(mejor_siguiente)
                actual = mejor_siguiente

        return secuencia

    def _evaluar_mejor_pedido(self, pedidos_activos, mapa, clima_mult):
        """
        Evalúa y retorna el mejor pedido disponible.

        Considera: pago, distancia, peso, prioridad.
        """
        mejor_pedido = None
        mejor_score = float('-inf')

        for pedido in pedidos_activos:
            if self.peso_total() + pedido.weight > self.capacidad:
                continue

            distancia_pickup = self._calcular_distancia(
                self.x, self.y, pedido.pickup[0], pedido.pickup[1])
            distancia_dropoff = self._calcular_distancia(
                pedido.pickup[0], pedido.pickup[1],
                pedido.dropoff[0], pedido.dropoff[1])

            distancia_total = distancia_pickup + distancia_dropoff

            # Score: maximizar pago, minimizar distancia y peso
            score = (pedido.payout * 2.0 -
                     distancia_total * 8 -
                     pedido.weight * 5 -
                     pedido.priority * 25)

            if score > mejor_score:
                mejor_score = score
                mejor_pedido = pedido

        return mejor_pedido

    def _obtener_direcciones_validas(self, mapa):
        """
        Retorna lista de direcciones válidas (no bloqueadas).

        Returns:
            list: Lista de tuplas (dx, dy)
        """
        direcciones = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        validas = []

        for dx, dy in direcciones:
            nx, ny = self.x + dx, self.y + dy

            if (0 <= nx < len(mapa[0]) and 0 <= ny < len(mapa) and
                    mapa[ny][nx] != 'B'):
                validas.append((dx, dy))

        return validas

    def _verificar_recoleccion(self, pedidos_activos):
        """Verifica y recoge pedidos automáticamente si está en pickup."""
        for pedido in list(pedidos_activos):
            if [self.x, self.y] == pedido.pickup:
                if self.recoger_pedido(pedido):
                    pedidos_activos.remove(pedido)
                    # Cambiar objetivo a entrega
                    self.objetivo_actual = tuple(pedido.dropoff)
                    self.tipo_objetivo = 'dropoff'

    def _verificar_entrega(self):
        """Verifica y entrega pedidos automáticamente si está en dropoff."""
        pedido_entregado = self.entregar_pedido()
        if pedido_entregado:
            # Limpiar objetivo actual
            self.objetivo_actual = None
            self.tipo_objetivo = None

    def _calcular_distancia(self, x1, y1, x2, y2):
        """Calcula distancia Manhattan entre dos puntos."""
        return abs(x1 - x2) + abs(y1 - y2)