"""
clima.py.

Aquí se maneja el sistema de clima del juego
con ayuda de la API, también maneja
los efectos del clima sobre el jugador.
"""

import random
import time
import json


class SistemaClima:
    """Crea el sistema de clima.

    Administra condiciones climáticas,
    las toma desde la API y hace que
    cambien automáticamente, también
    aplica los efectos del clima al jugador.
    """

    def __init__(self, api_module=None):
        """Construye el sistema.

        Carga la configuración del clima de la API y
        configura que siempre inicie con "clear".
        """
        self.api = api_module

        # Multiplicadores de velocidad para cada clima
        self.multiplicadores = {
            'clear': 1.00,
            'clouds': 0.98,
            'rain_light': 0.90,
            'rain': 0.85,
            'storm': 0.75,
            'fog': 0.88,
            'wind': 0.92,
            'heat': 0.90,
            'cold': 0.92
        }

        # Consumo extra de resistencia por clima
        self.consumo_resistencia = {
            'clear': 0.0,
            'clouds': 0.0,
            'rain_light': 0.05,
            'rain': 0.1,
            'storm': 0.3,
            'fog': 0.0,
            'wind': 0.1,
            'heat': 0.2,
            'cold': 0.05
        }

        # Variables del sistema
        self.estados_disponibles = []
        self.matriz_transicion = {}
        self.estado_actual = 'clear'
        self.intensidad_actual = 0.0
        self.tiempo_cambio = (
                time.time() + random.randint(45, 90))
        # 45-90 segundos

        # Variables de transición suave
        self.en_transicion = False
        self.estado_anterior = 'clear'
        self.multiplicador_anterior = 1.0
        self.tiempo_inicio_transicion = 0
        self.duracion_transicion = 3.0  # 3 segundos de transición

        # Cargar configuración del clima desde API
        self.cargar_configuracion_clima()

    def cargar_configuracion_clima(self):
        """Carga la configuración del clima de la API o archivo local."""
        try:
            if self.api:
                clima_data = self.api.obtener_clima()
            else:
                # Fallback a archivo local
                with open("data/clima.json", "r") as f:
                    clima_data = json.load(f)

            # Extraer datos de la API
            if "data" in clima_data:
                data = clima_data["data"]

                # Estados disponibles
                self.estados_disponibles =\
                    data.get("conditions", list(self.multiplicadores.keys()))

                # Configuración inicial
                initial = data.get(
                    "initial", {"condition": "clear", "intensity": 0.0})
                self.estado_actual = initial.get("condition", "clear")
                self.intensidad_actual = initial.get("intensity", 0.0)

                # Matriz de transición desde la API
                transition_data = data.get("transition", {})
                self.matriz_transicion =\
                    self._procesar_matriz_transicion(transition_data)

                print("Configuración del clima cargada desde API")
                print(f"Estado inicial: {self.estado_actual}")
                print(f"Estados disponibles: {len(self.estados_disponibles)}")

            else:
                print("Formato de API inesperado,"
                      " usando configuración por defecto")
                self._usar_configuracion_por_defecto()

        except Exception as e:
            print(f"Error al cargar clima de API: {e}")
            self._usar_configuracion_por_defecto()

    def _procesar_matriz_transicion(self, transition_data):
        """Convierte la matriz de transición.

         Lo hace del formato API al formato interno.

        API format: {"clear": {"clear": 0.6, "clouds": 0.3, "rain": 0.1}, ...}.
        Internal format: {"clear": ["clear", "clouds", "rain"],
        weights: [0.6, 0.3, 0.1]}.
        """
        matriz_procesada = {}

        for estado_origen, transiciones in transition_data.items():
            if estado_origen in self.estados_disponibles:
                # Extraer estados destino y sus probabilidades.
                estados_destino = []
                probabilidades = []

                for estado_destino, prob in transiciones.items():
                    if estado_destino in self.estados_disponibles:
                        estados_destino.append(estado_destino)
                        probabilidades.append(prob)

                # Normalizar probabilidades para asegurar que sumen 1.0.
                suma_prob = sum(probabilidades)
                if suma_prob > 0:
                    probabilidades = [p / suma_prob for p in probabilidades]

                    matriz_procesada[estado_origen] = {
                        'estados': estados_destino,
                        'probabilidades': probabilidades
                    }

        return matriz_procesada

    def _usar_configuracion_por_defecto(self):
        """Hace que se use un clima por defecto si el API falla."""
        self.estados_disponibles =\
            ['clear', 'clouds', 'rain_light', 'rain', 'storm',
             'fog', 'wind', 'heat', 'cold']
        self.estado_actual = 'clear'
        self.intensidad_actual = 0.5

        self.matriz_transicion = {  # Traduce los climas.
            'clear': {'estados': ['clear', 'clouds', 'wind'],
                      'probabilidades': [0.5, 0.3, 0.2]},
            'clouds': {'estados': ['clear', 'clouds', 'rain_light'],
                       'probabilidades': [0.3, 0.4, 0.3]},
            'rain_light': {'estados': ['clouds', 'rain_light', 'rain'],
                           'probabilidades': [0.4, 0.4, 0.2]},
            'rain': {'estados': ['clouds', 'rain', 'storm'],
                     'probabilidades': [0.4, 0.4, 0.2]},
            'storm': {'estados': ['rain', 'clouds', 'storm'],
                      'probabilidades': [0.5, 0.3, 0.2]},
            'fog': {'estados': ['fog', 'clouds', 'clear'],
                    'probabilidades': [0.5, 0.3, 0.2]},
            'wind': {'estados': ['wind', 'clouds', 'clear'],
                     'probabilidades': [0.5, 0.3, 0.2]},
            'heat': {'estados': ['heat', 'clear', 'clouds'],
                     'probabilidades': [0.5, 0.3, 0.2]},
            'cold': {'estados': ['cold', 'clear', 'clouds'],
                     'probabilidades': [0.5, 0.3, 0.2]}
        }

        print("Usando configuración de clima por defecto")

    def obtener_multiplicador_actual(self):
        """Retorna el multiplicador de velocidad.

        Retorna el actual (con transición suave).
        """
        if not self.en_transicion:
            base_mult = self.multiplicadores.get(self.estado_actual, 1.0)
            # Aplicar intensidad: a mayor intensidad, mayor efecto.
            return base_mult * (
                    1.0 - 0.5 * self.intensidad_actual * (1.0 - base_mult))

        # Durante transición, interpolar entre estados.
        tiempo_transcurrido = time.time() - self.tiempo_inicio_transicion
        progreso = min(1.0, tiempo_transcurrido / self.duracion_transicion)

        mult_anterior = self.multiplicadores.get(self.estado_anterior, 1.0)
        mult_nuevo = self.multiplicadores.get(self.estado_actual, 1.0)
        mult_nuevo *= (1.0 - 0.5 * self.intensidad_actual * (1.0 - mult_nuevo))

        # Interpolación linear.
        multiplicador = mult_anterior + (mult_nuevo - mult_anterior) * progreso

        # Finalizar transición.
        if progreso >= 1.0:
            self.en_transicion = False

        return multiplicador

    def obtener_consumo_resistencia_extra(self):
        """Retorna el consumo extra de resistencia por el clima actual."""
        consumo_base = self.consumo_resistencia.get(self.estado_actual, 0.0)

        if not self.en_transicion:
            return consumo_base * (1.0 + self.intensidad_actual)

        # Durante transición, interpolar.
        tiempo_transcurrido = time.time() - self.tiempo_inicio_transicion
        progreso = min(1.0, tiempo_transcurrido / self.duracion_transicion)

        consumo_anterior = self.consumo_resistencia.get(
            self.estado_anterior, 0.0)
        consumo_nuevo = consumo_base * (1.0 + self.intensidad_actual)

        return consumo_anterior + (consumo_nuevo - consumo_anterior) * progreso

    def actualizar(self):
        """Actualiza el estado del clima.

        Lo actualiza según el tiempo y la cadena de Markov.
        """
        ahora = time.time()

        # Verificar si es hora de cambiar el clima.
        if ahora >= self.tiempo_cambio:
            self._cambiar_clima()

    def _cambiar_clima(self):
        """Cambia el clima usando la matriz de Markov cargada desde la API."""
        if self.estado_actual not in self.matriz_transicion:
            print(f"Estado {self.estado_actual} no encontrado en matriz,"
                  f" usando aleatorio")
            nuevo_estado = random.choice(self.estados_disponibles)
        else:
            transicion = self.matriz_transicion[self.estado_actual]
            estados = transicion['estados']
            probabilidades = transicion['probabilidades']

            # Seleccionar siguiente estado basado en probabilidades.
            nuevo_estado = random.choices(estados, weights=probabilidades)[0]

        # Generar nueva intensidad (0.0 a 1.0).
        nueva_intensidad = random.uniform(0.2, 1.0)

        # Iniciar transición suave.
        self.estado_anterior = self.estado_actual
        self.estado_actual = nuevo_estado
        self.intensidad_actual = nueva_intensidad

        self.en_transicion = True
        self.tiempo_inicio_transicion = time.time()

        # Programar próximo cambio (45-90 segundos según especificación).
        self.tiempo_cambio = time.time() + random.randint(45, 90)

        print(f"Clima: {self.estado_anterior} → {self.estado_actual}"
              f" (intensidad: {self.intensidad_actual:.2f})")

    def obtener_info_clima(self):
        """Retorna información del clima para mostrar en pantalla."""
        return {
            'estado': self.estado_actual,
            'intensidad': self.intensidad_actual,
            'multiplicador': self.obtener_multiplicador_actual(),
            'en_transicion': self.en_transicion,
            'tiempo_hasta_cambio': max(0, self.tiempo_cambio - time.time()),
            'consumo_extra': self.obtener_consumo_resistencia_extra()
        }

    def traducir_clima(self, estado):
        """Traduce los climas para mostrarlos al jugador."""
        traducciones = {
            'clear': 'Despejado ',
            'clouds': 'Nublado ',
            'rain_light': 'Llovizna ',
            'rain': 'Lluvia ',
            'storm': 'Tormenta ',
            'fog': 'Niebla ',
            'wind': 'Viento ',
            'heat': 'Calor ',
            'cold': 'Frío '
        }
        return traducciones.get(estado, f"{estado} ")

    def obtener_efecto_descripcion(self):
        """Retorna descripción del efecto actual del clima."""
        mult = self.obtener_multiplicador_actual()
        consumo = self.obtener_consumo_resistencia_extra()

        if mult >= 0.95 and consumo <= 0.05:
            return "Condiciones ideales"
        elif mult >= 0.85:
            return "Condiciones buenas"
        elif mult >= 0.75:
            return "Condiciones difíciles"
        else:
            return "Condiciones extremas"

    def debug_info(self):
        """Información de debug sobre el sistema de clima."""
        return {
            'estados_disponibles': self.estados_disponibles,
            'matriz_size': len(self.matriz_transicion),
            'estado_actual': self.estado_actual,
            'transiciones_disponibles':
                list(self.matriz_transicion.get(self.estado_actual, {})
                     .get('estados', [])),
            'api_conectada': self.api is not None
        }
