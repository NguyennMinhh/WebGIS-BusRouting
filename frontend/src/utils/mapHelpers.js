import L from "leaflet";
import { parsePoint } from "./geomParser";

// Zoom đến và highlight trạm trên map
export function zoomToStation(map, data, stationName) {
  if (!map || !data) return;
  
  const station = data.bus_stations.find(s => s.name === stationName);
  if (!station) return;
  
  const coords = parsePoint(station.geom);
  if (!coords) return;
  
  // Zoom đến trạm với animation
  map.setView(coords, 17, { animate: true, duration: 1 });
  
  // Highlight trạm bằng circle
  const circle = L.circle(coords, {
    color: '#FF4500',
    fillColor: '#FF6347',
    fillOpacity: 0.3,
    radius: 50
  }).addTo(map);
  
  // Tìm và mở popup của trạm
  map.eachLayer((layer) => {
    if (layer instanceof L.Marker) {
      const popupContent = layer.getPopup()?.getContent();
      if (popupContent && popupContent.includes(station.code)) {
        setTimeout(() => layer.openPopup(), 500);
      }
    }
  });
  
  // Xóa circle sau 3 giây
  setTimeout(() => map.removeLayer(circle), 3000);
}


// Render các trạm lên map
export function renderStations(map, stations, icon) {
  stations.forEach((station) => {
    const coords = parsePoint(station.geom);
    if (coords) {
      L.marker(coords, { icon })
        .addTo(map)
        .bindPopup(
          `<strong>ID:</strong> ${station.id} <br> <strong>Name</strong>: ${station.name} <br> <strong>Code</strong>: ${station.code}`
        );
    }
  });
}


// Render các tuyến xe bus lên map
export function renderRoutes(map, routes, parseLine) {
  routes.forEach((route) => {
    const lineCoords = parseLine(route.geom);
    if (lineCoords.length) {
      const color = route.direction === "go" ? "#1E90FF" : "#FF4500";
      
      const polyline = L.polyline(lineCoords, {
        color,
        weight: 6,
        opacity: 0.8,
      }).addTo(map);

      polyline.bindPopup(
        `<strong>Name</strong>: ${route.name} - <strong>Route Code</strong>: ${route.route_code}`
      );
    }
  });
}