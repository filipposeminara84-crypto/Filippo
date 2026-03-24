import React, { useState } from 'react';
import { MapPin, Search, Loader2, X, Navigation, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const PRESET_LOCATIONS = [
  // Lombardia
  { nome: "Pioltello Centro", lat: 45.4945, lng: 9.3256, regione: "Lombardia" },
  { nome: "Segrate", lat: 45.4882, lng: 9.2951, regione: "Lombardia" },
  { nome: "Cernusco sul Naviglio", lat: 45.5230, lng: 9.3270, regione: "Lombardia" },
  { nome: "Gallarate", lat: 45.6603, lng: 8.7917, regione: "Lombardia" },
  { nome: "Milano - Lambrate", lat: 45.4850, lng: 9.2350, regione: "Lombardia" },
  { nome: "Vimodrone", lat: 45.5149, lng: 9.2857, regione: "Lombardia" },
  // Sicilia
  { nome: "Catania Centro", lat: 37.5079, lng: 15.0830, regione: "Sicilia" },
  { nome: "Catania - Via Galermo", lat: 37.5200, lng: 15.0670, regione: "Sicilia" },
  { nome: "Palermo Centro", lat: 38.1157, lng: 13.3615, regione: "Sicilia" },
  { nome: "Palermo - Forum", lat: 38.1050, lng: 13.3520, regione: "Sicilia" },
];

export default function LocationPicker({ currentLocation, onLocationChange, onClose }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [geoLoading, setGeoLoading] = useState(false);
  const [geoResult, setGeoResult] = useState(null);

  const reverseGeocode = async (lat, lng) => {
    try {
      const resp = await fetch(
        `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json&addressdetails=1&zoom=18`
      );
      const data = await resp.json();
      if (data && data.address) {
        const a = data.address;
        const via = a.road || a.pedestrian || a.footway || '';
        const num = a.house_number || '';
        const citta = a.city || a.town || a.village || a.municipality || '';
        const parts = [via, num, citta].filter(Boolean);
        return parts.join(', ') || data.display_name.split(',').slice(0, 3).join(', ');
      }
      return data.display_name?.split(',').slice(0, 3).join(', ') || null;
    } catch {
      return null;
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim() || searchQuery.trim().length < 3) return;
    setSearching(true);
    try {
      const resp = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(searchQuery + ', Italia')}&format=json&limit=5&countrycodes=it&addressdetails=1`
      );
      const data = await resp.json();
      setSearchResults(data.map(r => {
        const a = r.address || {};
        const via = a.road || a.pedestrian || a.footway || '';
        const num = a.house_number || '';
        const citta = a.city || a.town || a.village || a.municipality || '';
        const parts = [via, num, citta].filter(Boolean);
        return {
          nome: parts.length >= 2 ? parts.join(', ') : r.display_name.split(',').slice(0, 3).join(', '),
          lat: parseFloat(r.lat),
          lng: parseFloat(r.lon),
        };
      }));
    } catch (err) {
      console.error('Geocoding error:', err);
    } finally {
      setSearching(false);
    }
  };

  const handleGPS = () => {
    if (!navigator.geolocation) return;
    setGeoLoading(true);
    setGeoResult(null);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        const address = await reverseGeocode(lat, lng);
        const nome = address || `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
        setGeoResult({ lat, lng, nome });
        setGeoLoading(false);
      },
      (err) => {
        alert('Impossibile ottenere la posizione GPS. Seleziona manualmente.');
        setGeoLoading(false);
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
  };

  const selectLocation = (loc) => {
    onLocationChange(loc);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.95, y: 20 }}
        className="bg-white rounded-2xl shadow-xl w-full max-w-md max-h-[85vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
        data-testid="location-picker-modal"
      >
        <div className="p-5">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-stone-900">Imposta Posizione</h3>
            <button onClick={onClose} className="p-1 hover:bg-stone-100 rounded-lg" data-testid="close-location-picker">
              <X className="w-5 h-5 text-stone-400" />
            </button>
          </div>

          {/* GPS Button */}
          <button
            onClick={handleGPS}
            disabled={geoLoading}
            className="w-full flex items-center justify-center gap-2 h-12 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-xl transition-all active:scale-[0.98] mb-3"
            data-testid="use-gps-btn"
          >
            {geoLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <span className="text-lg">📍</span>}
            Usa posizione attuale
          </button>

          {/* GPS Result */}
          <AnimatePresence>
            {geoResult && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                className="mb-4 bg-emerald-50 border border-emerald-200 rounded-xl p-3"
                data-testid="gps-result"
              >
                <div className="flex items-start gap-2">
                  <MapPin className="w-5 h-5 text-emerald-600 mt-0.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-emerald-800 break-words" data-testid="gps-address">{geoResult.nome}</p>
                    <p className="text-xs text-emerald-600 mt-0.5">{geoResult.lat.toFixed(5)}, {geoResult.lng.toFixed(5)}</p>
                  </div>
                </div>
                <button
                  onClick={() => { onLocationChange(geoResult); }}
                  className="w-full mt-2 flex items-center justify-center gap-1.5 h-9 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-medium rounded-lg transition-all"
                  data-testid="confirm-gps-btn"
                >
                  <Check className="w-4 h-4" />
                  Usa questo indirizzo
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Search */}
          <div className="flex gap-2 mb-4">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Cerca indirizzo o citta..."
              className="flex-1 h-11 px-3 rounded-xl border border-stone-200 bg-stone-50 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 text-sm transition-all"
              data-testid="location-search-input"
            />
            <button
              onClick={handleSearch}
              disabled={searching || !searchQuery.trim()}
              className="h-11 px-3 bg-stone-800 hover:bg-stone-900 text-white rounded-xl transition-all disabled:opacity-50"
              data-testid="location-search-btn"
            >
              {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            </button>
          </div>

          {/* Search Results */}
          <AnimatePresence>
            {searchResults.length > 0 && (
              <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="overflow-hidden mb-4">
                <p className="text-xs text-stone-400 mb-2">Risultati ricerca</p>
                <div className="space-y-1">
                  {searchResults.map((loc, i) => (
                    <button
                      key={i}
                      onClick={() => selectLocation(loc)}
                      className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl hover:bg-emerald-50 transition-colors text-left"
                      data-testid={`search-result-${i}`}
                    >
                      <MapPin className="w-4 h-4 text-emerald-500 shrink-0" />
                      <span className="text-sm text-stone-700 truncate">{loc.nome}</span>
                    </button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Quick Locations by Region */}
          <div>
            <p className="text-xs text-stone-400 mb-2">Lombardia</p>
            <div className="space-y-1 mb-3">
              {PRESET_LOCATIONS.filter(l => l.regione === 'Lombardia').map((loc) => {
                const isSelected = Math.abs(currentLocation.lat - loc.lat) < 0.001 && Math.abs(currentLocation.lng - loc.lng) < 0.001;
                return (
                  <button
                    key={loc.nome}
                    onClick={() => selectLocation(loc)}
                    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition-colors text-left ${
                      isSelected ? 'bg-emerald-100 border border-emerald-200' : 'hover:bg-stone-50'
                    }`}
                    data-testid={`location-${loc.nome.toLowerCase().replace(/\s+/g, '-')}`}
                  >
                    <div className="flex items-center gap-2">
                      <MapPin className={`w-4 h-4 shrink-0 ${isSelected ? 'text-emerald-600' : 'text-stone-400'}`} />
                      <span className={`text-sm ${isSelected ? 'text-emerald-700 font-medium' : 'text-stone-700'}`}>{loc.nome}</span>
                    </div>
                    {isSelected && <Check className="w-4 h-4 text-emerald-600" />}
                  </button>
                );
              })}
            </div>
            <p className="text-xs text-stone-400 mb-2">Sicilia</p>
            <div className="space-y-1 mb-3">
              {PRESET_LOCATIONS.filter(l => l.regione === 'Sicilia').map((loc) => {
                const isSelected = Math.abs(currentLocation.lat - loc.lat) < 0.001 && Math.abs(currentLocation.lng - loc.lng) < 0.001;
                return (
                  <button
                    key={loc.nome}
                    onClick={() => selectLocation(loc)}
                    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition-colors text-left ${
                      isSelected ? 'bg-emerald-100 border border-emerald-200' : 'hover:bg-stone-50'
                    }`}
                    data-testid={`location-${loc.nome.toLowerCase().replace(/\s+/g, '-')}`}
                  >
                    <div className="flex items-center gap-2">
                      <MapPin className={`w-4 h-4 shrink-0 ${isSelected ? 'text-emerald-600' : 'text-stone-400'}`} />
                      <span className={`text-sm ${isSelected ? 'text-emerald-700 font-medium' : 'text-stone-700'}`}>{loc.nome}</span>
                    </div>
                    {isSelected && <Check className="w-4 h-4 text-emerald-600" />}
                  </button>
                );
              })}
            </div>
            <p className="text-xs text-stone-400 italic text-center mt-3">Copertura Lombardia e Sicilia. Espansione nazionale Q2 2026.</p>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
