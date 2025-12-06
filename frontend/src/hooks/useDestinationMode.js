import { useState, useEffect } from "react";
import L from "leaflet";

export function useDestinationMode(map) {
  const [destinationMode, setDestinationMode] = useState(false);
  const [destination, setDestination] = useState(null);

  // Lắng nghe click trên map khi bật destination mode
  useEffect(() => {
    if (!map || !destinationMode) return;

    const handleClick = (event) => {
      const { lat, lng } = event.latlng;
      setDestination({ lat, lng });
    };

    map.on("click", handleClick);
    return () => map.off("click", handleClick);
  }, [map, destinationMode]);

  // Vẽ marker khi có destination
  useEffect(() => {
    if (!map || !destination) return;

    const marker = L.marker([destination.lat, destination.lng])
      .addTo(map)
      .bindPopup("<b>Điểm Cần Đến!</b>");

    return () => map.removeLayer(marker);
  }, [destination, map]);

  const toggleDestinationMode = () => {
    setDestinationMode(!destinationMode);
  };

  return { 
    destination, 
    destinationMode, 
    toggleDestinationMode 
  };
}