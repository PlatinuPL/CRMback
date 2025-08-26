from CrmModuleOne.models import Parcel
from CrmModuleOne.utils import get_coordinates
import time

updated = 0
skipped = 0

parcels = Parcel.objects.filter(latitude__isnull=True, longitude__isnull=True)

for parcel in parcels:
    lat, lon = get_coordinates(
        voivodeship=parcel.voivodeship,
        county=parcel.county,
        town=parcel.town,
        precinct=parcel.precinct,
        plot_number=parcel.plot_number
    )

    if lat and lon:
        parcel.latitude = lat
        parcel.longitude = lon
        parcel.save()
        updated += 1
        print(f"✅ Zaktualizowano Parcel ID {parcel.id}: {lat}, {lon}")
    else:
        skipped += 1
        print(f"⚠️ Pominięto Parcel ID {parcel.id} – brak współrzędnych")

    time.sleep(1)  # bezpieczny limit

print(f"\n✅ Gotowe: {updated} działek zaktualizowano, {skipped} pominięto.")
