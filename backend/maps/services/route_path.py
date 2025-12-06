from django.db.models import Max
from maps.models import RouteStation, BusRoute

def get_route_path(start_order, end_order, route_code):
    if start_order < end_order:
        # ✅ THÊM list() Ở ĐÂY!
        route_stations = list(
            RouteStation.objects.filter(
                route__route_code=route_code,
                order__gte=start_order,
                order__lte=end_order
            ).select_related('station', 'route').order_by('order')
        )

    elif start_order > end_order:
        max_order = RouteStation.objects.filter(
            route__route_code=route_code
        ).aggregate(max_order=Max('order'))['max_order']

        first_part = RouteStation.objects.filter(
            route__route_code=route_code,
            order__gte=start_order
        ).select_related('station', 'route').order_by('order')

        second_part = RouteStation.objects.filter(
            route__route_code=route_code,
            order__lte=end_order
        ).select_related('station', 'route').order_by('order')

        route_stations = list(first_part) + list(second_part)

    else:
        return {
            'route_code': route_code,
            'stations': [],
            'routes': [],
            'message': 'Điểm đi và điểm đến trùng nhau'
        }

    # Xây dựng danh sách stations
    stations = []
    for rs in route_stations:
        stations.append({
            'id': rs.station.id,
            'order': rs.order,
            'name': rs.station.name,
            'code': rs.station.code,
            'geom': rs.station.geom.wkt
        })

    # FIX: Lấy routes theo đúng thứ tự, bỏ route cuối
    routes = []
    for rs in route_stations[:-1]:  # ✅ Giờ là list, không lỗi
        route = rs.route
        routes.append({
            'id': route.id,
            'order': rs.order,
            'name': route.name,
            'route_code': route.route_code,
            'direction': route.direction,
            'geom': route.geom.wkt if route.geom else None
        })

    print(f"Stations: {[s['code'] for s in stations]}")
    print(f"Routes: {[(r['order'], r['name']) for r in routes]}")

    return {
        'route_code': route_code,
        'stations': stations,
        'routes': routes,
        'total_stations': len(stations)
    }