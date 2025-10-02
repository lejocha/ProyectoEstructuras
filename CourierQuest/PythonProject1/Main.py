import pygame
import time
import api
from jugador import Jugador
from mapa import cargar_mapa, dibujar_mapa
from pedidos import reubicar_pedidos
from clases import ColaPedidos, Pedido
from clima import SistemaClima
from persistencia import SistemaPersistencia, HistorialMovimientos

pygame.init()
clock = pygame.time.Clock()

# --- Configuración ---
tile_size = 60
view_width, view_height = 13, 13   #Tamaño original de la ventan 16,16
screen = pygame.display.set_mode((view_width * tile_size, view_height * tile_size))
pygame.display.set_caption("Courier Quest - Mapa")

colors = {"C": (200, 200, 200), "B": (0, 0, 0), "P": (0, 200, 0)}


# --- Cargar imagen del jugador ---
player_image = pygame.image.load("assets/repartidor.png").convert_alpha()
player_image = pygame.transform.scale(player_image, (tile_size, tile_size))
direccionDer = True #La direccion a la que apunta el repartidor
player_imagen_flip = pygame.transform.flip(player_image, True, False)

# --- Cargar imágenes de pedidos y puntos de entrega ---
pickup_image = pygame.image.load("assets/pedido_pickup.png").convert_alpha()
pickup_image = pygame.transform.scale(pickup_image, (tile_size, tile_size))
dropoffNormal_image = pygame.image.load("assets/pedido_dropoff_normal.png").convert_alpha()
dropoffNormal_image = pygame.transform.scale(dropoffNormal_image, (tile_size, tile_size))
dropoffPrioridad_image = pygame.image.load("assets/pedido_dropoff_prioridad.png").convert_alpha()
dropoffPrioridad_image = pygame.transform.scale(dropoffPrioridad_image, (tile_size, tile_size))

# --- Cargar imágenes del ambiente ---
calle_image = pygame.image.load("assets/Calle.jpg").convert()
calle_image = pygame.transform.scale(calle_image, (tile_size, tile_size))
parque_image = pygame.image.load("assets/Parque.jpg").convert()
parque_image = pygame.transform.scale(parque_image, (tile_size, tile_size))
edificio_image = pygame.image.load("assets/Edificio.jpg").convert()
edificio_image = pygame.transform.scale(edificio_image, (tile_size, tile_size))


imagenes_tiles = {  #Se guardan las imagenes
    "C": calle_image,
    "P": parque_image,
    "B": edificio_image
}

# --- Inicializar sistemas ---
sistema_clima = SistemaClima(api)
sistema_persistencia = SistemaPersistencia()
historial_movimientos = HistorialMovimientos()

# --- Cargar mapa y pedidos iniciales ---
tiles = cargar_mapa(api)
mapa_data = api.obtener_mapa()["data"]
meta_ingresos = 5500  # Meta de ingresos del mapa

pedidos_data = api.obtener_pedidos()["data"]
reubicar_pedidos(pedidos_data, tiles)
cola_pedidos = ColaPedidos(pedidos_data)

# --- Crear jugador ---
jugador = Jugador(0, 0)
map_width, map_height = len(tiles[0]), len(tiles)

# --- Variables de control ---
ultimo_check = time.time()
check_interval = 15
pedidos_activos = []

# --- Variables de liberación ---
ultimo_liberado = 0
liberar_interval = 5

# --- Tiempo de juego ---
tiempo_inicio = time.time()
duracion = 10 * 60  # 10 minutos

# --- Variables de estado del juego ---
juego_terminado = False
juego_ganado = False
mostrar_puntajes = False
puntaje_calculado = None

# --- Variables de UI ---
mostrar_inventario_detallado = False
mostrar_estadisticas = False
ordendar_inventario = False


