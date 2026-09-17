import React, { useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Store, MapPin, Tag } from 'lucide-react';
import { formatPrice } from '../lib/utils';

// Fix Leaflet default icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const CHAIN_COLORS = {
  'Esselunga': '#e30613', 'Coop': '#e2001a', 'Ipercoop': '#e2001a',
  'Conad': '#0055a6', 'Carrefour': '#004e9f', 'Lidl': '#0050aa',
  'Eurospin': '#ffd100', 'Aldi': '#00005f', 'MD': '#e40012',
  'Penny': '#cd1719', 'Despar': '#008c45', 'Unes': '#e5231b',
  'Il Gigante': '#009639', 'Sigma': '#0071bc', 'Pam': '#003da5',
  'Bennet': '#d4002a', 'Famila': '#e3000b', 'Crai': '#e4002b',
  'Iperal': '#009245', 'NaturaSi': '#7ab648', 'Deco': '#f7941d',
};

function makeIcon(chain) {
  const color = CHAIN_COLORS[chain] || '#6b7280';
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 36" width="28" height="40">
    <path d="M12 0C5.4 0 0 5.4 0 12c0 9 12 24 12 24s12-15 12-24C24 5.4 18.6 0 12 0z" fill="${color}" stroke="white" stroke-width="1.5"/>
    <circle cx="12" cy="11" r="5" fill="white"/>
    <text x="12" y="14" text-anchor="middle" font-size="8" font-weight="bold" fill="${color}">${chain.charAt(0)}</text>
  </svg>`;
  return L.divIcon({
    html: svg,
    className: '',
    iconSize: [28, 40],
    iconAnchor: [14, 40],
    popupAnchor: [0, -36],
  });
}

const userIcon = L.divIcon({
  html: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32">
    <circle cx="12" cy="12" r="10" fill="#10b981" stroke="white" stroke-width="3"/>
    <circle cx="12" cy="12" r="4" fill="white"/>
  </svg>`,
  className: '',
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

export default function StoreMap({ stores, userLat, userLng, offerte, onStoreClick }) {
  const storeList = useMemo(() => {
    return Object.values(stores).filter(s => s.lat && s.lng);
  }, [stores]);

  if (!userLat || !userLng || storeList.length === 0) return null;

  return (
    <div className="rounded-2xl overflow-hidden border border-stone-200 shadow-sm" data-testid="store-map">
      <MapContainer
        center={[userLat, userLng]}
        zoom={13}
        style={{ height: '340px', width: '100%' }}
        scrollWheelZoom={true}
        zoomControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* User marker */}
        <Marker position={[userLat, userLng]} icon={userIcon}>
          <Popup><strong>La tua posizione</strong></Popup>
        </Marker>

        {/* Store markers */}
        {storeList.map(store => {
          const storeOffers = offerte[store.id] || [];
          const offerCount = storeOffers.length;
          const bestDiscount = storeOffers.reduce((best, p) =>
            (p.sconto_percentuale || 0) > best ? (p.sconto_percentuale || 0) : best, 0);

          return (
            <Marker
              key={store.id}
              position={[store.lat, store.lng]}
              icon={makeIcon(store.catena || store.nome)}
              eventHandlers={{
                click: () => onStoreClick && onStoreClick(store.id),
              }}
            >
              <Popup>
                <div className="min-w-[180px]">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Store className="w-3.5 h-3.5 text-stone-600" />
                    <span className="font-bold text-sm text-stone-900">{store.nome}</span>
                  </div>
                  {store.indirizzo && (
                    <p className="text-xs text-stone-500 mb-1 flex items-center gap-1">
                      <MapPin className="w-3 h-3" />{store.indirizzo}
                    </p>
                  )}
                  {store.distanza_km != null && (
                    <p className="text-xs text-stone-500 mb-1">{store.distanza_km} km da te</p>
                  )}
                  {offerCount > 0 && (
                    <div className="flex items-center gap-1 mt-1.5 text-xs">
                      <Tag className="w-3 h-3 text-orange-500" />
                      <span className="font-medium text-orange-600">{offerCount} offerte</span>
                      {bestDiscount > 0 && (
                        <span className="bg-red-500 text-white px-1.5 py-0.5 rounded-full text-[10px] font-bold ml-1">
                          fino a -{bestDiscount}%
                        </span>
                      )}
                    </div>
                  )}
                  {offerCount > 0 && (
                    <div className="mt-1.5 space-y-0.5">
                      {storeOffers.slice(0, 3).map((p, i) => (
                        <div key={i} className="text-[11px] text-stone-700 flex justify-between">
                          <span className="truncate mr-2">{p.nome_prodotto}</span>
                          <span className="font-mono font-medium text-orange-600 whitespace-nowrap">{formatPrice(p.prezzo)}</span>
                        </div>
                      ))}
                      {offerCount > 3 && (
                        <p className="text-[10px] text-stone-400">+{offerCount - 3} altre</p>
                      )}
                    </div>
                  )}
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}
