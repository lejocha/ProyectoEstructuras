---Proyecto 1 de Estructuras de Datos---
-
Juego: Courier Quest

Integrantes: 

- Justin Briones S.

- Emmanuel Rodriguez P.

- Josué Vargas G.

-Instrucciones de uso-
-
Al ejecutar el código en el Main.py
el juego comenzará directamente, cargan imágenes, la ventana
y la información obtenida de la API.

El personaje es capaz de moverse utilizando las teclas 
de dirección del teclado, también cuenta con otras acciones
que se mostrarán en la parte de abajo a la derecha de la 
pantalla junto con su respectiva tecla para accionar.

Para recoger pedidos y entregarlos el jugador debe
posicionarse en la casilla con la imagen del paquete o
del punto de entrega.

El juego terminará cuando se llegue a la cantidad de dinero
indicada en la meta (victoria), cuando se acabe el tiempo 
(derrota) o cuando la reputación baje del 20%(derrota).

-Estructuras de datos utilizadas-
-
Se hizo uso de heapq para hacer manejo de los pedidos
que el jugador se encarga de recoger y que estos se vayan
ordenando por orden de prioridad. 
Al recoger los pedidos estos son guardados con ayuda de
colas (deque) y el método sorted(), también se agregó
una segunda opción para que se ordenaran los pedidos por
dinero haciendo uso del "Insertion sort".

Para el manejo de pedidos con el heapq obtenemos una
complejidad de O(n log n) sin importar el orden en el
que aparezcan los pedidos con diferentes prioridades.

Para el ordenamiento "Insertion sort" al ordenar los
pedidos con ayuda de una cola estos reciben una complejidad
de O(n) en el mejor de los casos, es decir si los pedidos
se van recogiendo en un orden en el que no haya necesidad de
ordenarlos no se hacen intercambios y solo habrán 
comparaciones, sin embargo en el caso promedio y en el
peor de los casos (desordenados según dinero), habrá una
complejidad de O(n^2).