def mostrar_pantalla_final(ganado, puntaje_info):
    """Muestra la pantalla final del juego"""
    screen.fill((0, 0, 0))
    font_titulo = pygame.font.SysFont(None, 48)
    font_texto = pygame.font.SysFont(None, 24)

    if ganado:
        titulo = font_titulo.render("¡VICTORIA!", True, (0, 255, 0))
        subtitulo = font_texto.render(f"Meta alcanzada: ${meta_ingresos}", True, (255, 255, 255))
    else:
        titulo = font_titulo.render("GAME OVER", True, (255, 0, 0))
        if jugador.reputacion <= 20:
            subtitulo = font_texto.render("Reputación muy baja", True, (255, 255, 255))
        else:
            subtitulo = font_texto.render("Tiempo agotado", True, (255, 255, 255))

    # --- Mostrar puntaje final ---
    puntaje_text = font_texto.render(f"Puntaje Final: {puntaje_info['puntaje_final']}", True, (255, 255, 0))
    desglose = puntaje_info['desglose']

    y_offset = 150
    textos = [
        f"Puntaje Base: {desglose['base']}",
        f"Bonus Tiempo: +{desglose['bonus_tiempo']}",
        f"Bonus Meta: +{desglose['bonus_meta']}",
        f"Penalizaciones: -{desglose['penalizaciones']}",
        "",
        f"Entregas: {jugador.entregas_completadas}",
        f"Reputación Final: {jugador.reputacion}",
        f"Dinero Ganado: ${jugador.puntaje}",
        "",
        "Presiona ESC para continuar..."
    ]

    # --- Centrar y mostrar textos ---
    titulo_rect = titulo.get_rect(center=(screen.get_width() // 2, 50))
    subtitulo_rect = subtitulo.get_rect(center=(screen.get_width() // 2, 90))
    puntaje_rect = puntaje_text.get_rect(center=(screen.get_width() // 2, 120))

    screen.blit(titulo, titulo_rect)
    screen.blit(subtitulo, subtitulo_rect)
    screen.blit(puntaje_text, puntaje_rect)

    for i, texto in enumerate(textos):
        if texto:  # No mostrar líneas vacías
            rendered = font_texto.render(texto, True, (255, 255, 255))
            rendered_rect = rendered.get_rect(center=(screen.get_width() // 2, y_offset + i * 25))
            screen.blit(rendered, rendered_rect)

    # --- Interfaz de usuario mejorada ---
def mostrar_hud_mejorado():
    font = pygame.font.SysFont(None, 24)
    font_small = pygame.font.SysFont(None, 18)

    # --- Información del clima ---
    info_clima = sistema_clima.obtener_info_clima()
    clima_texto = sistema_clima.traducir_clima(info_clima['estado'])
    clima_color = (255, 255, 255)

    if info_clima['estado'] in ['storm', 'rain']:
        clima_color = (255, 100, 100)
    elif info_clima['estado'] in ['heat', 'cold']:
        clima_color = (255, 200, 100)

    screen.blit(font.render(f"Clima: {clima_texto}", True, clima_color), (10, 70))
    screen.blit(font_small.render(f"Intensidad: {info_clima['intensidad']:.1f}", True, (200, 200, 200)), (10, 95))

    # --- Meta de ingresos ---
    progreso_meta = (jugador.puntaje / meta_ingresos) * 100
    meta_texto = f"Meta: ${jugador.puntaje}/${meta_ingresos} ({progreso_meta:.1f}%)"
    color_meta = (0, 255, 0) if progreso_meta >= 100 else (255, 255, 255)
    screen.blit(font.render(meta_texto, True, color_meta), (10, 120))

    # --- Inventario resumen ---
    inventario_texto = f"Inventario: {len(jugador.inventario)}/{jugador.capacidad} (Peso: {jugador.peso_total()})"
    screen.blit(font.render(inventario_texto, True, (255, 255, 255)), (10, 145))

    # --- Estado del jugador ---
    estado_resistencia = jugador.obtener_estado_resistencia()
    color_estado = (255, 255, 255)
    if estado_resistencia == "Exhausto":
        color_estado = (255, 0, 0)
    elif estado_resistencia == "Cansado":
        color_estado = (255, 255, 0)

    screen.blit(font_small.render(f"Estado: {estado_resistencia}", True, color_estado), (10, 170))

    # --- Mostrar estadísticas ---
    if mostrar_estadisticas:
        estadisticas = jugador.obtener_estadisticas()
        y = 200  # O la posición que prefieras
        font_estad = pygame.font.SysFont(None, 22)
        for clave, valor in estadisticas.items():
            texto = f"{clave.replace('_', ' ').capitalize()}: {valor:.2f}" if isinstance(valor,
                                                                                         float) else f"{clave.replace('_', ' ').capitalize()}: {valor}"
            texto_render = font_estad.render(texto, True, (0, 0, 0))
            screen.blit(texto_render, (10, y))
            y += 25

    # --- Mostrar inventario ---
def mostrar_inventario_detallado_ui():
    if not mostrar_inventario_detallado or not jugador.inventario:
        return

    # Fondo semi-transparente
    overlay = pygame.Surface((400, 300))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (200, 100))

    font = pygame.font.SysFont(None, 20)
    font_titulo = pygame.font.SysFont(None, 24)

    # Título
    titulo = font_titulo.render("INVENTARIO DETALLADO", True, (255, 255, 255))
    screen.blit(titulo, (210, 110))

    # Lista de pedidos
    inventario_ordenado = jugador.obtener_inventario_ordenado('prioridad')
    y_offset = 140

    for i, pedido in enumerate(inventario_ordenado[:8]):  # Mostrar máximo 8
        color = (255, 100, 100) if pedido.priority >= 1 else (255, 255, 255)

        texto = f"{i + 1}. Peso:{pedido.weight} Pago:${pedido.payout} Prio:{pedido.priority}"
        tiempo_transcurrido = time.time() - getattr(pedido, 'tiempo_recogido', time.time())
        if tiempo_transcurrido > 20:
            texto += " [TARDE]"
            color = (255, 200, 100)

        rendered = font.render(texto, True, color)
        screen.blit(rendered, (210, y_offset + i * 20))

    # Lista de pedidos ordenados por $
    if ordendar_inventario:
            inventario_ordenado = jugador.obtener_inventario_por_plata()
            y_offset = 140
    
            for i, pedido in enumerate(inventario_ordenado[:8]):  # Mostrar máximo 8
                color = (255, 100, 100) if pedido.priority >= 1 else (255, 255, 255)
    
                texto = f"{i + 1}. Peso:{pedido.weight} Pago:${pedido.payout} Prio:{pedido.priority}"
                tiempo_transcurrido = time.time() - getattr(pedido, 'tiempo_recogido', time.time())
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

    # Guardar estado para deshacer (cada 2 segundos para no saturar memoria)
    if int(tiempo_transcurrido) % 2 == 0 and tiempo_transcurrido > 1:
        historial_movimientos.guardar_estado(jugador, pedidos_activos, ahora)

    # Condiciones de finalización del juego
    if not juego_terminado:
        # Victoria por meta alcanzada
        if jugador.puntaje >= meta_ingresos:
            juego_terminado = True
            juego_ganado = True
            tiempo_final = tiempo_transcurrido

        # Derrota por tiempo
        elif tiempo_transcurrido >= duracion:
            juego_terminado = True
            juego_ganado = False
            tiempo_final = duracion

        # Derrota por reputación
        elif jugador.reputacion <= 20:
            juego_terminado = True
            juego_ganado = False
            tiempo_final = tiempo_transcurrido

        # Si el juego acaba de terminar, calcular puntaje
        if juego_terminado and puntaje_calculado is None:
            puntaje_calculado = sistema_persistencia.calcular_puntaje_final(
                jugador, tiempo_final, duracion, meta_ingresos
            )

            # Guardar puntaje
            sistema_persistencia.guardar_puntaje(
                "Jugador",
                puntaje_calculado['puntaje_final'],
                {
                    'tiempo_total': tiempo_final,
                    'entregas_completadas': jugador.entregas_completadas,
                    'reputacion_final': jugador.reputacion,
                    'dinero_ganado': jugador.puntaje,
                    'meta_alcanzada': juego_ganado
                }
            )

    # Si el juego terminó, mostrar pantalla final
    if juego_terminado:
        mostrar_pantalla_final(juego_ganado, puntaje_calculado)
        pygame.display.flip()

        # Esperar a que presione ESC para salir
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
        continue

    # --- Chequear nuevos pedidos (solo si juego activo) ---
    if ahora - ultimo_check >= check_interval:
        try:
            resp = api.obtener_pedidos()
            nuevos_pedidos_data = resp.get("data", []) if isinstance(resp, dict) else resp
        except Exception as e:
            print("Error al obtener pedidos de la API:", e)
            nuevos_pedidos_data = []

        for p in nuevos_pedidos_data:
            existe = any(
                p["pickup"] == ped.pickup and p["dropoff"] == ped.dropoff
                for ped in list(cola_pedidos.cola) + pedidos_activos
            )
            if not existe:
                ocupadas = set()
                for ped in pedidos_activos + list(jugador.inventario):
                    ocupadas.add(tuple(ped.pickup))
                    ocupadas.add(tuple(ped.dropoff))
                ocupadas.add((jugador.x, jugador.y))
                reubicar_pedidos([p], tiles, ocupadas)

                nuevo_pedido = Pedido(
                    p["pickup"], p["dropoff"],
                    p.get("weight", 1),
                    p.get("priority", 0),
                    p.get("payout", 100)
                )
                cola_pedidos.agregar_pedido(nuevo_pedido)
                break
        ultimo_check = ahora

    # --- Liberar pedidos ---
    if len(pedidos_activos) < 5 and ahora - ultimo_liberado >= liberar_interval:
        pedido = cola_pedidos.obtener_siguiente()
        if pedido:
            pedidos_activos.append(pedido)
            ultimo_liberado = ahora

    # --- Eventos ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            dx = dy = 0

            # Movimiento
            if event.key == pygame.K_LEFT:
                dx = -1
                if direccionDer:
                    direccionDer = False
            elif event.key == pygame.K_RIGHT:
                dx = 1
                if not direccionDer:
                    direccionDer = True
            elif event.key == pygame.K_UP:
                dy = -1
            elif event.key == pygame.K_DOWN:
                dy = 1

            # Acciones especiales
            elif event.key == pygame.K_q:
                jugador.cancelar_ultimo_pedido()
            elif event.key == pygame.K_u:  # Deshacer
                historial_movimientos.deshacer(jugador, pedidos_activos)
            elif event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:  # Ctrl+S Guardar
                estado_actual = {
                    'jugador': jugador,
                    'pedidos_activos': pedidos_activos,
                    'cola_pedidos': cola_pedidos,
                    'clima': sistema_clima,
                    'tiempo_inicio': tiempo_inicio,
                    'tiempo_transcurrido': tiempo_transcurrido,
                    'mapa': tiles
                }
                sistema_persistencia.guardar_juego(estado_actual)
            elif event.key == pygame.K_i:  # Mostrar/ocultar inventario detallado
                mostrar_inventario_detallado = not mostrar_inventario_detallado
            elif event.key == pygame.K_t:  # Mostrar/ocultar estadísticas
                mostrar_estadisticas = not mostrar_estadisticas
            elif event.key == pygame.K_o: #Ordenar pedidos por plata
                ordendar_inventario = not ordendar_inventario


            # Realizar movimiento con clima
            if dx != 0 or dy != 0:
                clima_mult = sistema_clima.obtener_multiplicador_actual()
                consumo_clima = sistema_clima.obtener_consumo_resistencia_extra()
                jugador.mover(dx, dy, tiles, clima_mult, consumo_clima)

    # --- Revisar pickups ---
    for pedido in list(pedidos_activos):
        if [jugador.x, jugador.y] == pedido.pickup:
            if jugador.recoger_pedido(pedido):
                pedidos_activos.remove(pedido)

    # --- Revisar dropoffs ---
    entregado = jugador.entregar_pedido()
    if entregado:
        print(f"Pedido entregado - Puntaje: {jugador.puntaje}, Reputación: {jugador.reputacion}")

    # --- Renderizado ---
    # Cámara
    cam_x = max(0, min(jugador.x - view_width // 2, map_width - view_width))
    cam_y = max(0, min(jugador.y - view_height // 2, map_height - view_height))

    # Dibujar mapa y objetos
    screen.fill((255, 255, 255))
    dibujar_mapa(screen, tiles, colors, cam_x, cam_y, tile_size, view_width, view_height, imagenes_tiles)

    # Pedidos activos (pickups)
    for pedido in pedidos_activos:
        px, py = pedido.pickup
        if cam_x <= px < cam_x + view_width and cam_y <= py < cam_y + view_height:
            screen.blit(pickup_image, ((px - cam_x) * tile_size, (py - cam_y) * tile_size)) #Agrega imagen

        # --- Leyenda de prioridades arriba a la izquierda ---
        leyenda_size = 26
        dropoff_prioridad_img_scaled = pygame.transform.scale(dropoffPrioridad_image, (leyenda_size, leyenda_size))
        dropoff_normal_img_scaled = pygame.transform.scale(dropoffNormal_image, (leyenda_size, leyenda_size))

        font = pygame.font.SysFont(None, 26)
        if dropoff_prioridad_img_scaled:
            screen.blit(dropoff_prioridad_img_scaled, (5, 5))
        else:
            pygame.draw.rect(screen, (255, 0, 0), (10, 10, 20, 20))  # Fallback
        screen.blit(font.render("Prioridad máxima", True, (255, 255, 255)), (35, 10))

        if dropoff_normal_img_scaled:
            screen.blit(dropoff_normal_img_scaled, (5, 30))
        else:
            pygame.draw.rect(screen, (255, 105, 180), (10, 40, 20, 20))  # Fallback
        screen.blit(font.render("Prioridad normal", True, (255, 255, 255)), (35, 40))

    # Dropoffs del inventario
    for pedido in jugador.inventario:
        dx, dy = pedido.dropoff
        if cam_x <= dx < cam_x + view_width and cam_y <= dy < cam_y + view_height:
            if pedido.priority >= 1:    #Si es prioridad maxima
                imagen_dropoff = dropoffPrioridad_image
            else:
                imagen_dropoff = dropoffNormal_image

            screen.blit(imagen_dropoff, ((dx - cam_x) * tile_size, (dy - cam_y) * tile_size))

    # Jugador
    # ---Cambia la direccion del jugador ---
    if direccionDer:
        screen.blit(player_image, ((jugador.x - cam_x) * tile_size, (jugador.y - cam_y) * tile_size))
    else:
        screen.blit(player_imagen_flip, ((jugador.x - cam_x) * tile_size, (jugador.y - cam_y) * tile_size))

    # UI
    mostrar_hud_mejorado()

    # Barra de resistencia
    font = pygame.font.SysFont(None, 24)
    ancho_barra = 200
    alto_barra = 20
    x_barra = 10
    y_barra = screen.get_height() - 80

    porcentaje = max(0, jugador.resistencia / jugador.max_resistencia)
    ancho_actual = int(ancho_barra * porcentaje)
    color_barra = (0, 255, 0) if porcentaje > 0.3 else (255, 255, 0) if porcentaje > 0.1 else (255, 0, 0)

    pygame.draw.rect(screen, (100, 100, 100), (x_barra, y_barra, ancho_barra, alto_barra))
    pygame.draw.rect(screen, color_barra, (x_barra, y_barra, ancho_actual, alto_barra))
    screen.blit(font.render("Resistencia", True, (0, 0, 0)), (x_barra, y_barra - 20))

    # Barra de reputación
    y_barra_rep = screen.get_height() - 30
    porcentaje_rep = max(0, jugador.reputacion / 100)
    ancho_actual_rep = int(ancho_barra * porcentaje_rep)
    color_barra_rep = (255, 0, 0) if jugador.reputacion <= 30 else (255, 255, 0) if jugador.reputacion <= 60 else (0, 0,
                                                                                                                   255)

    pygame.draw.rect(screen, (100, 100, 100), (x_barra, y_barra_rep, ancho_barra, alto_barra))
    pygame.draw.rect(screen, color_barra_rep, (x_barra, y_barra_rep, ancho_actual_rep, alto_barra))
    screen.blit(font.render("Reputación", True, (0, 0, 0)), (x_barra, y_barra_rep - 20))

    # Cronómetro
    tiempo_restante = max(0, int(duracion - tiempo_transcurrido))
    minutos = tiempo_restante // 60
    segundos = tiempo_restante % 60
    cronometro_texto = f"Tiempo: {minutos:02d}:{segundos:02d}"
    font_crono = pygame.font.SysFont(None, 36)
    color_tiempo = (255, 0, 0) if tiempo_restante < 60 else (0, 0, 0)
    screen.blit(font_crono.render(cronometro_texto, True, color_tiempo),
                (screen.get_width() - 180, 10))

    # Mostrar mensajes temporales
    if jugador.mensaje and time.time() - jugador.mensaje_tiempo < 3:
        font_msg = pygame.font.SysFont(None, 28)
        aviso = font_msg.render(jugador.mensaje, True, (0, 0, 0))
        screen.blit(aviso, (10, screen.get_height() - 130))

    # Mensaje de energía
    if jugador.bloqueado:
        font_msg = pygame.font.SysFont(None, 36)
        aviso = font_msg.render("¡Sin energía! Descansando...", True, (255, 0, 0))
        screen.blit(aviso, (10, screen.get_height() - 110))

    # --- Controles ---
    font_controles = pygame.font.SysFont(None, 20)
    controles_texto = [
        '"Q" cancelar pedido  "U" deshacer  "I" inventario',
        '"Ctrl+S" guardar  "T" estadísticas "I+O" orden por $'
    ]
    for i, texto in enumerate(controles_texto):
        rendered = font_controles.render(texto, True, (0, 0, 0))
        rect = rendered.get_rect()
        rect.bottomright = (screen.get_width() - 10, screen.get_height() - 30 + i * 20)
        screen.blit(rendered, rect)

    # Overlays opcionales
    mostrar_inventario_detallado_ui()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()