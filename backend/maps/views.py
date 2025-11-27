from rest_framework.response import Response
from rest_framework import generics
from rest_framework.views import APIView

from .models import User, BusRoute, BusStation, RouteStation
from .serializers import UserSerializer, MapSerializer
from .services.route_finder import RouteFinder


class UserListApiView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class MapView(APIView):
    """API để lấy dữ liệu bản đồ và tìm tuyến đường"""
    
    def get(self, request):
        """Lấy tất cả dữ liệu bản đồ"""
        data = {
            "bus_routes": BusRoute.objects.all(),
            "bus_stations": BusStation.objects.all(),
            "users": User.objects.all(),
        }
        serializer = MapSerializer(data)
        return Response(serializer.data)

    def post(self, request):
        """Tìm tuyến đường tối ưu"""
        # Lấy tham số
        start_lat = float(request.data.get("start_lat"))
        start_long = float(request.data.get("start_long"))
        end_lat = float(request.data.get("end_lat"))
        end_long = float(request.data.get("end_long"))
        
        # Sử dụng service để tìm tuyến
        route_finder = RouteFinder(start_lat, start_long, end_lat, end_long)
        route_info, qualified_routes, qualified_stations = route_finder.find_best_route()
        
        if not route_info:
            return Response({
                "error": "Không tìm thấy tuyến đường phù hợp",
                "message": "Vui lòng thử lại với điểm khác hoặc tăng bán kính tìm kiếm"
            }, status=404)
        
        # Trả về kết quả
        return Response({
            "message": "Dữ liệu đã nhận.",
            "buffer_meter": route_finder.meter_radius,
            "shortest_obj": route_info,
            "qualified_routes": qualified_routes,
            "qualified_stations": qualified_stations,
        })


class RouteDetailView(APIView):
    """API để lấy chi tiết một tuyến bus"""
    
    def get(self, request, route_code):
        """Lấy chi tiết tuyến theo route_code"""
        related_routes = BusRoute.objects.filter(route_code=route_code).all()
        related_stations = BusStation.objects.filter(
            station_routes__route__route_code=route_code
        ).distinct()

        # Xây dựng dữ liệu trạm
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

        # Xây dựng dữ liệu route
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
        
        return Response({
            "bus_routes": bus_routes,
            "bus_stations": bus_stations,
        })


class RouteCodeListView(APIView):
    """API để lấy danh sách tất cả route_code"""
    
    def get(self, request):
        """Lấy danh sách route_code"""
        codes = BusRoute.objects.values_list("route_code", flat=True).distinct()
        return Response(list(codes))