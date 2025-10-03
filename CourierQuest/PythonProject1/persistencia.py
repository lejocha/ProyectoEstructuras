"""
persistencia.py.

Maneja la persistencia del juego para
guardar y cargar datos y también maneja
un registro de los movimientos del jugador
para volver a un estado anterior.
"""

import pickle
import json
import os
import time
from datetime import datetime


class SistemaPersistencia:
    """Se encarga de manejar la persistencia.

    Tanto el guardado y cargar los datos del juego,
    incluyendo estados guardados y puntajes.
    """

    def __init__(self):
        """Crea las carpetas.

        Donde se guarardaran
        los archivos del juego.
        """
        self.carpeta_saves = "saves"
        self.carpeta_data = "data"
        self.archivo_puntajes = "data/puntajes.json"
        self.crear_carpetas()

    def crear_carpetas(self):
        """Crea las carpetas si no existen."""
        for carpeta in [self.carpeta_saves, self.carpeta_data]:
            if not os.path.exists(carpeta):
                os.makedirs(carpeta)

    def guardar_juego(self, estado_juego, slot=1):
        """Guarda el estado del juego en un archivo."""
        archivo = f"{self.carpeta_saves}/slot{slot}.sav"

        try:
            datos_guardado = {
                'timestamp': time.time(),
                'fecha_guardado': datetime.now().isoformat(),
                'version': '1.0',
                'estado_juego': estado_juego
            }

            with open(archivo, 'wb') as f:
                pickle.dump(datos_guardado, f)

            print(f"Juego guardado exitosamente en {archivo}")
            return True

        except Exception as e:
            print(f"Error al guardar juego: {e}")
            return False

    def cargar_juego(self, slot=1):
        """Carga el estado del juego desde un archivo."""
        archivo = f"{self.carpeta_saves}/slot{slot}.sav"

        if not os.path.exists(archivo):
            print(f"No existe guardado en slot {slot}")
            return None

        try:
            with open(archivo, 'rb') as f:
                datos = pickle.load(f)

            print(f"Juego cargado desde {archivo}")
            print(f"Guardado el: {datos['fecha_guardado']}")
            return datos['estado_juego']

        except Exception as e:
            print(f"Error al cargar juego: {e}")
            return None

    def listar_guardados(self):
        """Retorna una lista con partidas guardadas."""
        guardados = []

        for i in range(1, 6):  # Slots 1-5
            archivo = f"{self.carpeta_saves}/slot{i}.sav"
            if os.path.exists(archivo):
                try:
                    with open(archivo, 'rb') as f:
                        datos = pickle.load(f)

                    guardados.append({
                        'slot': i,
                        'fecha': datos['fecha_guardado'],
                        'timestamp': datos['timestamp']
                    })
                except (pickle.UnpicklingError, EOFError, OSError) as e:
                    print(f"Error al leer {archivo}: {e}")
                    continue

        return guardados

    def guardar_puntaje(
            self, nombre_jugador, puntaje_final,
            datos_extra=None):
        """Guarda un puntaje al archivo .json."""
        nuevo_puntaje = {
            'nombre': nombre_jugador,
            'puntaje': puntaje_final,
            'fecha': datetime.now().isoformat(),
            'timestamp': time.time()
        }

        if datos_extra:
            nuevo_puntaje.update(datos_extra)

        puntajes = self.cargar_puntajes()

        puntajes.append(nuevo_puntaje)

        puntajes.sort(key=lambda x: x['puntaje'], reverse=True)

        puntajes = puntajes[:10]

        try:
            with open(self.archivo_puntajes, 'w', encoding='utf-8') as f:
                json.dump(puntajes, f, indent=2, ensure_ascii=False)

            print(f"Puntaje guardado: {puntaje_final} puntos")
            return True

        except Exception as e:
            print(f"Error al guardar puntaje: {e}")
            return False

    def cargar_puntajes(self):
        """Lee puntajes.json y devuelve puntajes guardados."""
        if not os.path.exists(self.archivo_puntajes):
            return []

        try:
            with open(self.archivo_puntajes, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar puntajes: {e}")
            return []

    def obtener_mejor_puntaje(self):
        """Devuelve el puntaje más alto en el archivo."""
        puntajes = self.cargar_puntajes()
        if puntajes:
            return puntajes[0]['puntaje']
        return 0

    def calcular_puntaje_final(self, jugador, tiempo_total,
                               duracion_objetivo, meta_ingresos):
        """Calcula el puntaje final del jugador."""
        score_base = jugador.puntaje

        if jugador.reputacion >= 90:
            score_base = int(score_base * 1.05)

        bonus_tiempo = 0
        tiempo_restante_porcentaje =\
            (duracion_objetivo - tiempo_total) / duracion_objetivo
        if tiempo_restante_porcentaje > 0.2:
            bonus_tiempo = int(score_base * 0.1 * tiempo_restante_porcentaje)

        bonus_meta = 0
        if jugador.puntaje >= meta_ingresos:
            bonus_meta = int(meta_ingresos * 0.15)

        penalizaciones = 0

        puntaje_final = score_base + bonus_tiempo + bonus_meta - penalizaciones

        return {
            'puntaje_final': puntaje_final,
            'desglose': {
                'base': score_base,
                'bonus_tiempo': bonus_tiempo,
                'bonus_meta': bonus_meta,
                'penalizaciones': penalizaciones
            }
        }


class HistorialMovimientos:
    """Maneja un registro de los movimientos del jugador."""

    def __init__(self, max_pasos=50):
        """Construye un historial vacío."""
        self.historial = []
        self.max_pasos = max_pasos

    def guardar_estado(
            self, jugador, pedidos_activos, tiempo):
        """Guarda el estado actual del jugador."""
        estado = {
            'jugador_x': jugador.x,
            'jugador_y': jugador.y,
            'resistencia': jugador.resistencia,
            'puntaje': jugador.puntaje,
            'reputacion': jugador.reputacion,
            'inventario': list(jugador.inventario),
            'pedidos_activos': pedidos_activos.copy(),
            'timestamp': tiempo
        }

        self.historial.append(estado)

        if len(self.historial) > self.max_pasos:
            self.historial.pop(0)

    def deshacer(self, jugador, pedidos_activos):
        """Revierte al estado anterior si hay al menos 2."""
        if len(self.historial) < 2:
            return False

        self.historial.pop()
        estado_anterior = self.historial[-1]

        jugador.x = estado_anterior['jugador_x']
        jugador.y = estado_anterior['jugador_y']
        jugador.resistencia = estado_anterior['resistencia']
        jugador.puntaje = estado_anterior['puntaje']
        jugador.reputacion = estado_anterior['reputacion']
        jugador.inventario = estado_anterior['inventario'].copy()

        pedidos_activos.clear()
        pedidos_activos.extend(estado_anterior['pedidos_activos'])

        print("Movimiento deshecho")
        return True

    def puede_deshacer(self):
        """Devuelve true si hay 2 estados guardados."""
        return len(self.historial) >= 2
