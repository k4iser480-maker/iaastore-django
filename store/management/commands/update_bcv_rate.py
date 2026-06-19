from django.core.management.base import BaseCommand
from store.models import ExchangeRate
from pyDolarVenezuela.pages import BCV

class Command(BaseCommand):
    help = 'Actualiza la tasa de cambio del BCV usando pyDolarVenezuela'

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando extracción de la tasa BCV...')
        try:
            from pyDolarVenezuela import Monitor
            from pyDolarVenezuela.pages import BCV
            
            monitor = Monitor(BCV, 'USD')
            dolar = monitor.get_value_monitors('usd')
            
            if dolar and hasattr(dolar, 'price'):
                price = dolar.price
                # Actualizar o crear el registro
                rate_obj, created = ExchangeRate.objects.update_or_create(
                    currency='USD',
                    defaults={'rate': price}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Creada tasa BCV inicial: {price} Bs'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Tasa BCV actualizada exitosamente a: {price} Bs'))
            else:
                self.stdout.write(self.style.ERROR('No se pudo encontrar el precio del USD en los datos del BCV.'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al obtener la tasa BCV: {str(e)}'))
