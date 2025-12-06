import requests

def get_route_geom(lat1, lon1, lat2, lon2):
    start = f"{lon1},{lat1}"
    end = f"{lon2},{lat2}"
    url = f"http://router.project-osrm.org/route/v1/foot/{start};{end}?overview=full&geometries=geojson"

    response = requests.get(url)
    data = response.json()

    if "routes" not in data or len(data["routes"]) == 0:
        return None

    route = data["routes"][0]
    return {
        "distance": route["distance"],
        "duration": route["duration"],
        "geometry": route["geometry"],  # LineString GeoJSON
    }
