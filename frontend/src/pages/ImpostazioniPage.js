import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Settings, MapPin, Store, Wallet, Clock, Save, Loader2, Check } from 'lucide-react';
import { preferenzeAPI, supermercatiAPI, authAPI } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/Layout';

export default function ImpostazioniPage() {
  const { user, updateUser } = useAuth();
  const [preferenze, setPreferenze] = useState({
    raggio_max_km: 5,
    max_supermercati: 3,
    peso_prezzo: 0.7,
    peso_tempo: 0.3,
    supermercati_preferiti: []
  });
  const [supermercati, setSupermercati] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [prefRes, supRes] = await Promise.all([
        preferenzeAPI.get(),
        supermercatiAPI.getAll()
      ]);
      setPreferenze(prefRes.data);
      setSupermercati(supRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSliderChange = (value) => {
    const pesoPrezzo = value / 100;
    setPreferenze(prev => ({
      ...prev,
      peso_prezzo: pesoPrezzo,
      peso_tempo: 1 - pesoPrezzo
    }));
  };

  const toggleSupermercato = (id) => {
    setPreferenze(prev => {
      const isSelected = prev.supermercati_preferiti.includes(id);
      return {
        ...prev,
        supermercati_preferiti: isSelected
          ? prev.supermercati_preferiti.filter(s => s !== id)
          : [...prev.supermercati_preferiti, id]
      };
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await preferenzeAPI.update(preferenze);
      const userRes = await authAPI.getMe();
      updateUser(userRes.data);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      alert('Errore nel salvataggio');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-stone-900">Impostazioni</h1>
          <p className="text-stone-500">Personalizza le tue preferenze di ricerca</p>
        </div>

        {/* Raggio di Ricerca */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl border border-stone-100 p-5"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
              <MapPin className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-stone-900">Raggio di Ricerca</h3>
              <p className="text-sm text-stone-500">Distanza massima dai supermercati</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <input
              type="range"
              min="1"
              max="10"
              value={preferenze.raggio_max_km}
              onChange={(e) => setPreferenze(prev => ({ ...prev, raggio_max_km: parseInt(e.target.value) }))}
              className="flex-1 h-2 bg-stone-200 rounded-lg appearance-none cursor-pointer accent-blue-500"
              data-testid="radius-slider"
            />
            <span className="text-lg font-bold text-stone-900 w-16 text-right">
              {preferenze.raggio_max_km} km
            </span>
          </div>
        </motion.div>

        {/* Max Supermercati */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-2xl border border-stone-100 p-5"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-orange-100 rounded-xl flex items-center justify-center">
              <Store className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <h3 className="font-semibold text-stone-900">Numero Massimo Supermercati</h3>
              <p className="text-sm text-stone-500">Quanti negozi visitare al massimo</p>
            </div>
          </div>

          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((num) => (
              <button
                key={num}
                onClick={() => setPreferenze(prev => ({ ...prev, max_supermercati: num }))}
                className={`flex-1 h-12 rounded-xl font-semibold transition-all ${
                  preferenze.max_supermercati === num
                    ? 'bg-orange-500 text-white shadow-lg shadow-orange-500/30'
                    : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
                }`}
                data-testid={`max-stores-${num}`}
              >
                {num}
              </button>
            ))}
          </div>
        </motion.div>

        {/* Priorità Prezzo/Tempo */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-2xl border border-stone-100 p-5"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
              <Wallet className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <h3 className="font-semibold text-stone-900">Priorità Ottimizzazione</h3>
              <p className="text-sm text-stone-500">Bilancia risparmio e tempo</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex justify-between text-sm">
              <div className="flex items-center gap-2 text-emerald-600">
                <Wallet className="w-4 h-4" />
                <span>Risparmio ({Math.round(preferenze.peso_prezzo * 100)}%)</span>
              </div>
              <div className="flex items-center gap-2 text-blue-600">
                <span>Tempo ({Math.round(preferenze.peso_tempo * 100)}%)</span>
                <Clock className="w-4 h-4" />
              </div>
            </div>

            <input
              type="range"
              min="0"
              max="100"
              value={Math.round(preferenze.peso_prezzo * 100)}
              onChange={(e) => handleSliderChange(parseInt(e.target.value))}
              className="w-full h-3 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, #10B981 ${preferenze.peso_prezzo * 100}%, #3B82F6 ${preferenze.peso_prezzo * 100}%)`
              }}
              data-testid="priority-slider"
            />

            <div className="flex justify-between text-xs text-stone-400">
              <span>Massimo risparmio</span>
              <span>Percorso più veloce</span>
            </div>
          </div>
        </motion.div>

        {/* Supermercati Preferiti */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-2xl border border-stone-100 p-5"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
              <Store className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h3 className="font-semibold text-stone-900">Supermercati Preferiti</h3>
              <p className="text-sm text-stone-500">Seleziona i tuoi negozi preferiti</p>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {supermercati.map((sup) => (
              <button
                key={sup.id}
                onClick={() => toggleSupermercato(sup.id)}
                className={`p-3 rounded-xl border-2 text-left transition-all ${
                  preferenze.supermercati_preferiti.includes(sup.id)
                    ? 'border-emerald-500 bg-emerald-50'
                    : 'border-stone-200 hover:border-stone-300'
                }`}
                data-testid={`store-pref-${sup.id}`}
              >
                <p className="font-medium text-stone-900 text-sm">{sup.catena}</p>
                <p className="text-xs text-stone-500 truncate">{sup.nome}</p>
              </button>
            ))}
          </div>
        </motion.div>

        {/* Save Button */}
        <motion.button
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          onClick={handleSave}
          disabled={saving}
          className={`w-full h-14 font-bold rounded-2xl shadow-lg transition-all active:scale-[0.98] flex items-center justify-center gap-3 ${
            saved
              ? 'bg-emerald-500 text-white shadow-emerald-500/30'
              : 'bg-stone-900 text-white shadow-stone-900/30 hover:bg-stone-800'
          }`}
          data-testid="save-preferences-btn"
        >
          {saving ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : saved ? (
            <>
              <Check className="w-5 h-5" />
              Salvato!
            </>
          ) : (
            <>
              <Save className="w-5 h-5" />
              Salva Preferenze
            </>
          )}
        </motion.button>
      </div>
    </Layout>
  );
}
