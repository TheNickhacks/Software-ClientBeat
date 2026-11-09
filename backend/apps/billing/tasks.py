from celery import shared_task
from apps.billing.management.commands.procesar_ciclos_vencidos import ejecutar_barrido_ciclos_vencidos


@shared_task(name='billing.procesar_ciclos_vencidos_diario')
def tarea_procesar_ciclos_vencidos_diario():
    """
    Tarea programada diaria (Celery Beat) para gestionar el período de gracia de 3 días,
    enviar alertas Dunning y suspender cuentas en mora.
    """
    return ejecutar_barrido_ciclos_vencidos()

