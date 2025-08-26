from django.core.management.base import BaseCommand
from CrmModuleOne.models import Parcel, Prelead
import requests
from pyproj import Transformer

class Command(BaseCommand):
    help = 'Pobiera współrzędne działek z GUGiK i zapisuje je do Parcel'

    def handle(self, *args, **kwargs):
        transformer = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
        parcels = Parcel.objects.filter(latitude__isnull=True, longitude__isnull=True)

        for parcel in parcels:
            ident = f"{parcel.voivodeship}|{parcel.county}|{parcel.town}|{parcel.precinct}|{parcel.plot_number}"
            print(f"🔍 Przetwarzam działkę: {ident}")

            try:
                url = f"https://integracja.gugik.gov.pl/cgi-bin/KrajowaIntegracjaEwidencjiGruntow?request=GetParcelById&id={ident}&resultFormat=json"
                response = requests.get(url, timeout=10)
                data = response.json()

                if data.get("status") != "OK" or not data.get("features"):
                    self.stdout.write(self.style.WARNING(f"⚠️  Nie znaleziono danych: {ident}"))
                    continue

                coords = data["features"][0]["geometry"]["coordinates"]
                x, y = coords
                lng, lat = transformer.transform(x, y)

                parcel.latitude = lat
                parcel.longitude = lng
                parcel.save()

                self.stdout.write(self.style.SUCCESS(f"✔️  Zapisano: {lat:.6f}, {lng:.6f} dla {ident}"))

            except Exception as e:
                self.stderr.write(f"[BŁĄD] {ident}: {e}")
