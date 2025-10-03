"""
clases.py.

Se crea la clase Jugador en la que se manejará
su inventario, resistencia, puntaje, entre otros.
Además de sus acciones como moverse u acciones
del jugador con los pedidos como (recoger,
entregar, entre otros).
"""

import time
from collections import deque  # Para utilizar colas


class Jugador:
    """Clase para crear un objeto Jugador."""

    def __init__(self, x, y, capacidad=10):
        """Construye el objeto jugador con su direccion (x,y) y variables."""
        self.x = x           # Ubicación del personaje.
        self.y = y
        self.inventario = deque()   # Inventario en cola.
        self.resistencia = 100
        self.max_resistencia = 100
        self.puntaje = 0
        self.reputacion = 70
        self.velocidad_base = 3
        self.ticks_sin_mover = 0
        self.capacidad = capacidad
        self.bloqueado = False
        self.ultimo_recupero = time.time()
        self.mensaje = ""
        self.mensaje_tiempo = 0
        # Entregas
        self.entregas_completadas = 0
        self.cancelaciones = 0
        self.entregas_tempranas = 0
        self.entregas_tardias = 0

    def peso_total(self):
        """Calcula el peso total actual del jugador."""
        return sum(p.weight for p in self.inventario)

    def calcular_multiplicador_velocidad(self, clima_mult, mapa_tiles):
        """Calcula el multiplicador de velocidad usando la fórmula completa.

        v = v0 * mclima * mpeso * mrep * mresistencia * surface_weight.
        """
        # mpeso = max(0.8, 1 - 0.03 * peso_total).
        peso = self.peso_total()
        mpeso = max(0.8, 1 - 0.03 * peso)

        # mrep = 1.03 si reputación >= 90, si no 1.0.
        mrep = 1.03 if self.reputacion >= 90 else 1.0

        # mresistencia según estado.
        if self.resistencia <= 0:
            mresistencia = 0  # Exhausto.
        elif self.resistencia <= 30:
            mresistencia = 0.8  # Cansado.
        else:
            mresistencia = 1.0  # Normal.

        # Surface_weight del tile actual.
        tile_actual = mapa_tiles[self.y][self.x]\
            if 0 <= self.y < len(mapa_tiles) and 0 <= self.x < len(
            mapa_tiles[0]) else 'C'
        surface_weights = {
            'C': 1.0, 'P': 0.95, 'B': 0.0}  # Edificios bloqueados.
        surface_weight = surface_weights.get(tile_actual, 1.0)

        velocidad_final = (self.velocidad_base
                           * clima_mult * mpeso * mrep
                           * mresistencia * surface_weight)
        return max(0, velocidad_final)

    def mover(self, dx, dy, mapa, clima_mult=1.0, consumo_clima_extra=0.0):
        """Cambia la direccion en (x,y) del jugador.

        para moverse por el mapa.
        """
        if self.bloqueado:
            return False

        nx, ny = self.x + dx, self.y + dy

        # Verificar límites del mapa.
        if not (0 <= nx < len(mapa[0]) and 0 <= ny < len(mapa)):
            self.ticks_sin_mover += 1
            return False

        # Verificar si no es edificio.
        if mapa[ny][nx] == "B":
            self.ticks_sin_mover += 1
            return False

        # Calcular velocidad con fórmula completa.
        velocidad = self.calcular_multiplicador_velocidad(clima_mult, mapa)

        if velocidad <= 0:
            return False

        # Mover jugador.
        self.x, self.y = nx, ny

        # Calcular consumo de resistencia.
        consumo_base = 0.5
        peso_extra = max(0, self.peso_total() - 3)
        consumo_peso = 0.2 * peso_extra

        consumo_total = consumo_base + consumo_peso + consumo_clima_extra

        self.resistencia = max(0, self.resistencia - consumo_total)
        self.ticks_sin_mover = 0

        # Bloquear si se queda sin resistencia.
        if self.resistencia <= 0:
            self.bloqueado = True
            self.ultimo_recupero = time.time()

        return True

    def recuperar(self):
        """Maneja la recuperación de la resistencia del jugador."""
        ahora = time.time()
        if ahora - self.ultimo_recupero >= 1:  # Cada segundo
            puntos_recuperacion = 5  # 5 puntos por segundo según PDF
            self.resistencia = min(
                self.max_resistencia, self.resistencia + puntos_recuperacion)
            self.ultimo_recupero = ahora

            # Desbloquear si recupera suficiente resistencia
            if self.resistencia >= 30:
                self.bloqueado = False

    def recoger_pedido(self, pedido):
        """Recoge pedidos en el inventario si hay capacidad."""
        pedido.tiempo_recogido = time.time()

        if self.peso_total() + pedido.weight <= self.capacidad:
            self.inventario.append(pedido)
            self.mensaje = f"Pedido recogido (Peso: {pedido.weight})"
            self.mensaje_tiempo = time.time()
            return True
        else:
            self.mensaje = \
                f"Capacidad insuficiente (Peso necesario: {pedido.weight})"
            self.mensaje_tiempo = time.time()
            return False

    def cancelar_ultimo_pedido(self):
        """Cancelar el último pedido recogido."""
        if self.inventario:
            pedido_cancelado = self.inventario.pop()
            self.reputacion = max(0, self.reputacion - 4)
            self.cancelaciones += 1
            self.mensaje = \
                (f"Pedido cancelado (-4 reputación)"
                 f" Peso liberado: {pedido_cancelado.weight}")
            self.mensaje_tiempo = time.time()
            return pedido_cancelado
        else:
            self.mensaje = "No hay pedidos para cancelar"
            self.mensaje_tiempo = time.time()
            return None

    def entregar_pedido(self):
        """Entrega un pedido con sistema de prioridades mejorado."""
        if not self.inventario:
            return None

        # Encuentra el pedido de mayor prioridad disponible para entregar.
        max_priority = max(p.priority for p in self.inventario)
        pedidos_prioridad_max =\
            [p for p in self.inventario if p.priority == max_priority]

        # Revisar si el jugador está en el dropoff.
        # De algún pedido de mayor prioridad.
        for p in pedidos_prioridad_max:
            if [self.x, self.y] == p.dropoff:
                self.inventario.remove(p)

                # Calcular tiempo de entrega.
                tiempo_transcurrido =\
                    time.time() - getattr(p, "tiempo_recogido", time.time())

                # Sistema de reputación mejorado con bonos.
                if tiempo_transcurrido <= 20:  # Entrega puntual (≤20s).
                    if (tiempo_transcurrido
                            <= 16):  # Entrega temprana (≥20% antes de 20s).
                        self.reputacion = min(100, self.reputacion + 5)
                        self.entregas_tempranas += 1
                        self.mensaje = "Entrega TEMPRANA! +5 reputación"
                    else:
                        self.reputacion = min(100, self.reputacion + 3)
                        self.mensaje = "Entrega puntual +3 reputación"
                else:
                    # Entregas tardías con penalizaciones escaladas.
                    if (tiempo_transcurrido <= 50):
                        # 21-50s (Equivalente a ≤30s en escala real).
                        self.reputacion = max(0, self.reputacion - 2)
                        self.mensaje =\
                            "Entrega ligeramente tardía -2 reputación"
                    elif (tiempo_transcurrido
                          <= 140):  # 51-140s (equivalente a 31-120s).
                        self.reputacion = max(0, self.reputacion - 5)
                        self.mensaje = "Entrega tardía -5 reputación"
                    else:  # >140s (equivalente a >120s).
                        self.reputacion = max(0, self.reputacion - 10)
                        self.mensaje = "Entrega MUY tardía -10 reputación"

                    self.entregas_tardias += 1

                # Aplicar pago base.
                pago_base = p.payout
                self.puntaje += pago_base

                # Bonus de 5% si reputación >= 90.
                bonus = 0
                if self.reputacion >= 90:
                    bonus = int(pago_base * 0.05)
                    self.puntaje += bonus
                    self.mensaje += f" +{bonus} bonus reputación"

                self.entregas_completadas += 1
                self.mensaje_tiempo = time.time()

                # Sistema de rachas.
                # (bonus cada 3 entregas puntuales consecutivas).
                if hasattr(self, 'racha_entregas_puntuales'):
                    if tiempo_transcurrido <= 20:
                        self.racha_entregas_puntuales += 1
                        if self.racha_entregas_puntuales >= 3:
                            self.reputacion = min(100, self.reputacion + 2)
                            self.mensaje += " +2 bonus racha!"
                            self.racha_entregas_puntuales = 0
                    else:
                        self.racha_entregas_puntuales = 0
                else:
                    self.racha_entregas_puntuales =\
                        1 if tiempo_transcurrido <= 20 else 0

                return p

        # No se puede entregar porque hay pedido de mayor prioridad.
        return None

    def obtener_inventario_ordenado(self, criterio='prioridad'):
        """Retorna el inventario del jugador ordenado por prioridad."""
        if criterio == 'prioridad':
            return sorted(self.inventario,
                          key=lambda p: p.priority, reverse=True)
        else:
            return list(self.inventario)

    def obtener_inventario_por_plata(self):
        """Hace Insertion sort a los pedidos, los ordena por plata."""
        lista = list(self.inventario)
        # Se pasa de queue a lista para hacer el ordenamiento.
        for i in range(1, len(lista)):
            actual = lista[i]
            j = i - 1
            while j >= 0 and lista[j].payout < actual.payout:
                lista[j + 1] = lista[j]
                j -= 1
            lista[j + 1] = actual
        self.inventario = deque(lista)  # Convierte nuevamente a queue.
        return list(self.inventario)

    def obtener_estadisticas(self):
        """Retorna estadísticas del jugador para mostrar en UI."""
        return {
            'entregas_completadas': self.entregas_completadas,
            'cancelaciones': self.cancelaciones,
            'entregas_tempranas': self.entregas_tempranas,
            'entregas_tardias': self.entregas_tardias,
            'peso_actual': self.peso_total(),
            'capacidad_libre': self.capacidad - self.peso_total(),
            'eficiencia': self.entregas_completadas / max(
                1, self.entregas_completadas + self.cancelaciones),
            'puntualidad': self.entregas_tempranas / max(
                1, self.entregas_completadas)
        }

    def obtener_estado_resistencia(self):
        """Retorna el estado actual de resistencia."""
        if self.resistencia <= 0:
            return "Exhausto"
        elif self.resistencia <= 30:
            return "Cansado"
        elif self.resistencia <= 50:
            return "Fatigado"
        else:
            return "Normal"
