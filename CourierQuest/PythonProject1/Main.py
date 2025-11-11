
import pygame
import time
import api
from jugador import Jugador
from jugadorCPU import JugadorCPU
from mapa import cargar_mapa, dibujar_mapa
from pedidos import reubicar_pedidos, asignar_posicion_aleatoria
from clases import ColaPedidos, Pedido
from clima import SistemaClima
from persistencia import SistemaPersistencia, HistorialMovimientos


pygame.init()
clock = pygame.time.Clock()

# --- Configuración ---
tile_size = 60
view_width, view_height = 13, 13
screen = pygame.display.set_mode((view_width * tile_size,
                                  view_height * tile_size))
pygame.display.set_caption("Courier Quest - Modo CPU")

colors = {"C": (200, 200, 200), "B": (0, 0, 0), "P": (0, 200, 0)}

# --- Cargar imágenes del jugador humano ---
player_image = pygame.image.load("assets/repartidor.png").convert_alpha()
player_image = pygame.transform.scale(player_image, (tile_size, tile_size))
player_imagen_flip = pygame.transform.flip(player_image, True, False)
direccion_der = True

# --- Cargar imágenes del CPU ---
cpu_image = pygame.image.load("assets/repartidor.png").convert_alpha()
# Colorear de manera diferente (rojo para CPU)
cpu_image = pygame.transform.scale(cpu_image, (tile_size, tile_size))
# Aplicar tinte rojo al CPU
cpu_image_colored = cpu_image.copy()
# Crear superficie roja semi-transparente
red_tint = pygame.Surface((tile_size, tile_size))
red_tint.fill((255, 50, 50))
red_tint.set_alpha(100)
cpu_image_colored.blit(red_tint, (0, 0), special_flags=pygame.BLEND_ADD)

# --- Cargar imágenes de pedidos ---
pickup_image = pygame.image.load("assets/pedido_pickup.png").convert_alpha()
pickup_image = pygame.transform.scale(pickup_image, (tile_size, tile_size))
dropoff_normal_image = pygame.image.load(
    "assets/pedido_dropoff_normal.png").convert_alpha()
dropoff_normal_image = pygame.transform.scale(
    dropoff_normal_image, (tile_size, tile_size))
dropoff_prioridad_image = pygame.image.load(
    "assets/pedido_dropoff_prioridad.png").convert_alpha()
dropoff_prioridad_image = pygame.transform.scale(
    dropoff_prioridad_image, (tile_size, tile_size))

# --- Cargar imágenes del ambiente ---
calle_image = pygame.image.load("assets/Calle.jpg").convert()
calle_image = pygame.transform.scale(calle_image, (tile_size, tile_size))
parque_image = pygame.image.load("assets/Parque.jpg").convert()
parque_image = pygame.transform.scale(parque_image, (tile_size, tile_size))
edificio_image = pygame.image.load("assets/Edificio.jpg").convert()
edificio_image = pygame.transform.scale(edificio_image, (tile_size, tile_size))

imagenes_tiles = {
    "C": calle_image,
    "P": parque_image,
    "B": edificio_image
}

# --- Inicializar sistemas ---
sistema_clima = SistemaClima(api)
sistema_persistencia = SistemaPersistencia()
historial_movimientos = HistorialMovimientos()

# --- Cargar mapa y pedidos ---
tiles = cargar_mapa(api)
mapa_data = api.obtener_mapa()["data"]
meta_ingresos = 5500

pedidos_data = api.obtener_pedidos()["data"]
reubicar_pedidos(pedidos_data, tiles)
cola_pedidos = ColaPedidos(pedidos_data)

# --- Crear jugadores ---
jugador = Jugador(0, 0)
map_width, map_height = len(tiles[0]), len(tiles)

