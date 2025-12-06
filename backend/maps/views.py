from django.http import HttpResponse
from rest_framework.response import Response
from django.shortcuts import render

from .models import User, BusRoute, BusStation, RouteStation
from maps.serializers import UserSerializer, MapSerializer, RouteCodeSerializer
from rest_framework import generics
from rest_framework.views import APIView
from django.contrib.gis.geos import Point
from .services.route_path import get_route_path
from .services.get_route_geom import get_route_geom


class UserListApiView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class MapView(APIView):
    def get(self, request):
        data = {
            "bus_routes": BusRoute.objects.all(),
            "bus_stations": BusStation.objects.all(),
            "users": User.objects.all(),
        }
        serializer = MapSerializer(data)
        return Response(serializer.data)

    def post(self, request):
        start_lat = float(request.data.get("start_lat"))
        start_long = float(request.data.get("start_long"))
        end_lat = float(request.data.get("end_lat"))
        end_long = float(request.data.get("end_long"))

        # (W.I.P): Dùng buffer để tìm các trạm phù hợp: (1 km = 0.009)
        meter_radius = 12500
        radius = meter_radius / 111000

        user_location = Point(start_long, start_lat, srid=4326)
        destination_location = Point(end_long, end_lat, srid=4326)

        user_buffer = user_location.buffer(radius)
        destination_buffer = destination_location.buffer(radius)

        stations_near_user = BusStation.objects.filter(geom__within=user_buffer)
        stations_near_destination = BusStation.objects.filter(
            geom__within=destination_buffer
        )

        # Lọc bus_station bằng bus_route trùng mã
        user_route_codes = (
            BusRoute.objects.filter(route_stations__station__in=stations_near_user)
            .values_list("route_code", flat=True)
            .distinct()
        )
        dest_route_codes = (
            BusRoute.objects.filter(
                route_stations__station__in=stations_near_destination
            )
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

        # Lọc các trạm có thể đi dựa trên các route_codes:
        qualified_stations = []
        for code in qualified_route_codes:
            # 1. Lấy station_ids thuộc tuyến (qua RouteStation)
            route_station_ids = RouteStation.objects.filter(
                route__route_code=code
            ).values_list("station_id", flat=True)

            # 2. Lọc stations gần destination nằm trong tuyến
            code_stations_near_destination = stations_near_destination.filter(
                id__in=route_station_ids
            )

            # 3. Lọc stations gần user nằm trong tuyến
            code_stations_near_user = stations_near_user.filter(
                id__in=route_station_ids
            )

            stations_near_user_sorted = sorted(
                [
                    {
                        "id": station.id,
                        "name": station.name,
                        "code": station.code,
                        "route_code": code,
                        "order": RouteStation.objects.filter(
                            route__route_code=code,
                            station=station
                        ).first().order,
                        "straight_distance": round(station.geom.distance(user_location) * 111_000, 2),
                        "geom": station.geom.wkt
                    }
                    for station in code_stations_near_user
                ], 
                key=lambda station: station["straight_distance"]
            )

            stations_near_destination_sorted = sorted(
                [
                    {
                        "id": station.id,
                        "name": station.name,
                        "code": station.code,
                        "order": RouteStation.objects.filter(
                            route__route_code=code,
                            station=station
                        ).first().order,
                        "straight_distance": round(station.geom.distance(destination_location) * 111_000, 2)
                    }
                    for station in code_stations_near_destination
                ], 
                key=lambda station: station["straight_distance"]
            )

            qualified_stations.append({
                "route_code": code,
                "buffer": meter_radius,
                "total_walk_distance": stations_near_user_sorted[0]["straight_distance"] + stations_near_destination_sorted[0]["straight_distance"],
                "stations_near_user": stations_near_user_sorted,
                "stations_near_destination": stations_near_destination_sorted
            })

        # Chọn route tốt nhất dựa trên total_walk_distance
        shortest_obj = qualified_stations[0]
        for obj in qualified_stations:
            if obj["total_walk_distance"] < shortest_obj["total_walk_distance"]:
                shortest_obj = obj

        # LẤY THÔNG TIN ĐƯỜNG ĐI CHI TIẾT
        start_order = shortest_obj["stations_near_user"][0]["order"]
        end_order = shortest_obj["stations_near_destination"][0]["order"]
        route_code = shortest_obj["route_code"]
        
        # Gọi hàm tìm đường
        route_path = get_route_path(start_order, end_order, route_code)

        start_station = shortest_obj["stations_near_user"][0]
        end_station = shortest_obj["stations_near_destination"][0]

        start_station_obj = BusStation.objects.get(id=start_station["id"])
        end_station_obj = BusStation.objects.get(id=end_station["id"])

        # Gọi hàm lấy geometry đường đi
        start_route_geom = get_route_geom(
            user_location.y, user_location.x,
            start_station_obj.geom.y, start_station_obj.geom.x
        )
        end_route_geom = get_route_geom(
            end_station_obj.geom.y, end_station_obj.geom.x,
            destination_location.y, destination_location.x
        )

        # TẠO SHORTEST_OBJ MỚI
        shortest_obj_v2 = {
            "route_code": route_code,
            "start_station": start_station,
            "end_station": end_station,
            "total_walk_distance": shortest_obj["total_walk_distance"],
            "total_stations": route_path['total_stations'],
            "user_location": [user_location.x, user_location.y],
            "destination_location": [destination_location.x, destination_location.y],
            "stations": route_path['stations'],  # Danh sách trạm sẽ đi
            "routes": route_path['routes'],       # Danh sách route sẽ đi, và bỏ route cuối đi để đỡ bị thừa
            "start_route_geom": start_route_geom,
            "end_route_geom": end_route_geom
        }
 
        return Response({
            "message": "Dữ liệu đã nhận.",
            "buffer_meter": round(radius * 111_000, 2),
            "shortest_obj": shortest_obj_v2,  # Response mới
            "qualified_routes": list(qualified_route_codes),
            "qualified_stations": qualified_stations,  # Giữ lại để debug
        })

class RouteDetailView(APIView):
    def get(self, request, route_code):
        related_routes = BusRoute.objects.filter(route_code=route_code).all()
        related_stations = BusStation.objects.filter(
            station_routes__route__route_code=route_code
        ).distinct()

        # Tự tạo data structure
        bus_stations = []
        for station in related_stations:
            rs = RouteStation.objects.filter(
                route__route_code=route_code,
                station=station
            ).first()
            
            bus_stations.append({
                "id": station.id,
                "code": station.code,
                "name": station.name,
                "order": rs.order if rs else None,
                "geom": station.geom.wkt if station.geom else None
            })

        bus_routes = []
        for route in related_routes:
            rs = RouteStation.objects.filter(route=route).first()

            bus_routes.append({
                "id": route.id,
                "name": route.name,
                "route_code": route.route_code,
                "order": rs.order if rs else None,
                "geom": route.geom.wkt if route.geom else None,
                "direction": route.direction
            })
        
        data = {
            "bus_routes": bus_routes, # bỏ route cuối cùng tại bị thừa
            "bus_stations": bus_stations,
        }
        
        # Trả về trực tiếp, không cần serializer
        return Response(data)

class RouteCodeListView(APIView):
    def get(self, request):
        codes = BusRoute.objects.values_list("route_code", flat=True).distinct()
        return Response(codes)
