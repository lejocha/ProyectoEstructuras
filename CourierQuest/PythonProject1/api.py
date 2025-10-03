"""
api.py.

Se cargan las URL de los API con ayuda de la librería "requests
y se crean variables con json para que los datos sean posibles
de utilizar localmente para que el juego sea utilizado en modo offline.

Se obtiene el mapa, el clima y los pedidos de la API.
"""

import requests
import json

# URLs de la API
URL_MAPA = \
    ("https://tigerds-api.kindflower-ccaf48b6"
     ".eastus.azurecontainerapps.io/city/map")
URL_PEDIDOS = \
    ("https://tigerds-api.kindflower-ccaf48b6"
     ".eastus.azurecontainerapps.io/city/jobs")
URL_CLIMA = \
    ("https://tigerds-api.kindflower-ccaf48b6"
     ".eastus.azurecontainerapps.io/city/weather")


LOCAL_MAPA = "data/ciudad.json"
LOCAL_PEDIDOS = "data/pedidos.json"
LOCAL_CLIMA = "data/clima.json"


def obtener_mapa():
    """Se obtiene el mapa mediante el URL de la API."""
    try:
        resp = requests.get(URL_MAPA, timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except requests.exceptions.RequestException:
        print("No se pudo conectar a la API. Usando mapa local...")
    with open(LOCAL_MAPA, "r") as f:
        return json.load(f)


def obtener_pedidos():
    """Se obtienen los pedidos mediante el URL de la API."""
    try:
        resp = requests.get(URL_PEDIDOS, timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except requests.exceptions.RequestException:
        print("No se pudo conectar a la API. Usando pedidos locales...")
    with open(LOCAL_PEDIDOS, "r") as f:
        return json.load(f)


def obtener_clima():
    """Se obtienen el clima mediante el URL de la API."""
    try:
        resp = requests.get(URL_CLIMA, timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except requests.exceptions.RequestException:
        print("No se pudo conectar a la API. Usando clima local...")
    with open(LOCAL_CLIMA, "r") as f:
        return json.load(f)
