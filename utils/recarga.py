"""
Utilidad: recarga automática de datos al recuperar el foco.

Los módulos leen la BD al abrirse; si otro módulo cambia los datos
mientras la ventana sigue abierta (p. ej. Cobros marca una orden
'pagada' y Órdenes seguía abierta), sus listas quedan desactualizadas.
Este helper vincula el evento <FocusIn> de la ventana para recargar
los datos cuando vuelve al primer plano.
"""

import time


def vincular_recarga_foco(ventana, recargas) -> None:
    """
    Hace que la ventana recargue sus datos al recuperar el foco.

    recargas: lista de funciones sin argumentos que refrescan listas.
    Solo actúa cuando la VENTANA misma recupera el foco (no con cada
    widget interno que gana el foco) y con debounce de 0.5 s contra
    eventos de foco repetidos.
    """
    estado = {"ultima": time.time(), "inicial_pasada": False}

    def al_recuperar_foco(evento=None):
        # Solo el foco de la ventana en sí; ignora cambios internos
        if evento is not None and str(evento.widget) != str(ventana):
            return
        # Ignora el primer FocusIn (creación de la ventana)
        if not estado["inicial_pasada"]:
            estado["inicial_pasada"] = True
            return
        # Debounce: no recargar más de una vez cada 0.5 s
        ahora = time.time()
        if ahora - estado["ultima"] < 0.5:
            return
        estado["ultima"] = ahora
        for recargar in recargas:
            recargar()

    ventana.bind("<FocusIn>", al_recuperar_foco)