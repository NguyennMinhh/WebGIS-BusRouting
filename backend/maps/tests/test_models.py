from django.test import TestCase
from django.contrib.gis.geos import Point, LineString
from maps.models import BusStation, BusRoute, RouteStation


class BusStationModelTest(TestCase):
    """Test model BusStation"""
    
    def setUp(self):
        """Tạo dữ liệu test - chạy trước mỗi test method"""
        self.station = BusStation.objects.create(
            name="Trạm Test",
            code="TEST01",
            geom=Point(105.8342, 21.0278, srid=4326)
        )
    
    def test_station_creation(self):
        """Test tạo station thành công"""
        self.assertEqual(self.station.name, "Trạm Test")
        self.assertEqual(self.station.code, "TEST01")
        self.assertIsNotNone(self.station.geom)
    
    def test_station_str_method(self):
        """Test __str__ method"""
        self.assertEqual(str(self.station), "Trạm Test")
    
    def test_unique_code_constraint(self):
        """Test code phải unique"""
        from django.db import IntegrityError
        
        with self.assertRaises(IntegrityError):
            BusStation.objects.create(
                name="Trạm Test 2",
                code="TEST01",  # Code trùng
                geom=Point(105.8400, 21.0300, srid=4326)
            )
    
    def test_geom_is_point(self):
        """Test geometry là Point type"""
        self.assertEqual(self.station.geom.geom_type, 'Point')
        self.assertEqual(self.station.geom.srid, 4326)


class BusRouteModelTest(TestCase):
    """Test model BusRoute"""
    
    def setUp(self):
        """Chuẩn bị dữ liệu"""
        # Tạo 2 trạm
        self.start_station = BusStation.objects.create(
            name="Trạm Đầu",
            code="START01",
            geom=Point(105.8342, 21.0278, srid=4326)
        )
        
        self.end_station = BusStation.objects.create(
            name="Trạm Cuối",
            code="END01",
            geom=Point(105.8400, 21.0300, srid=4326)
        )
        
        # Tạo route
        self.route = BusRoute.objects.create(
            name="Tuyến Test",
            route_code="28",
            direction="go",
            start_station=self.start_station,
            end_station=self.end_station,
            geom=LineString(
                [(105.8342, 21.0278), (105.8400, 21.0300)],
                srid=4326
            )
        )
    
    def test_route_creation(self):
        """Test tạo route thành công"""
        self.assertEqual(self.route.route_code, "28")
        self.assertEqual(self.route.direction, "go")
        self.assertIsNotNone(self.route.geom)
    
    def test_route_direction_choices(self):
        """Test direction chỉ nhận 'go' hoặc 'return'"""
        # Direction hợp lệ
        route_return = BusRoute.objects.create(
            name="Tuyến về",
            route_code="28",
            direction="return",
            geom=LineString([(105.8400, 21.0300), (105.8342, 21.0278)], srid=4326)
        )
        self.assertEqual(route_return.direction, "return")
    
    def test_route_has_start_end_stations(self):
        """Test route có start và end station"""
        self.assertEqual(self.route.start_station, self.start_station)
        self.assertEqual(self.route.end_station, self.end_station)


class RouteStationModelTest(TestCase):
    """Test model RouteStation"""
    
    def setUp(self):
        """Chuẩn bị dữ liệu"""
        # Tạo stations
        self.station1 = BusStation.objects.create(
            name="Trạm 1", code="S1",
            geom=Point(105.8342, 21.0278, srid=4326)
        )
        self.station2 = BusStation.objects.create(
            name="Trạm 2", code="S2",
            geom=Point(105.8350, 21.0285, srid=4326)
        )
        self.station3 = BusStation.objects.create(
            name="Trạm 3", code="S3",
            geom=Point(105.8400, 21.0300, srid=4326)
        )
        
        # Tạo route
        self.route = BusRoute.objects.create(
            name="Tuyến Test",
            route_code="28",
            direction="go"
        )
    
    def test_create_route_station(self):
        """Test tạo RouteStation"""
        rs = RouteStation.objects.create(
            route=self.route,
            station=self.station1,
            order=1
        )
        self.assertEqual(rs.order, 1)
        self.assertEqual(rs.route, self.route)
        self.assertEqual(rs.station, self.station1)
    
    def test_route_station_ordering(self):
        """Test RouteStation được sắp xếp theo order"""
        RouteStation.objects.create(route=self.route, station=self.station1, order=1)
        RouteStation.objects.create(route=self.route, station=self.station2, order=2)
        RouteStation.objects.create(route=self.route, station=self.station3, order=3)
        
        route_stations = list(self.route.route_stations.all())
        
        # Kiểm tra thứ tự
        self.assertEqual(route_stations[0].order, 1)
        self.assertEqual(route_stations[1].order, 2)
        self.assertEqual(route_stations[2].order, 3)
    
    def test_auto_update_start_end_station(self):
        """Test tự động cập nhật start/end station khi thêm RouteStation"""
        # Thêm các trạm theo thứ tự
        RouteStation.objects.create(route=self.route, station=self.station1, order=1)
        RouteStation.objects.create(route=self.route, station=self.station2, order=2)
        RouteStation.objects.create(route=self.route, station=self.station3, order=3)
        
        # Reload route từ database
        self.route.refresh_from_db()
        
        # Kiểm tra start/end được cập nhật
        self.assertEqual(self.route.start_station, self.station1)
        self.assertEqual(self.route.end_station, self.station3)
    
    def test_unique_route_station_constraint(self):
        """Test không thể thêm cùng station vào route 2 lần"""
        from django.db import IntegrityError
        
        RouteStation.objects.create(
            route=self.route,
            station=self.station1,
            order=1
        )
        
        with self.assertRaises(IntegrityError):
            RouteStation.objects.create(
                route=self.route,
                station=self.station1,  # Trùng station
                order=2
            )