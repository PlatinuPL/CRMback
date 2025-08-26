import requests

def get_coordinates(voivodeship, county, town, precinct=None, plot_number=None):
    queries = []

    # Pełne zapytanie (działka + obręb + miejscowość + powiat + województwo)
    full_query = ", ".join(part for part in [plot_number, precinct, town, county, voivodeship, "Polska"] if part)
    queries.append(full_query)

    # Uproszczone zapytanie (bez działki i obrębu)
    basic_query = ", ".join(part for part in [town, county, voivodeship, "Polska"] if part)
    if basic_query != full_query:
        queries.append(basic_query)

    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "django-parcel-geocoder"}

    for query in queries:
        print(f"Próbuję zapytanie: {query}")
        response = requests.get(url, params={"q": query, "format": "json", "limit": 1}, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                print(f"✅ Sukces: {lat}, {lon}")
                return lat, lon
        else:
            print(f"❌ Błąd HTTP: {response.status_code} dla zapytania {query}")

    print("⚠️ Nie znaleziono współrzędnych.")
    return None, None
