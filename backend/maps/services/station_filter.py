from django.contrib.gis.geos import Point
from maps.models import BusStation, BusRoute, RouteStation


def get_stations_near_location(location: Point, radius: float):
    """Lấy các trạm gần vị trí với bán kính cho trước"""
    buffer = location.buffer(radius)
    return BusStation.objects.filter(geom__within=buffer)


def get_qualified_route_codes(stations_near_user, stations_near_destination):
    """Lấy các route_code phù hợp (có trạm gần cả user và destination)"""
    user_route_codes = (
        BusRoute.objects.filter(route_stations__station__in=stations_near_user)
        .values_list("route_code", flat=True)
        .distinct()
    )
    
    dest_route_codes = (
        BusRoute.objects.filter(route_stations__station__in=stations_near_destination)
        .values_list("route_code", flat=True)
        .distinct()
    )
    
    qualified_route_codes = (
        BusRoute.objects
        .filter(route_code__in=user_route_codes)
        .filter(route_code__in=dest_route_codes)
        .order_by('route_code')
        .distinct('route_code')
        .values_list('route_code', flat=True)
    )
    
    return qualified_route_codes


def get_station_info(station, route_code, reference_location):
    """Lấy thông tin chi tiết của một trạm"""
    rs = RouteStation.objects.filter(
        route__route_code=route_code,
        station=station
    ).first()
    
    return {
        "id": station.id,
        "name": station.name,
        "code": station.code,
        "route_code": route_code,
        "order": rs.order if rs else None,
        "straight_distance": round(station.geom.distance(reference_location) * 111_000, 2),
        "geom": station.geom.wkt
    }


def get_sorted_stations_for_route(route_code, stations, reference_location):
    """Lấy danh sách trạm đã sắp xếp theo khoảng cách"""
    route_station_ids = RouteStation.objects.filter(
        route__route_code=route_code
    ).values_list("station_id", flat=True)
    
    filtered_stations = stations.filter(id__in=route_station_ids)
    
    stations_with_info = [
        get_station_info(station, route_code, reference_location)
        for station in filtered_stations
    ]
    
    return sorted(stations_with_info, key=lambda s: s["straight_distance"])


def build_qualified_stations(qualified_route_codes, stations_near_user, 
                             stations_near_destination, user_location, 
                             destination_location, meter_radius):
    """Xây dựng danh sách qualified_stations cho tất cả các tuyến"""
    qualified_stations = []
    
    for code in qualified_route_codes:
        stations_near_user_sorted = get_sorted_stations_for_route(
            code, stations_near_user, user_location
        )
        
        stations_near_destination_sorted = get_sorted_stations_for_route(
            code, stations_near_destination, destination_location
        )
        
        if not stations_near_user_sorted or not stations_near_destination_sorted:
            continue
        
        qualified_stations.append({
            "route_code": code,
            "buffer": meter_radius,
            "total_walk_distance": (
                stations_near_user_sorted[0]["straight_distance"] + 
                stations_near_destination_sorted[0]["straight_distance"]
            ),
            "stations_near_user": stations_near_user_sorted,
            "stations_near_destination": stations_near_destination_sorted
        })
    
    return qualified_stations


def find_shortest_route(qualified_stations):
    """Tìm tuyến có tổng quãng đi bộ ngắn nhất"""
    if not qualified_stations:
        return None
    
    return min(qualified_stations, key=lambda x: x["total_walk_distance"])