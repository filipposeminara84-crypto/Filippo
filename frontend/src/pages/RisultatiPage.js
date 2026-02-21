import React, { useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import { motion } from 'framer-motion';
import {
  ArrowLeft, Navigation, Clock, Wallet, TrendingDown,
  MapPin, Store, ChevronDown, ChevronUp, ExternalLink
} from 'lucide-react';
import { formatPrice, formatTime } from '../lib/utils';
import Layout from '../components/Layout';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet default icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom markers
const createCustomIcon = (number, color) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      background: ${color};
      color: white;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
      font-size: 14px;
      border: 3px solid white;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    ">${number}</div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
};

const userIcon = L.divIcon({
  className: 'user-marker',
  html: `<div style="
    background: #3B82F6;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    border: 3px solid white;
    box-shadow: 0 0 0 8px rgba(59, 130, 246, 0.3);
  "></div>`,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
});

function FitBounds({ bounds }) {
  const map = useMap();
  React.useEffect(() => {
    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [bounds, map]);
  return null;
}

export default function RisultatiPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { risultato, listaOriginale } = location.state || {};
  const [expandedStore, setExpandedStore] = React.useState(null);
  const [userPosition] = React.useState({ lat: 45.4945, lng: 9.3256 });

  if (!risultato) {
    return (
      <Layout>
        <div className="text-center py-12">
          <p className="text-stone-500">Nessun risultato disponibile</p>
          <button
            onClick={() => navigate('/')}
            className="mt-4 text-emerald-600 hover:underline"
          >
            Torna alla home
          </button>
        </div>
      </Layout>
    );
  }

  const { piano_ottimale, costo_totale, tempo_stimato_min, risparmio_euro, risparmio_percentuale, distanza_totale_km } = risultato;

  // Calculate map bounds
  const bounds = useMemo(() => {
    const points = [[userPosition.lat, userPosition.lng]];
    piano_ottimale.forEach(item => {
      points.push([item.supermercato.lat, item.supermercato.lng]);
    });
    return points;
  }, [piano_ottimale, userPosition]);

  // Polyline coordinates
  const polylinePositions = useMemo(() => {
    const positions = [[userPosition.lat, userPosition.lng]];
    piano_ottimale.forEach(item => {
      positions.push([item.supermercato.lat, item.supermercato.lng]);
    });
    return positions;
  }, [piano_ottimale, userPosition]);

  // Open navigation in Google Maps
  const openNavigation = () => {
    const waypoints = piano_ottimale.map(item => 
      `${item.supermercato.lat},${item.supermercato.lng}`
    ).join('/');
    const url = `https://www.google.com/maps/dir/${userPosition.lat},${userPosition.lng}/${waypoints}`;
    window.open(url, '_blank');
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Back Button */}
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-stone-600 hover:text-stone-900 transition-colors"
          data-testid="back-btn"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Nuova ricerca</span>
        </button>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-2xl border border-stone-100 p-4"
          >
            <div className="flex items-center gap-2 text-stone-500 mb-1">
              <Wallet className="w-4 h-4" />
              <span className="text-sm">Totale</span>
            </div>
            <p className="text-2xl font-bold text-stone-900 font-mono" data-testid="total-cost">
              {formatPrice(costo_totale)}
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-emerald-50 rounded-2xl border border-emerald-100 p-4 savings-pulse"
          >
            <div className="flex items-center gap-2 text-emerald-600 mb-1">
              <TrendingDown className="w-4 h-4" />
              <span className="text-sm">Risparmio</span>
            </div>
            <p className="text-2xl font-bold text-emerald-600 font-mono" data-testid="savings">
              {formatPrice(risparmio_euro)}
            </p>
            <p className="text-xs text-emerald-500">-{risparmio_percentuale}%</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-2xl border border-stone-100 p-4"
          >
            <div className="flex items-center gap-2 text-stone-500 mb-1">
              <Clock className="w-4 h-4" />
              <span className="text-sm">Tempo</span>
            </div>
            <p className="text-2xl font-bold text-stone-900" data-testid="time-estimate">
              {formatTime(tempo_stimato_min)}
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-2xl border border-stone-100 p-4"
          >
            <div className="flex items-center gap-2 text-stone-500 mb-1">
              <Store className="w-4 h-4" />
              <span className="text-sm">Negozi</span>
            </div>
            <p className="text-2xl font-bold text-stone-900" data-testid="store-count">
              {piano_ottimale.length}
            </p>
            <p className="text-xs text-stone-500">{distanza_totale_km} km</p>
          </motion.div>
        </div>

        {/* Map */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4 }}
          className="bg-white rounded-2xl shadow-sm border border-stone-100 overflow-hidden"
        >
          <div className="h-[300px] md:h-[400px]" data-testid="map-container">
            <MapContainer
              center={[userPosition.lat, userPosition.lng]}
              zoom={13}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              
              {/* User Position */}
              <Marker position={[userPosition.lat, userPosition.lng]} icon={userIcon}>
                <Popup>La tua posizione</Popup>
              </Marker>

              {/* Store Markers */}
              {piano_ottimale.map((item, idx) => (
                <Marker
                  key={item.supermercato.id}
                  position={[item.supermercato.lat, item.supermercato.lng]}
                  icon={createCustomIcon(idx + 1, idx === 0 ? '#10B981' : '#F97316')}
                >
                  <Popup>
                    <div className="font-sans">
                      <p className="font-bold">{item.supermercato.nome}</p>
                      <p className="text-sm text-gray-600">{item.supermercato.indirizzo}</p>
                      <p className="text-sm font-medium text-emerald-600 mt-1">
                        Subtotale: {formatPrice(item.subtotale)}
                      </p>
                    </div>
                  </Popup>
                </Marker>
              ))}

              {/* Route Line */}
              <Polyline
                positions={polylinePositions}
                color="#10B981"
                weight={4}
                opacity={0.7}
                dashArray="10, 10"
              />

              <FitBounds bounds={bounds} />
            </MapContainer>
          </div>
        </motion.div>

        {/* Navigation Button */}
        <motion.button
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          onClick={openNavigation}
          className="w-full h-14 bg-emerald-500 hover:bg-emerald-600 text-white font-bold rounded-2xl shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/40 transition-all active:scale-[0.98] flex items-center justify-center gap-3"
          data-testid="start-navigation-btn"
        >
          <Navigation className="w-5 h-5" />
          AVVIA NAVIGAZIONE
          <ExternalLink className="w-4 h-4" />
        </motion.button>

        {/* Store Details */}
        <div className="space-y-3">
          <h3 className="font-semibold text-stone-900">Dettaglio per Supermercato</h3>
          
          {piano_ottimale.map((item, idx) => (
            <motion.div
              key={item.supermercato.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.6 + idx * 0.1 }}
              className="bg-white rounded-2xl border border-stone-100 overflow-hidden"
            >
              <button
                onClick={() => setExpandedStore(expandedStore === idx ? null : idx)}
                className="w-full flex items-center justify-between p-4 hover:bg-stone-50 transition-colors"
                data-testid={`store-card-${idx}`}
              >
                <div className="flex items-center gap-4">
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold"
                    style={{ background: idx === 0 ? '#10B981' : '#F97316' }}
                  >
                    {idx + 1}
                  </div>
                  <div className="text-left">
                    <p className="font-semibold text-stone-900">{item.supermercato.nome}</p>
                    <p className="text-sm text-stone-500">{item.prodotti.length} prodotti</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <p className="font-bold text-stone-900 font-mono">{formatPrice(item.subtotale)}</p>
                  {expandedStore === idx ? (
                    <ChevronUp className="w-5 h-5 text-stone-400" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-stone-400" />
                  )}
                </div>
              </button>

              {expandedStore === idx && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="border-t border-stone-100"
                >
                  <div className="p-4 space-y-2">
                    {item.prodotti.map((prod, prodIdx) => (
                      <div
                        key={prodIdx}
                        className="flex items-center justify-between py-2 border-b border-stone-50 last:border-0"
                      >
                        <span className="text-stone-700">{prod.prodotto}</span>
                        <span className="font-mono text-stone-900">{formatPrice(prod.prezzo)}</span>
                      </div>
                    ))}
                  </div>
                  <div className="px-4 pb-4">
                    <div className="bg-stone-50 rounded-xl p-3">
                      <p className="text-sm text-stone-500">
                        <MapPin className="w-4 h-4 inline mr-1" />
                        {item.supermercato.indirizzo}
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
