from django.contrib.gis.geos import Point
from maps.models import BusStation
from .station_filter import (
    get_stations_near_location,
    get_qualified_route_codes,
    build_qualified_stations,
    find_shortest_route
)
from .route_path import get_route_path
from .get_route_geom import get_route_geom


class RouteFinder:
    """Service class để tìm tuyến đường bus tối ưu"""
    
    def __init__(self, start_lat, start_long, end_lat, end_long, meter_radius=120500):
        self.user_location = Point(start_long, start_lat, srid=4326)
        self.destination_location = Point(end_long, end_lat, srid=4326)
        self.meter_radius = meter_radius
        self.radius = meter_radius / 111000
    
    def find_best_route(self):
        """Tìm tuyến đường tốt nhất"""
        # 1. Tìm các trạm gần user và destination
        stations_near_user = get_stations_near_location(
            self.user_location, self.radius
        )
        stations_near_destination = get_stations_near_location(
            self.destination_location, self.radius
        )
        
        # 2. Lấy các route_code phù hợp
        qualified_route_codes = get_qualified_route_codes(
            stations_near_user, stations_near_destination
        )
        
        if not qualified_route_codes:
            return None, None, None
        
        # 3. Xây dựng qualified_stations
        qualified_stations = build_qualified_stations(
            qualified_route_codes,
            stations_near_user,
            stations_near_destination,
            self.user_location,
            self.destination_location,
            self.meter_radius
        )
        
        if not qualified_stations:
            return None, None, None
        
        # 4. Tìm tuyến ngắn nhất
        shortest_obj = find_shortest_route(qualified_stations)
        
        # 5. Lấy thông tin chi tiết đường đi
        route_info = self._build_route_info(shortest_obj)
        
        return route_info, list(qualified_route_codes), qualified_stations
    
    def _build_route_info(self, shortest_obj):
        """Xây dựng thông tin chi tiết về tuyến đường"""
        start_order = shortest_obj["stations_near_user"][0]["order"]
        end_order = shortest_obj["stations_near_destination"][0]["order"]
        route_code = shortest_obj["route_code"]
        
        # Lấy đường đi chi tiết
        route_path = get_route_path(start_order, end_order, route_code)
        
        # Lấy thông tin trạm
        start_station = shortest_obj["stations_near_user"][0]
        end_station = shortest_obj["stations_near_destination"][0]
        
        # Lấy geometry đường đi bộ
        start_station_obj = BusStation.objects.get(id=start_station["id"])
        end_station_obj = BusStation.objects.get(id=end_station["id"])
        
        start_route_geom = get_route_geom(
            self.user_location.y, self.user_location.x,
            start_station_obj.geom.y, start_station_obj.geom.x
        )
        
        end_route_geom = get_route_geom(
            end_station_obj.geom.y, end_station_obj.geom.x,
            self.destination_location.y, self.destination_location.x
        )
        
        # Xây dựng response object
        return {
            "route_code": route_code,
            "start_station": start_station,
            "end_station": end_station,
            "total_walk_distance": shortest_obj["total_walk_distance"],
            "total_stations": route_path['total_stations'],
            "user_location": [self.user_location.x, self.user_location.y],
            "user_destination": [self.destination_location.x, self.destination_location.y],
            "stations": route_path['stations'],
            "routes": route_path['routes'],
            "start_route_geom": start_route_geom,
            "end_route_geom": end_route_geom
        }