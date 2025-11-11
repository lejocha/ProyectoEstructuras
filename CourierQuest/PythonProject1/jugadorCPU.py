"""
jugador_cpu.py - VERSIÓN CORREGIDA.

Implementa la clase para jugadores CPU con
diferentes niveles de dificultad.
Corrige problemas de movimiento estático.
"""

import random
import time
from collections import deque
from jugador import Jugador


class JugadorCPU(Jugador):
    """Clase para jugadores controlados por IA."""

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
        self.tipo_objetivo = None
        self.ultimo_cambio_objetivo = time.time()
        self.tiempo_cambio_objetivo = 5

        # CORRECCIÓN: Iniciar con tiempo negativo para moverse inmediatamente
        self.ultimo_movimiento = 0

        # CORRECCIÓN: Intervalos más cortos por dificultad
        if dificultad == 'facil':
            self.intervalo_movimiento = 0.2
        elif dificultad == 'medio':
            self.intervalo_movimiento = 0.15
        else:  # dificil
            self.intervalo_movimiento = 0.1

        print(f"CPU creado: dif={dificultad}, pos=({x},{y}), intervalo={self.intervalo_movimiento}s")

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

        # Si está exhausto, solo esperar (no bloquear completamente)
        if self.resistencia <= 0:
            if ahora - self.ultimo_movimiento >= 2.0:  # Esperar 2 segundos
                self.ultimo_movimiento = ahora
            return

        # Control de velocidad de movimiento
        if ahora - self.ultimo_movimiento < self.intervalo_movimiento:
            return

        # DEBUG: descomentar para ver actividad del CPU
        # print(f"CPU actualizando: {self.dificultad}, pos=({self.x},{self.y})")

        # Decidir y ejecutar acción según dificultad
        movimiento_realizado = False

        if self.dificultad == 'facil':
            movimiento_realizado = self._comportamiento_facil(
                pedidos_activos, mapa, clima_mult, consumo_clima)
        elif self.dificultad == 'medio':
            movimiento_realizado = self._comportamiento_medio(
                pedidos_activos, mapa, clima_mult, consumo_clima)
        elif self.dificultad == 'dificil':
            movimiento_realizado = self._comportamiento_dificil(
                pedidos_activos, mapa, clima_mult, consumo_clima)

        # CORRECCIÓN: Actualizar tiempo incluso si no se movió
        self.ultimo_movimiento = ahora

    def _comportamiento_facil(
            self, pedidos_activos, mapa, clima_mult, consumo_clima):
        """
        Implementa comportamiento aleatorio (dificultad fácil).

        Returns:
            bool: True si se realizó algún movimiento
        """
        ahora = time.time()

        # Verificar recolección automática
        self._verificar_recoleccion(pedidos_activos)

        # Verificar entrega automática
        self._verificar_entrega()

        # Cambiar objetivo periódicamente
        if (self.objetivo_actual is None or
                ahora - self.ultimo_cambio_objetivo > self.tiempo_cambio_objetivo):
            self._elegir_objetivo_aleatorio(pedidos_activos)
            self.ultimo_cambio_objetivo = ahora

        # Movimiento aleatorio
        direcciones_validas = self._obtener_direcciones_validas(mapa)
        if direcciones_validas:
            dx, dy = random.choice(direcciones_validas)
            resultado = self.mover(dx, dy, mapa, clima_mult, consumo_clima)
            return resultado

        return False

    def _comportamiento_medio(
            self, pedidos_activos, mapa, clima_mult, consumo_clima):
        """
        Implementa búsqueda greedy con evaluación heurística.

        Returns:
            bool: True si se realizó algún movimiento
        """
        # Verificar recolección y entrega
        self._verificar_recoleccion(pedidos_activos)
        self._verificar_entrega()

        # Si no tiene objetivo, elegir el mejor según heurística
        if self.objetivo_actual is None:
            self._elegir_mejor_objetivo(pedidos_activos, mapa)

        # Si tiene objetivo, moverse hacia él
        if self.objetivo_actual:
            mejor_movimiento = self._evaluar_mejor_movimiento(mapa)
            if mejor_movimiento:
                dx, dy = mejor_movimiento
                resultado = self.mover(dx, dy, mapa, clima_mult, consumo_clima)
                return resultado

        # Sin objetivo válido, movimiento aleatorio
        direcciones_validas = self._obtener_direcciones_validas(mapa)
        if direcciones_validas:
            dx, dy = random.choice(direcciones_validas)
            return self.mover(dx, dy, mapa, clima_mult, consumo_clima)

        return False

    def _comportamiento_dificil(
            self, pedidos_activos, mapa, clima_mult, consumo_clima):
        """
        Implementa búsqueda de ruta óptima con A*.

        Returns:
            bool: True si se realizó algún movimiento
        """
        # Verificar recolección y entrega
        self._verificar_recoleccion(pedidos_activos)
        self._verificar_entrega()

        # Elegir mejor objetivo con planificación
        if self.objetivo_actual is None:
            self._elegir_objetivo_optimo(pedidos_activos, mapa, clima_mult)

        # Moverse según ruta calculada con A*
        if self.objetivo_actual:
            siguiente_paso = self._calcular_siguiente_paso_astar(
                mapa, clima_mult)
            if siguiente_paso:
                dx = siguiente_paso[0] - self.x
                dy = siguiente_paso[1] - self.y
                resultado = self.mover(dx, dy, mapa, clima_mult, consumo_clima)
                return resultado

        # Sin objetivo o ruta, movimiento aleatorio
        direcciones_validas = self._obtener_direcciones_validas(mapa)
        if direcciones_validas:
            dx, dy = random.choice(direcciones_validas)
            return self.mover(dx, dy, mapa, clima_mult, consumo_clima)

        return False

    def _elegir_objetivo_aleatorio(self, pedidos_activos):
        """Elige un objetivo aleatorio de los pedidos disponibles."""
        if self.inventario and random.random() < 0.7:
            # 70% prioridad a entregar si tiene pedidos
            pedido = random.choice(list(self.inventario))
            self.objetivo_actual = tuple(pedido.dropoff)
            self.tipo_objetivo = 'dropoff'
        elif pedidos_activos and len(self.inventario) < self.capacidad:
            # Recoger nuevo pedido
            pedido = random.choice(pedidos_activos)
            self.objetivo_actual = tuple(pedido.pickup)
            self.tipo_objetivo = 'pickup'
        else:
            self.objetivo_actual = None

    def _elegir_mejor_objetivo(self, pedidos_activos, mapa):
        """
        Elige objetivo usando heurística greedy.
        """
        mejor_score = float('-inf')
        mejor_objetivo = None
        mejor_tipo = None

        # Evaluar entregas pendientes (prioridad alta)
        for pedido in self.inventario:
            distancia = self._calcular_distancia(
                self.x, self.y, pedido.dropoff[0], pedido.dropoff[1])
            # Score: pago alto, distancia baja
            score = pedido.payout * 1.5 - distancia * 10 - pedido.priority * 20

            if score > mejor_score:
                mejor_score = score
                mejor_objetivo = tuple(pedido.dropoff)
                mejor_tipo = 'dropoff'

        # Evaluar pedidos disponibles (si hay espacio)
        if len(self.inventario) < self.capacidad:
            for pedido in pedidos_activos:
                if self.peso_total() + pedido.weight <= self.capacidad:
                    distancia = self._calcular_distancia(
                        self.x, self.y, pedido.pickup[0], pedido.pickup[1])
                    score = pedido.payout * 1.2 - distancia * 5 - pedido.priority * 15

                    if score > mejor_score:
                        mejor_score = score
                        mejor_objetivo = tuple(pedido.pickup)
                        mejor_tipo = 'pickup'

        self.objetivo_actual = mejor_objetivo
        self.tipo_objetivo = mejor_tipo

    def _elegir_objetivo_optimo(self, pedidos_activos, mapa, clima_mult):
        """Elige objetivo optimizando secuencia de entregas."""
        if self.inventario:
            # Calcular secuencia óptima de entregas
            mejor_secuencia = self._calcular_mejor_secuencia_entregas()
            if mejor_secuencia:
                self.objetivo_actual = mejor_secuencia[0]
                self.tipo_objetivo = 'dropoff'
                return

        # Si no hay secuencia, buscar mejor pickup
        if len(self.inventario) < self.capacidad and pedidos_activos:
            mejor_pedido = self._evaluar_mejor_pedido(
                pedidos_activos, mapa, clima_mult)
            if mejor_pedido:
                self.objetivo_actual = tuple(mejor_pedido.pickup)
                self.tipo_objetivo = 'pickup'

    def _evaluar_mejor_movimiento(self, mapa):
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

            costos = {'C': 1.0, 'P': 0.95, 'B': float('inf')}
            costo_base = costos.get(mapa[y][x], 1.0)
            return costo_base / max(0.1, clima_mult)

        frontera = []
        heappush(frontera, (0, inicio))
        vino_de = {inicio: None}
        costo_hasta = {inicio: 0}

        # CORRECCIÓN: Limitar iteraciones para evitar lag
        max_iterations = 500
        iterations = 0

        while frontera and iterations < max_iterations:
            iterations += 1
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

        return None

    def _calcular_mejor_secuencia_entregas(self):
        """
        Calcula secuencia óptima de entregas (greedy TSP).

        Returns:
            list: Lista de posiciones objetivo ordenadas
        """
        if not self.inventario:
            return []

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
        """Evalúa y retorna el mejor pedido disponible."""
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
        """Verifica y recoge pedidos automáticamente."""
        for pedido in list(pedidos_activos):
            if [self.x, self.y] == pedido.pickup:
                if self.recoger_pedido(pedido):
                    pedidos_activos.remove(pedido)
                    self.objetivo_actual = tuple(pedido.dropoff)
                    self.tipo_objetivo = 'dropoff'
                    print(f"CPU recogió pedido en ({self.x},{self.y})")

    def _verificar_entrega(self):
        """Verifica y entrega pedidos automáticamente."""
        pedido_entregado = self.entregar_pedido()
        if pedido_entregado:
            self.objetivo_actual = None
            self.tipo_objetivo = None
            print(f"CPU entregó pedido en ({self.x},{self.y}) - ${self.puntaje}")

    def _calcular_distancia(self, x1, y1, x2, y2):
        """Calcula distancia Manhattan entre dos puntos."""
        return abs(x1 - x2) + abs(y1 - y2)