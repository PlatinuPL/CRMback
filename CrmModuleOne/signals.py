import logging
logger = logging.getLogger(__name__)

print("SYGNAŁY CrmModuleOne ZAŁADOWANE")  # dodaj to na początku pliku

from django.db.models.signals import pre_save
from django.dispatch import receiver
from CrmModuleOne.models import Parcel
from CrmModuleOne.utils import get_coordinates

@receiver(pre_save, sender=Parcel)
def set_coordinates(sender, instance, **kwargs):
    print("PRE_SAVE dla Parcel ODPALONY")
    if not instance.latitude or not instance.longitude:
        lat, lon = get_coordinates(
            instance.voivodeship,
            instance.county,
            instance.town,
            instance.precinct,
            instance.plot_number
        )
        print(f"Koordynaty pobrane: {lat}, {lon}")
        instance.latitude = lat
        instance.longitude = lon