# Menú de selección de dificultad
def seleccionar_dificultad():
    """Muestra menú para seleccionar dificultad del CPU."""
    font_titulo = pygame.font.SysFont(None, 48)
    font_opcion = pygame.font.SysFont(None, 32)

    seleccionando = True
    dificultad_seleccionada = None

    while seleccionando:
        screen.fill((30, 30, 50))

        # Título
        titulo = font_titulo.render(
            "Selecciona Dificultad CPU", True, (255, 255, 255))
        titulo_rect = titulo.get_rect(
            center=(screen.get_width() // 2, 100))
        screen.blit(titulo, titulo_rect)

        # Opciones
        opciones = [
            ("1 - FÁCIL (Aleatorio)", 'facil', 200),
            ("2 - MEDIO (Greedy)", 'medio', 270),
            ("3 - DIFÍCIL (A*)", 'dificil', 340),
            ("", None, 410),
            ("ESC - Sin CPU", None, 480)
        ]

        for texto, dif, y_pos in opciones:
            if texto:
                color = (100, 255, 100) if dif else (200, 200, 200)
                opcion = font_opcion.render(texto, True, color)
                opcion_rect = opcion.get_rect(
                    center=(screen.get_width() // 2, y_pos))
                screen.blit(opcion, opcion_rect)

        # Descripción de dificultades
        descripciones = [
            "Fácil: El CPU se mueve aleatoriamente",
            "Medio: Evalúa movimientos con heurísticas",
            "Difícil: Usa algoritmos de ruta óptima"
        ]

        font_small = pygame.font.SysFont(None, 20)
        for i, desc in enumerate(descripciones):
            texto = font_small.render(desc, True, (180, 180, 180))
            screen.blit(texto, (50, 550 + i * 25))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    dificultad_seleccionada = 'facil'
                    seleccionando = False
                elif event.key == pygame.K_2:
                    dificultad_seleccionada = 'medio'
                    seleccionando = False
                elif event.key == pygame.K_3:
                    dificultad_seleccionada = 'dificil'
                    seleccionando = False
                elif event.key == pygame.K_ESCAPE:
                    dificultad_seleccionada = None
                    seleccionando = False

    return dificultad_seleccionada

# Seleccionar dificultad
dificultad_cpu = seleccionar_dificultad()

if dificultad_cpu is None:
    print("Jugando sin CPU")
    jugador_cpu = None
else:
    # Crear CPU en posición opuesta del mapa
    cpu_x = map_width - 1
    cpu_y = map_height - 1
    # Asegurar que no sea edificio
    while tiles[cpu_y][cpu_x] == 'B':
        cpu_x -= 1
        if cpu_x < 0:
            cpu_x = map_width - 1
            cpu_y -= 1

    jugador_cpu = JugadorCPU(cpu_x, cpu_y, dificultad=dificultad_cpu)
    print(f"CPU creado con dificultad: {dificultad_cpu}")

# --- Variables de control ---
ultimo_check = time.time()
check_interval = 15
pedidos_activos = []
pedidos_vistos = set()
ultimo_limpieza_vistos = time.time()
intervalo_limpieza = 20

ultimo_liberado = 0
liberar_interval = 5

tiempo_inicio = time.time()
duracion = 10 * 60

juego_terminado = False
ganador = None
puntaje_calculado_humano = None
puntaje_calculado_cpu = None

mostrar_inventario_detallado = False
mostrar_estadisticas = False
ordendar_inventario = False


def mostrar_pantalla_final(ganador_final, puntaje_humano, puntaje_cpu_info):
    """Muestra pantalla final con resultados de ambos jugadores."""
    screen.fill((0, 0, 0))
    font_titulo = pygame.font.SysFont(None, 48)
    font_texto = pygame.font.SysFont(None, 24)

    if ganador_final == 'humano':
        titulo = font_titulo.render("¡VICTORIA HUMANO!", True, (0, 255, 0))
    elif ganador_final == 'cpu':
        titulo = font_titulo.render("¡VICTORIA CPU!", True, (255, 100, 100))
    else:
        titulo = font_titulo.render("JUEGO TERMINADO", True, (255, 255, 0))

    titulo_rect = titulo.get_rect(center=(screen.get_width() // 2, 50))
    screen.blit(titulo, titulo_rect)

    # Resultados del jugador humano
    y_offset = 120
    textos_humano = [
        f"=== JUGADOR HUMANO ===",
        f"Puntaje: {puntaje_humano['puntaje_final']}",
        f"Entregas: {jugador.entregas_completadas}",
        f"Dinero: ${jugador.puntaje}",
        f"Reputación: {jugador.reputacion}",
        ""
    ]

    for texto in textos_humano:
        rendered = font_texto.render(texto, True, (100, 255, 100))
        rendered_rect = rendered.get_rect(
            center=(screen.get_width() // 2, y_offset))
        screen.blit(rendered, rendered_rect)
        y_offset += 30

    # Resultados del CPU (si existe)
    if jugador_cpu and puntaje_cpu_info:
        textos_cpu = [
            f"=== JUGADOR CPU ({jugador_cpu.dificultad.upper()}) ===",
            f"Puntaje: {puntaje_cpu_info['puntaje_final']}",
            f"Entregas: {jugador_cpu.entregas_completadas}",
            f"Dinero: ${jugador_cpu.puntaje}",
            f"Reputación: {jugador_cpu.reputacion}",
            ""
        ]

        for texto in textos_cpu:
            rendered = font_texto.render(texto, True, (255, 100, 100))
            rendered_rect = rendered.get_rect(
                center=(screen.get_width() // 2, y_offset))
            screen.blit(rendered, rendered_rect)
            y_offset += 30

    # Mensaje final
    final_msg = font_texto.render(
        "Presiona ESC para salir", True, (255, 255, 255))
    final_rect = final_msg.get_rect(
        center=(screen.get_width() // 2, y_offset + 20))
    screen.blit(final_msg, final_rect)


def mostrar_hud_mejorado():
    """Muestra HUD con información de ambos jugadores."""
    font = pygame.font.SysFont(None, 22)
    font_small = pygame.font.SysFont(None, 18)

    # Información del clima
    info_clima = sistema_clima.obtener_info_clima()
    clima_texto = sistema_clima.traducir_clima(info_clima['estado'])
    clima_color = (255, 255, 255)

    if info_clima['estado'] in ['storm', 'rain']:
        clima_color = (255, 100, 100)
    elif info_clima['estado'] in ['heat', 'cold']:
        clima_color = (255, 200, 100)

    screen.blit(font.render(
        f"Clima: {clima_texto}", True, clima_color), (10, 10))

    # Meta e información del humano
    y_pos = 40
    screen.blit(font.render(
        f"HUMANO - ${jugador.puntaje}/{meta_ingresos}",
        True, (100, 255, 100)), (10, y_pos))
    screen.blit(font_small.render(
        f"Rep: {jugador.reputacion} | Entregas: {jugador.entregas_completadas}",
        True, (180, 255, 180)), (10, y_pos + 20))

    # Información del CPU (si existe)
    if jugador_cpu:
        y_pos += 50
        screen.blit(font.render(
            f"CPU ({jugador_cpu.dificultad.upper()}) - ${jugador_cpu.puntaje}",
            True, (255, 100, 100)), (10, y_pos))
        screen.blit(font_small.render(
            f"Rep: {jugador_cpu.reputacion} | Entregas: {jugador_cpu.entregas_completadas}",
            True, (255, 180, 180)), (10, y_pos + 20))


def mostrar_inventario_detallado_ui():
    """Muestra inventario del jugador humano."""
    if not mostrar_inventario_detallado or not jugador.inventario:
        return

    overlay = pygame.Surface((400, 300))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (200, 100))

    font = pygame.font.SysFont(None, 20)
    font_titulo = pygame.font.SysFont(None, 24)

    titulo = font_titulo.render("INVENTARIO", True, (255, 255, 255))
    screen.blit(titulo, (210, 110))

    inventario_ordenado = jugador.obtener_inventario_ordenado('prioridad')
    y_offset = 140

    for i, pedido in enumerate(inventario_ordenado[:8]):
        color = (255, 100, 100) if pedido.priority >= 1 else (255, 255, 255)
        texto = (f"{i + 1}. Peso:{pedido.weight} "
                 f"Pago:${pedido.payout} Prio:{pedido.priority}")

        tiempo_transcurrido = time.time() - getattr(
            pedido, 'tiempo_recogido', time.time())
        if tiempo_transcurrido > 20:
            texto += " [TARDE]"
            color = (255, 200, 100)

        rendered = font.render(texto, True, color)
        screen.blit(rendered, (210, y_offset + i * 20))


# --- Bucle principal ---
running = True
while running:
    ahora = time.time()
    tiempo_transcurrido = ahora - tiempo_inicio

    # Actualizar sistemas
    sistema_clima.actualizar()
    jugador.recuperar()

    # Actualizar CPU
    if jugador_cpu:
        clima_mult = sistema_clima.obtener_multiplicador_actual()
        consumo_clima = sistema_clima.obtener_consumo_resistencia_extra()
        jugador_cpu.actualizar(
            pedidos_activos, tiles, clima_mult, consumo_clima)

    # Condiciones de finalización
    if not juego_terminado:
        # Victoria por meta
        if jugador.puntaje >= meta_ingresos:
            juego_terminado = True
            ganador = 'humano'
            tiempo_final = tiempo_transcurrido
        elif jugador_cpu and jugador_cpu.puntaje >= meta_ingresos:
            juego_terminado = True
            ganador = 'cpu'
            tiempo_final = tiempo_transcurrido
        # Derrota por tiempo
        elif tiempo_transcurrido >= duracion:
            juego_terminado = True
            # Ganador por más dinero
            if jugador_cpu:
                ganador = 'humano' if jugador.puntaje > jugador_cpu.puntaje else 'cpu'
            else:
                ganador = 'humano'
            tiempo_final = duracion
        # Derrota por reputación
        elif jugador.reputacion <= 20:
            juego_terminado = True
            ganador = 'cpu' if jugador_cpu else None
            tiempo_final = tiempo_transcurrido
        elif jugador_cpu and jugador_cpu.reputacion <= 20:
            juego_terminado = True
            ganador = 'humano'
            tiempo_final = tiempo_transcurrido

        # Calcular puntajes finales
        if juego_terminado and puntaje_calculado_humano is None:
            puntaje_calculado_humano = sistema_persistencia.calcular_puntaje_final(
                jugador, tiempo_final, duracion, meta_ingresos)

            if jugador_cpu:
                puntaje_calculado_cpu = sistema_persistencia.calcular_puntaje_final(
                    jugador_cpu, tiempo_final, duracion, meta_ingresos)

    # Pantalla final
    if juego_terminado:
        mostrar_pantalla_final(
            ganador, puntaje_calculado_humano, puntaje_calculado_cpu)
        pygame.display.flip()

        for event in pygame.event.get():
            if (event.type == pygame.QUIT or
                    (event.type == pygame.KEYDOWN and
                     event.key == pygame.K_ESCAPE)):
                running = False
        continue

    # Limpiar pedidos vistos
    if ahora - ultimo_limpieza_vistos >= intervalo_limpieza:
        ids_activos = set()
        for ped in pedidos_activos:
            ids_activos.add(getattr(ped, 'id', None))
        for ped in jugador.inventario:
            ids_activos.add(getattr(ped, 'id', None))
        if jugador_cpu:
            for ped in jugador_cpu.inventario:
                ids_activos.add(getattr(ped, 'id', None))

        pedidos_vistos = ids_activos
        ultimo_limpieza_vistos = ahora

    # Chequear nuevos pedidos
    if ahora - ultimo_check >= check_interval:
        try:
            resp = api.obtener_pedidos()
            nuevos_pedidos_data = (resp.get("data", [])
                                   if isinstance(resp, dict) else resp)
        except Exception as e:
            print("Error al obtener pedidos:", e)
            nuevos_pedidos_data = []

        for p in nuevos_pedidos_data:
            pedido_id = p.get("id", f"{p['pickup']}-{p['dropoff']}")

            if pedido_id not in pedidos_vistos:
                pedidos_vistos.add(pedido_id)

                ocupadas = set()
                for ped in pedidos_activos:
                    ocupadas.add(tuple(ped.pickup))
                    ocupadas.add(tuple(ped.dropoff))
                for ped in list(jugador.inventario):
                    ocupadas.add(tuple(ped.pickup))
                    ocupadas.add(tuple(ped.dropoff))
                if jugador_cpu:
                    for ped in list(jugador_cpu.inventario):
                        ocupadas.add(tuple(ped.pickup))
                        ocupadas.add(tuple(ped.dropoff))

                ocupadas.add((jugador.x, jugador.y))
                if jugador_cpu:
                    ocupadas.add((jugador_cpu.x, jugador_cpu.y))

                pickup_pos = asignar_posicion_aleatoria(
                    tiles, ocupadas, separacion=4)
                if pickup_pos:
                    p["pickup"] = pickup_pos
                    ocupadas.add(tuple(pickup_pos))
                else:
                    continue

                dropoff_pos = asignar_posicion_aleatoria(
                    tiles, ocupadas, separacion=4)
                if dropoff_pos:
                    p["dropoff"] = dropoff_pos
                else:
                    continue

                nuevo_pedido = Pedido(
                    p["pickup"], p["dropoff"],
                    p.get("weight", 1),
                    p.get("priority", 0),
                    p.get("payout", 100))
                nuevo_pedido.id = pedido_id

                cola_pedidos.agregar_pedido(nuevo_pedido)

        ultimo_check = ahora

    # Liberar pedidos
    if len(pedidos_activos) < 5 and ahora - ultimo_liberado >= liberar_interval:
        pedido = cola_pedidos.obtener_siguiente()
        if pedido:
            pedidos_activos.append(pedido)
            ultimo_liberado = ahora

    # Eventos del jugador humano
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            dx = dy = 0

            if event.key == pygame.K_LEFT:
                dx = -1
                direccion_der = False
            elif event.key == pygame.K_RIGHT:
                dx = 1
                direccion_der = True
            elif event.key == pygame.K_UP:
                dy = -1
            elif event.key == pygame.K_DOWN:
                dy = 1
            elif event.key == pygame.K_q:
                jugador.cancelar_ultimo_pedido()
            elif event.key == pygame.K_i:
                mostrar_inventario_detallado = not mostrar_inventario_detallado
            elif event.key == pygame.K_t:
                mostrar_estadisticas = not mostrar_estadisticas

            if dx != 0 or dy != 0:
                clima_mult = sistema_clima.obtener_multiplicador_actual()
                consumo_clima = sistema_clima.obtener_consumo_resistencia_extra()
                jugador.mover(dx, dy, tiles, clima_mult, consumo_clima)

    # Recoger pedidos (humano)
    for pedido in list(pedidos_activos):
        if [jugador.x, jugador.y] == pedido.pickup:
            if jugador.recoger_pedido(pedido):
                pedidos_activos.remove(pedido)

    # Entregar pedidos (humano)
    jugador.entregar_pedido()

    # Renderizado
    cam_x = max(0, min(jugador.x - view_width // 2,
                       map_width - view_width))
    cam_y = max(0, min(jugador.y - view_height // 2,
                       map_height - view_height))

    screen.fill((255, 255, 255))
    dibujar_mapa(screen, tiles, colors, cam_x, cam_y,
                 tile_size, view_width, view_height, imagenes_tiles)

    # Pedidos activos
    for pedido in pedidos_activos:
        px, py = pedido.pickup
        if (cam_x <= px < cam_x + view_width and
                cam_y <= py < cam_y + view_height):
            screen.blit(pickup_image,
                        ((px - cam_x) * tile_size,
                         (py - cam_y) * tile_size))

    # Dropoffs (ambos jugadores)
    for pedido in list(jugador.inventario) + (list(jugador_cpu.inventario)
                                               if jugador_cpu else []):
        dx, dy = pedido.dropoff
        if (cam_x <= dx < cam_x + view_width and
                cam_y <= dy < cam_y + view_height):
            imagen = (dropoff_prioridad_image if pedido.priority >= 1
                      else dropoff_normal_image)
            screen.blit(imagen,
                        ((dx - cam_x) * tile_size,
                         (dy - cam_y) * tile_size))

    # CPU
    if jugador_cpu:
        cpu_x_screen = jugador_cpu.x
        cpu_y_screen = jugador_cpu.y
        if (cam_x <= cpu_x_screen < cam_x + view_width and
                cam_y <= cpu_y_screen < cam_y + view_height):
            screen.blit(cpu_image_colored,
                        ((cpu_x_screen - cam_x) * tile_size,
                         (cpu_y_screen - cam_y) * tile_size))

    # Jugador humano
    if direccion_der:
        screen.blit(player_image,
                    ((jugador.x - cam_x) * tile_size,
                     (jugador.y - cam_y) * tile_size))
    else:
        screen.blit(player_imagen_flip,
                    ((jugador.x - cam_x) * tile_size,
                     (jugador.y - cam_y) * tile_size))

    # UI
    mostrar_hud_mejorado()

    # Barra de resistencia (humano)
    font = pygame.font.SysFont(None, 20)
    ancho_barra = 150
    alto_barra = 15
    x_barra = 10
    y_barra = screen.get_height() - 80

    porcentaje = max(0, jugador.resistencia / jugador.max_resistencia)
    ancho_actual = int(ancho_barra * porcentaje)
    color_barra = ((0, 255, 0) if porcentaje > 0.3
                   else (255, 255, 0) if porcentaje > 0.1
                   else (255, 0, 0))

    pygame.draw.rect(screen, (100, 100, 100),
                     (x_barra, y_barra, ancho_barra, alto_barra))
    pygame.draw.rect(screen, color_barra,
                     (x_barra, y_barra, ancho_actual, alto_barra))
    screen.blit(font.render("Resistencia (H)", True, (0, 0, 0)),
                (x_barra, y_barra - 18))

    # Barra de resistencia (CPU)
    if jugador_cpu:
        y_barra_cpu = y_barra + 25
        porcentaje_cpu = max(0, jugador_cpu.resistencia /
                             jugador_cpu.max_resistencia)
        ancho_actual_cpu = int(ancho_barra * porcentaje_cpu)
        color_barra_cpu = ((255, 100, 100) if porcentaje_cpu > 0.3
                           else (255, 200, 100) if porcentaje_cpu > 0.1
                           else (255, 0, 0))

        pygame.draw.rect(screen, (100, 100, 100),
                         (x_barra, y_barra_cpu, ancho_barra, alto_barra))
        pygame.draw.rect(screen, color_barra_cpu,
                         (x_barra, y_barra_cpu, ancho_actual_cpu, alto_barra))
        screen.blit(font.render("Resistencia (CPU)", True, (0, 0, 0)),
                    (x_barra, y_barra_cpu - 18))

    # Cronómetro
    tiempo_restante = max(0, int(duracion - tiempo_transcurrido))
    minutos = tiempo_restante // 60
    segundos = tiempo_restante % 60
    cronometro_texto = f"{minutos:02d}:{segundos:02d}"
    font_crono = pygame.font.SysFont(None, 36)
    color_tiempo = (255, 0, 0) if tiempo_restante < 60 else (0, 0, 0)
    screen.blit(font_crono.render(cronometro_texto, True, color_tiempo),
                (screen.get_width() - 120, 10))

    mostrar_inventario_detallado_ui()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()