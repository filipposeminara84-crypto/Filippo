import React, { useState } from 'react';
import { MapPin, Search, Loader2, X, Navigation, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const LOCATIONS_PIOLTELLO = [
  { nome: "Pioltello Centro", lat: 45.4945, lng: 9.3256 },
  { nome: "Pioltello - Seggiano", lat: 45.4988, lng: 9.3124 },
  { nome: "Segrate", lat: 45.4882, lng: 9.2951 },
  { nome: "Cernusco sul Naviglio", lat: 45.5230, lng: 9.3270 },
  { nome: "Rodano", lat: 45.4782, lng: 9.3526 },
  { nome: "Vignate", lat: 45.4959, lng: 9.3771 },
  { nome: "Pantigliate", lat: 45.4447, lng: 9.3506 },
  { nome: "Limito di Pioltello", lat: 45.5022, lng: 9.3408 },
  { nome: "Milano - Lambrate", lat: 45.4850, lng: 9.2350 },
  { nome: "Vimodrone", lat: 45.5149, lng: 9.2857 },
];

export default function LocationPicker({ currentLocation, onLocationChange, onClose }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [geoLoading, setGeoLoading] = useState(false);

  const handleSearch = async () => {
    if (!searchQuery.trim() || searchQuery.trim().length < 3) return;
    setSearching(true);
    try {
      const resp = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(searchQuery + ', Italia')}&format=json&limit=5&countrycodes=it`
      );
      const data = await resp.json();
      setSearchResults(data.map(r => ({
        nome: r.display_name.split(',').slice(0, 3).join(', '),
        lat: parseFloat(r.lat),
        lng: parseFloat(r.lon),
      })));
    } catch (err) {
      console.error('Geocoding error:', err);
    } finally {
      setSearching(false);
    }
  };

  const handleGPS = () => {
    if (!navigator.geolocation) return;
    setGeoLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        onLocationChange({ lat: pos.coords.latitude, lng: pos.coords.longitude, nome: 'Posizione GPS' });
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
            className="w-full flex items-center justify-center gap-2 h-11 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-xl transition-all active:scale-[0.98] mb-4"
            data-testid="use-gps-btn"
          >
            {geoLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Navigation className="w-4 h-4" />}
            Usa GPS
          </button>

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

          {/* Quick Locations */}
          <div>
            <p className="text-xs text-stone-400 mb-2">Localita comuni</p>
            <div className="space-y-1">
              {LOCATIONS_PIOLTELLO.map((loc) => {
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
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
