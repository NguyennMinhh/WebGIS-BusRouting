import { useState } from "react";
import L from "leaflet";
import { userIcon } from "../utils/icon";

export function useUserLocation(map) {
  const [userLocation, setUserLocation] = useState(null);
  const [userMarker, setUserMarker] = useState(null); // Lưu marker để xóa sau

  const addUserLocation = () => {
    if (!map) {
      console.warn("Map chưa sẵn sàng, vui lòng đợi...");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        const location = { latitude, longitude };
        
        setUserLocation(location);
        
        // Xóa marker cũ nếu có
        if (userMarker) {
          map.removeLayer(userMarker);
        }
        
        // Thêm marker mới
        const newMarker = L.marker([latitude, longitude], { icon: userIcon })
          .addTo(map)
          .bindPopup("<b>Bạn đang ở đây!</b>")
          .openPopup();
        
        setUserMarker(newMarker);
        map.setView([latitude, longitude], 15);
      },
      (error) => {
        console.error("Lỗi lấy vị trí:", error);
        
        // Xử lý các loại lỗi cụ thể
        let errorMessage = "Không thể lấy vị trí.";
        switch(error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = "Bạn đã từ chối quyền truy cập vị trí. Vui lòng bật trong cài đặt trình duyệt.";
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = "Không thể xác định vị trí. Vui lòng kiểm tra GPS.";
            break;
          case error.TIMEOUT:
            errorMessage = "Yêu cầu vị trí hết thời gian. Vui lòng thử lại.";
            break;
          default:
            errorMessage = "Lỗi không xác định khi lấy vị trí.";
        }
        
        alert(errorMessage);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    );
  };

  return { userLocation, addUserLocation };
}