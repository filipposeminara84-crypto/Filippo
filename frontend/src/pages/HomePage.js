import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShoppingCart, Plus, X, Search, Save, List, Loader2,
  MapPin, Clock, Wallet, Sparkles, ChevronRight, Trash2
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { prodottiAPI, listeAPI, ottimizzaAPI, preferenzeAPI } from '../lib/api';
import { formatPrice } from '../lib/utils';
import Layout from '../components/Layout';

export default function HomePage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [listaSpesa, setListaSpesa] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [listeSalvate, setListeSalvate] = useState([]);
  const [loading, setLoading] = useState(false);
  const [ottimizzando, setOttimizzando] = useState(false);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [nomeListaSalvataggio, setNomeListaSalvataggio] = useState('');
  const [userLocation, setUserLocation] = useState({ lat: 45.4945, lng: 9.3256 }); // Default Pioltello
  const [preferenze, setPreferenze] = useState(null);
  
  const inputRef = useRef(null);

  useEffect(() => {
    loadListeSalvate();
    loadPreferenze();
    getUserLocation();
  }, []);

  const loadListeSalvate = async () => {
    try {
      const res = await listeAPI.getAll();
      setListeSalvate(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadPreferenze = async () => {
    try {
      const res = await preferenzeAPI.get();
      setPreferenze(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const getUserLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setUserLocation({
            lat: pos.coords.latitude,
            lng: pos.coords.longitude
          });
        },
        () => {
          // Use default Pioltello location
          console.log('Using default location');
        }
      );
    }
  };

  const handleInputChange = async (e) => {
    const value = e.target.value;
    setInputValue(value);
    
    if (value.length >= 2) {
      try {
        const res = await prodottiAPI.autocomplete(value);
        setSuggestions(res.data);
        setShowSuggestions(true);
      } catch (err) {
        console.error(err);
      }
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const addProdotto = (prodotto) => {
    if (prodotto && !listaSpesa.includes(prodotto) && listaSpesa.length < 50) {
      setListaSpesa([...listaSpesa, prodotto]);
    }
    setInputValue('');
    setSuggestions([]);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const removeProdotto = (prodotto) => {
    setListaSpesa(listaSpesa.filter(p => p !== prodotto));
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && inputValue.trim()) {
      e.preventDefault();
      addProdotto(inputValue.trim());
    }
  };

  const loadListaSalvata = (lista) => {
    setListaSpesa(lista.prodotti);
  };

  const saveCurrentList = async () => {
    if (!nomeListaSalvataggio.trim() || listaSpesa.length === 0) return;
    
    setLoading(true);
    try {
      await listeAPI.create({
        nome: nomeListaSalvataggio,
        prodotti: listaSpesa
      });
      await loadListeSalvate();
      setShowSaveModal(false);
      setNomeListaSalvataggio('');
    } catch (err) {
      alert(err.response?.data?.detail || 'Errore nel salvataggio');
    } finally {
      setLoading(false);
    }
  };

  const deleteLista = async (listaId, e) => {
    e.stopPropagation();
    try {
      await listeAPI.delete(listaId);
      await loadListeSalvate();
    } catch (err) {
      console.error(err);
    }
  };

  const handleOttimizza = async () => {
    if (listaSpesa.length === 0) return;
    
    setOttimizzando(true);
    try {
      const res = await ottimizzaAPI.ottimizza({
        lista_prodotti: listaSpesa,
        lat_utente: userLocation.lat,
        lng_utente: userLocation.lng,
        raggio_km: preferenze?.raggio_max_km || 5,
        max_supermercati: preferenze?.max_supermercati || 3,
        peso_prezzo: preferenze?.peso_prezzo || 0.7,
        peso_tempo: preferenze?.peso_tempo || 0.3
      });
      
      navigate('/risultati', { state: { risultato: res.data, listaOriginale: listaSpesa } });
    } catch (err) {
      alert(err.response?.data?.detail || 'Errore nell\'ottimizzazione');
    } finally {
      setOttimizzando(false);
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Welcome Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-stone-900">
              Ciao, {user?.nome}! 👋
            </h1>
            <p className="text-stone-500 mt-1">Cosa devi comprare oggi?</p>
          </div>
          
          {user?.statistiche && (
            <div className="hidden md:flex items-center gap-2 bg-emerald-50 px-4 py-2 rounded-xl">
              <Sparkles className="w-5 h-5 text-emerald-500" />
              <span className="text-sm font-medium text-emerald-700">
                Risparmiati: {formatPrice(user.statistiche.risparmio_totale_euro || 0)}
              </span>
            </div>
          )}
        </div>

        {/* Input Lista */}
        <div className="bg-white rounded-2xl shadow-sm border border-stone-100 p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
              <ShoppingCart className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <h2 className="font-semibold text-stone-900">Lista della Spesa</h2>
              <p className="text-sm text-stone-500">{listaSpesa.length}/50 prodotti</p>
            </div>
          </div>

          {/* Search Input */}
          <div className="relative mb-4">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-stone-400" />
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              placeholder="Aggiungi prodotto..."
              className="w-full h-12 pl-12 pr-4 rounded-xl border border-stone-200 bg-stone-50 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
              data-testid="product-input"
            />
            
            {/* Suggestions Dropdown */}
            <AnimatePresence>
              {showSuggestions && suggestions.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-lg border border-stone-200 z-20 overflow-hidden"
                >
                  {suggestions.map((sug, idx) => (
                    <button
                      key={idx}
                      onClick={() => addProdotto(sug)}
                      className="w-full px-4 py-3 text-left hover:bg-emerald-50 text-stone-700 hover:text-emerald-700 transition-colors border-b border-stone-100 last:border-0"
                      data-testid={`suggestion-${idx}`}
                    >
                      {sug}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Lista Prodotti */}
          <div className="space-y-2 max-h-64 overflow-y-auto">
            <AnimatePresence>
              {listaSpesa.map((prodotto, idx) => (
                <motion.div
                  key={prodotto}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20, height: 0 }}
                  className="flex items-center justify-between bg-stone-50 px-4 py-3 rounded-xl group"
                >
                  <span className="text-stone-700">{prodotto}</span>
                  <button
                    onClick={() => removeProdotto(prodotto)}
                    className="text-stone-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                    data-testid={`remove-product-${idx}`}
                  >
                    <X className="w-5 h-5" />
                  </button>
                </motion.div>
              ))}
            </AnimatePresence>
            
            {listaSpesa.length === 0 && (
              <div className="text-center py-8 text-stone-400">
                <ShoppingCart className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>La lista è vuota</p>
                <p className="text-sm">Inizia ad aggiungere prodotti</p>
              </div>
            )}
          </div>

          {/* Actions */}
          {listaSpesa.length > 0 && (
            <div className="flex gap-3 mt-4 pt-4 border-t border-stone-100">
              <button
                onClick={() => setShowSaveModal(true)}
                className="flex items-center gap-2 px-4 py-2 text-stone-600 hover:bg-stone-100 rounded-xl transition-colors"
                data-testid="save-list-btn"
              >
                <Save className="w-4 h-4" />
                Salva
              </button>
              <button
                onClick={handleOttimizza}
                disabled={ottimizzando}
                className="flex-1 flex items-center justify-center gap-2 h-12 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/30 transition-all active:scale-[0.98] disabled:opacity-50"
                data-testid="optimize-btn"
              >
                {ottimizzando ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Sparkles className="w-5 h-5" />
                )}
                Ottimizza Spesa
              </button>
            </div>
          )}
        </div>

        {/* Liste Salvate */}
        {listeSalvate.length > 0 && (
          <div className="bg-white rounded-2xl shadow-sm border border-stone-100 p-5">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-orange-100 rounded-xl flex items-center justify-center">
                <List className="w-5 h-5 text-orange-600" />
              </div>
              <h2 className="font-semibold text-stone-900">Liste Salvate</h2>
            </div>
            
            <div className="space-y-2">
              {listeSalvate.map((lista) => (
                <div
                  key={lista.id}
                  onClick={() => loadListaSalvata(lista)}
                  className="flex items-center justify-between px-4 py-3 bg-stone-50 rounded-xl cursor-pointer hover:bg-orange-50 transition-colors group"
                  data-testid={`saved-list-${lista.id}`}
                >
                  <div>
                    <p className="font-medium text-stone-700 group-hover:text-orange-700">{lista.nome}</p>
                    <p className="text-sm text-stone-500">{lista.prodotti.length} prodotti</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => deleteLista(lista.id, e)}
                      className="p-2 text-stone-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                      data-testid={`delete-list-${lista.id}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    <ChevronRight className="w-5 h-5 text-stone-400 group-hover:text-orange-500" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick Stats */}
        {user?.statistiche && (
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-white rounded-2xl border border-stone-100 p-4">
              <p className="text-2xl font-bold text-emerald-600">{user.statistiche.spese_totali || 0}</p>
              <p className="text-sm text-stone-500">Spese completate</p>
            </div>
            <div className="bg-white rounded-2xl border border-stone-100 p-4">
              <p className="text-2xl font-bold text-orange-500">{formatPrice(user.statistiche.risparmio_totale_euro || 0)}</p>
              <p className="text-sm text-stone-500">Risparmiati</p>
            </div>
            <div className="bg-white rounded-2xl border border-stone-100 p-4">
              <p className="text-2xl font-bold text-blue-500">{user.statistiche.tempo_totale_risparmiato_min || 0}</p>
              <p className="text-sm text-stone-500">Min risparmiati</p>
            </div>
          </div>
        )}
      </div>

      {/* Save Modal */}
      <AnimatePresence>
        {showSaveModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={() => setShowSaveModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-2xl p-6 w-full max-w-sm"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-bold text-stone-900 mb-4">Salva Lista</h3>
              <input
                type="text"
                value={nomeListaSalvataggio}
                onChange={(e) => setNomeListaSalvataggio(e.target.value)}
                placeholder="Nome della lista"
                className="w-full h-12 px-4 rounded-xl border border-stone-200 bg-stone-50 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 mb-4"
                data-testid="list-name-input"
                autoFocus
              />
              <div className="flex gap-3">
                <button
                  onClick={() => setShowSaveModal(false)}
                  className="flex-1 h-12 border border-stone-200 text-stone-600 font-medium rounded-xl hover:bg-stone-50 transition-colors"
                >
                  Annulla
                </button>
                <button
                  onClick={saveCurrentList}
                  disabled={loading || !nomeListaSalvataggio.trim()}
                  className="flex-1 h-12 bg-emerald-500 text-white font-medium rounded-xl hover:bg-emerald-600 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                  data-testid="confirm-save-btn"
                >
                  {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                  Salva
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </Layout>
  );
}
