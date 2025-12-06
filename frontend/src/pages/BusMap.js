import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet-polylinedecorator";
import { useEffect, useState } from "react";
import { fetchMapData, sendLocationDataToBackend } from "../services/api";
import { useNavigate } from "react-router-dom";

import iconUrl from "leaflet/dist/images/marker-icon.png";
import iconShadow from "leaflet/dist/images/marker-shadow.png";

import { parseLine } from "../utils/geomParser";
import { busStationIcon } from "../utils/icon";
import { useDestinationMode } from "../hooks/useDestinationMode";
import { useUserLocation } from "../hooks/useUserLocation";
import { zoomToStation, renderStations, renderRoutes } from "../utils/mapHelpers";

const DefaultIcon = L.icon({
  iconUrl,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});
L.Marker.prototype.options.icon = DefaultIcon;

export default function BusMap() {
  const [data, setData] = useState(null);
  const [map, setMap] = useState(null);
  const [routeResult, setRouteResult] = useState(null);
  const navigate = useNavigate();

  // Hooks
  const { userLocation, addUserLocation } = useUserLocation(map);
  const { destinationMode, destination, toggleDestinationMode } = useDestinationMode(map);

  // Lấy dữ liệu API
  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetchMapData();
        console.log("Response: ", res);
        setData(res);
      } catch (err) {
        console.log("Error: ", err.message);
      }
    };
    load();
  }, []);

  // Vẽ bản đồ:
  useEffect(() => {
    if (!data) return;
    const mapContainer = document.getElementById("map");
    if (!mapContainer) return;

    const map = L.map(mapContainer).setView([21.03, 105.82], 13);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/">OSM</a>',
    }).addTo(map);

    // Vẽ các trạm:
    renderStations(map, data.bus_stations, busStationIcon);

    // Vẽ các tuyến:
    renderRoutes(map, data.bus_routes, parseLine);

    setMap(map);

    return () => map.remove();
  }, [data]);

  useEffect(() => {
    console.log("User Location: ", userLocation);
  }, [userLocation]);

  if (!data) return <p>Đang tải bản đồ...</p>;

  return (
    <div style={{ display: "flex", gap: "1rem" }}>
      {/* Cột trái: Bản đồ */}
      <div
        id="map"
        style={{
          flex: "0 0 70%",
          height: "53rem",
          borderRadius: "8px",
          border: "1px solid #ccc",
        }}
      ></div>

      {/* Cột phải: Panel thông tin */}
      <div
        style={{
          flex: "0 0 30%",
          background: "#fff",
          borderRadius: "8px",
          border: "1px solid #ddd",
          padding: "1rem",
          overflowY: "auto",
          height: "53rem",
        }}
      >
        {/* Nút điều khiển */}
        <div style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "8px" }}>
          <button
            onClick={addUserLocation}
            style={{
              padding: "10px",
              background: "#4CAF50",
              color: "white",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
              fontWeight: "bold",
            }}
          >
            Lấy vị trí của tôi
          </button>

          <button
            onClick={toggleDestinationMode}
            style={{
              padding: "10px",
              background: destinationMode ? "#FFA500" : "#ccc",
              color: destinationMode ? "white" : "#666",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
              fontWeight: "bold",
            }}
          >
            {destinationMode ? "🟡 Đang chọn điểm đến" : "⚪ Bật chế độ chọn điểm đến"}
          </button>

          <button
            disabled={!userLocation || !destination}
            style={{
              padding: "10px",
              background:
                !userLocation || !destination ? "#ddd" : "#2196F3",
              color: !userLocation || !destination ? "#999" : "white",
              border: "none",
              borderRadius: "6px",
              cursor: !userLocation || !destination ? "not-allowed" : "pointer",
              fontWeight: "bold",
            }}
            onClick={async () => {
              if (!userLocation || !destination)
                return alert("Thiếu vị trí người dùng hoặc điểm đến");
              try {
                const res = await sendLocationDataToBackend(
                  userLocation.latitude,
                  userLocation.longitude,
                  destination.lat,
                  destination.lng
                );
                console.log("Server response:", res);
                setRouteResult(res);
              } catch (err) {
                console.error("Lỗi khi gửi:", err);
                alert("Không gửi được dữ liệu.");
              }
            }}
          >
            Tìm tuyến xe buýt
          </button>
        </div>
        
        {/* Hiển thị thông tin */}
        <h3>Kết quả tìm kiếm tuyến</h3>

        {!routeResult ? (
          <div
            style={{
              textAlign: "center",
              padding: "2rem 1rem",
              color: "#666",
            }}
          >
            <p>Chưa có dữ liệu tìm kiếm.</p>
            <p style={{ fontSize: "14px" }}>
              Nhấn nút bên trên để bắt đầu
            </p>
          </div>
        ) : (
          <>
            {/* Thông tin chung */}
            <div
              style={{
                background: "#e8f5e9",
                padding: "12px",
                borderRadius: "6px",
                marginBottom: "1rem",
              }}
            >
              <p style={{ margin: "4px 0", fontSize: "14px" }}>
                <strong>Bán kính:</strong> {routeResult.buffer_meter}m
              </p>
              <p style={{ margin: "4px 0", fontSize: "14px" }}>
                <strong>Tuyến khả dụng:</strong>{" "}
                {routeResult.qualified_routes?.length > 0
                  ? routeResult.qualified_routes.join(", ")
                  : "Không có"}
              </p>
            </div>

            {/* Tuyến tốt nhất */}
            {routeResult.shortest_obj && (
              <div style={{ 
                border: "2px solid #4CAF50", 
                borderRadius: "8px", 
                padding: "12px", 
                marginBottom: "1rem", 
                background: "#f1f8f4" 
              }}>
                <h4 style={{ 
                  margin: "0 0 10px 0", 
                  color: "#2E7D32", 
                  fontSize: "20px" 
                }}>
                  Tuyến tốt nhất: {routeResult.shortest_obj.route_code}
                </h4>

                <button
                  onClick={() =>
                    navigate("/result-route", {
                      state: {
                        resultRoute: routeResult.shortest_obj
                      }
                    })
                  }
                  style={{ padding: "10px" }}
                >
                  Chọn tuyến
                </button>   
                
                <div style={{ background: "#fff", padding: "10px", borderRadius: "4px", marginTop: "10px" }}>
                  <p style={{ margin: "4px 0", fontSize: "14px", fontWeight: "bold", color: "#1976D2" }}>
                    Tổng quãng đi bộ: {routeResult.shortest_obj.total_walk_distance.toFixed(2)}m
                  </p>
                  
                  <hr style={{ margin: "10px 0", border: "none", borderTop: "1px solid #ddd" }} />
                  
                  <div style={{ marginBottom: "12px" }}>
                    <p style={{ margin: "4px 0 6px 0", fontSize: "14px", fontWeight: "bold" }}>
                      Trạm gần bạn nhất:
                    </p>
                    {routeResult.shortest_obj.start_station ? (
                      <div>
                        <p
                          style={{ 
                            margin: "2px 0 2px 10px", 
                            fontSize: "13px",
                            cursor: "pointer",
                            color: "#1976D2",
                            textDecoration: "underline"
                          }}
                          onClick={() => zoomToStation(map, data, routeResult.shortest_obj.start_station.name)}
                          title="Click để xem trạm trên bản đồ"
                        >
                          <strong>{routeResult.shortest_obj.start_station.name}</strong> ({routeResult.shortest_obj.start_station.code})
                        </p>
                        <p style={{ margin: "0 0 0 10px", fontSize: "11px", color: "#666" }}>
                          → Đi bộ {routeResult.shortest_obj.start_station.straight_distance}m
                          {routeResult.shortest_obj.start_station.order && 
                            ` • Order: ${routeResult.shortest_obj.start_station.order}`
                          }
                        </p>
                      </div>
                    ) : (
                      <p style={{ margin: "0 0 0 10px", fontSize: "12px", color: "#999" }}>Không có trạm</p>
                    )}
                  </div>
                  
                  <div>
                    <p style={{ margin: "4px 0 6px 0", fontSize: "14px", fontWeight: "bold" }}>
                      Trạm gần điểm đến nhất:
                    </p>
                    {routeResult.shortest_obj.end_station ? (
                      <div>
                        <p 
                          style={{ 
                            margin: "2px 0 2px 10px", 
                            fontSize: "13px",
                            cursor: "pointer",
                            color: "#1976D2",
                            textDecoration: "underline"
                          }}
                          onClick={() => zoomToStation(routeResult.shortest_obj.end_station.name)}
                          title="Click để xem trạm trên bản đồ"
                        >
                          <strong>{routeResult.shortest_obj.end_station.name}</strong> ({routeResult.shortest_obj.end_station.code})
                        </p>
                        <p style={{ margin: "0 0 0 10px", fontSize: "11px", color: "#666" }}>
                          → Đi bộ {routeResult.shortest_obj.end_station.straight_distance}m
                          {routeResult.shortest_obj.end_station.order && 
                            ` • Order: ${routeResult.shortest_obj.end_station.order}`
                          }
                        </p>
                      </div>
                    ) : (
                      <p style={{ margin: "0 0 0 10px", fontSize: "12px", color: "#999" }}>Không có trạm</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Hiển thị chi tiết từng tuyến */}
            <h4 style={{ fontSize: "16px", marginBottom: "10px", marginTop: "1rem" }}>
              Tất cả các tuyến phù hợp:
            </h4>
            {routeResult.qualified_stations?.map((routeData, idx) => (
              <div
                key={idx}
                style={{
                  border: "1px solid #ddd",
                  borderRadius: "8px",
                  padding: "12px",
                  marginBottom: "1rem",
                  background: routeData.route_code === routeResult.shortest_obj?.route_code ? "#f1f8f4" : "#fff",
                }}
              >
                {/* Header tuyến */}
                <h4
                  style={{
                    margin: "0 0 10px 0",
                    color: "#1E90FF",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    fontSize: "18px"
                  }}
                >
                  Tuyến {routeData.route_code}
                  <span style={{ fontSize: "12px", color: "#666" }}>
                    ({routeData.total_walk_distance.toFixed(2)}m)
                  </span>
                </h4>

                {/* Trạm gần người dùng - HIỂN THỊ TẤT CẢ THEO ORDER */}
                <div style={{ marginBottom: "12px" }}>
                  <p
                    style={{
                      fontWeight: "bold",
                      margin: "8px 0 6px 0",
                      fontSize: "13px",
                    }}
                  >
                    Trạm gần bạn (theo thứ tự):
                  </p>
                  {routeData.stations_near_user?.length > 0 ? (
                    <ol
                      style={{
                        margin: 0,
                        paddingLeft: "20px",
                        fontSize: "12px",
                      }}
                    >
                      {/* Sort theo order trước khi hiển thị */}
                      {[...routeData.stations_near_user]
                        .sort((a, b) => (a.order || 999) - (b.order || 999))
                        .map((station) => (
                        <li key={station.id} style={{ marginBottom: "4px" }}>
                          <span
                            style={{
                              cursor: "pointer",
                              color: "#1976D2",
                              textDecoration: "underline"
                            }}
                            onClick={() => zoomToStation(station.name)}
                            title="Click để xem trạm trên bản đồ"
                          >
                            <strong>{station.name}</strong> ({station.code})
                          </span>
                          <br />
                          <span style={{ color: "#666", fontSize: "11px" }}>
                            ↔ {station.straight_distance}m
                            {station.order && ` • Thứ tự: ${station.order}`}
                          </span>
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <p style={{ color: "#999", fontSize: "12px", marginLeft: "10px" }}>
                      Không có trạm
                    </p>
                  )}
                </div>

                {/* Trạm gần điểm đến - HIỂN THỊ TẤT CẢ THEO ORDER */}
                <div>
                  <p
                    style={{
                      fontWeight: "bold",
                      margin: "8px 0 6px 0",
                      fontSize: "13px",
                    }}
                  >
                    Trạm gần điểm đến (theo thứ tự):
                  </p>
                  {routeData.stations_near_destination?.length > 0 ? (
                    <ol
                      style={{
                        margin: 0,
                        paddingLeft: "20px",
                        fontSize: "12px",
                      }}
                    >
                      {/* Sort theo order trước khi hiển thị */}
                      {[...routeData.stations_near_destination]
                        .sort((a, b) => (a.order || 999) - (b.order || 999))
                        .map((station) => (
                        <li key={station.id} style={{ marginBottom: "4px" }}>
                          <span
                            style={{
                              cursor: "pointer",
                              color: "#1976D2",
                              textDecoration: "underline"
                            }}
                            onClick={() => zoomToStation(station.name)}
                            title="Click để xem trạm trên bản đồ"
                          >
                            <strong>{station.name}</strong> ({station.code})
                          </span>
                          <br />
                          <span style={{ color: "#666", fontSize: "11px" }}>
                            ↔ {station.straight_distance}m
                            {station.order && ` • Thứ tự: ${station.order}`}
                          </span>
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <p style={{ color: "#999", fontSize: "12px", marginLeft: "10px" }}>
                      Không có trạm
                    </p>
                  )}
                </div>
              </div>
            ))}

            {/* Nếu không có tuyến nào */}
            {routeResult.qualified_stations?.length === 0 && (
              <div
                style={{
                  textAlign: "center",
                  padding: "2rem 1rem",
                  color: "#d32f2f",
                }}
              >
                <p>Không tìm thấy tuyến phù hợp</p>
                <p style={{ fontSize: "13px" }}>
                  Thử tăng bán kính tìm kiếm hoặc chọn điểm khác
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}