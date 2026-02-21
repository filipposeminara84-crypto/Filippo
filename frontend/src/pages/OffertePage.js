import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Tag, TrendingDown, Store, RefreshCw, Loader2, Sparkles } from 'lucide-react';
import { prodottiAPI, supermercatiAPI, prezziAPI } from '../lib/api';
import { formatPrice } from '../lib/utils';
import Layout from '../components/Layout';

export default function OffertePage() {
  const [offerte, setOfferte] = useState({});
  const [supermercati, setSupermercati] = useState({});
  const [loading, setLoading] = useState(true);
  const [aggiornando, setAggiornando] = useState(false);
  const [ultimoAggiornamento, setUltimoAggiornamento] = useState(null);
  const [filtroCategoria, setFiltroCategoria] = useState('tutte');
  const [categorie, setCategorie] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [offerteRes, supRes, catRes, aggRes] = await Promise.all([
        prodottiAPI.getOfferte(),
        supermercatiAPI.getAll(),
        prodottiAPI.getCategorie(),
        prezziAPI.ultimoAggiornamento()
      ]);
      
      setOfferte(offerteRes.data);
      const supMap = {};
      supRes.data.forEach(s => supMap[s.id] = s);
      setSupermercati(supMap);
      setCategorie(catRes.data);
      setUltimoAggiornamento(aggRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAggiornaPrezzi = async () => {
    setAggiornando(true);
    try {
      await prezziAPI.aggiorna();
      // Wait a bit for background task
      setTimeout(async () => {
        await loadData();
        setAggiornando(false);
      }, 2000);
    } catch (err) {
      console.error(err);
      setAggiornando(false);
    }
  };

  const getTotaleOfferte = () => {
    return Object.values(offerte).reduce((acc, prods) => acc + prods.length, 0);
  };

  const getOfferteFiltered = () => {
    if (filtroCategoria === 'tutte') return offerte;
    
    const filtered = {};
    Object.entries(offerte).forEach(([storeId, prods]) => {
      const filteredProds = prods.filter(p => p.categoria === filtroCategoria);
      if (filteredProds.length > 0) {
        filtered[storeId] = filteredProds;
      }
    });
    return filtered;
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

  const offerteFiltered = getOfferteFiltered();

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-stone-900 flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-orange-500" />
              Offerte del Giorno
            </h1>
            <p className="text-stone-500">{getTotaleOfferte()} prodotti in promozione</p>
          </div>
          <button
            onClick={handleAggiornaPrezzi}
            disabled={aggiornando}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white rounded-xl hover:bg-emerald-600 transition-colors disabled:opacity-50"
            data-testid="refresh-prices-btn"
          >
            {aggiornando ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            Aggiorna Prezzi
          </button>
        </div>

        {/* Ultimo aggiornamento */}
        {ultimoAggiornamento?.timestamp && (
          <div className="text-sm text-stone-400">
            Ultimo aggiornamento: {new Date(ultimoAggiornamento.timestamp).toLocaleString('it-IT')}
            {ultimoAggiornamento.nuove_offerte > 0 && (
              <span className="ml-2 text-orange-500">
                ({ultimoAggiornamento.nuove_offerte} nuove offerte)
              </span>
            )}
          </div>
        )}

        {/* Filtro Categorie */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          <button
            onClick={() => setFiltroCategoria('tutte')}
            className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
              filtroCategoria === 'tutte'
                ? 'bg-emerald-500 text-white'
                : 'bg-white text-stone-600 border border-stone-200 hover:bg-stone-50'
            }`}
          >
            Tutte
          </button>
          {categorie.map(cat => (
            <button
              key={cat}
              onClick={() => setFiltroCategoria(cat)}
              className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
                filtroCategoria === cat
                  ? 'bg-emerald-500 text-white'
                  : 'bg-white text-stone-600 border border-stone-200 hover:bg-stone-50'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Offerte per Supermercato */}
        {Object.keys(offerteFiltered).length === 0 ? (
          <div className="bg-white rounded-2xl border border-stone-100 p-12 text-center">
            <Tag className="w-12 h-12 mx-auto text-stone-300 mb-4" />
            <p className="text-stone-500">Nessuna offerta disponibile</p>
            <p className="text-sm text-stone-400 mt-1">Prova ad aggiornare i prezzi</p>
          </div>
        ) : (
          Object.entries(offerteFiltered).map(([storeId, prods], idx) => (
            <motion.div
              key={storeId}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="bg-white rounded-2xl border border-stone-100 overflow-hidden"
            >
              <div className="bg-gradient-to-r from-orange-500 to-red-500 px-5 py-4">
                <div className="flex items-center gap-3">
                  <Store className="w-5 h-5 text-white" />
                  <div>
                    <h3 className="font-bold text-white">
                      {supermercati[storeId]?.nome || storeId}
                    </h3>
                    <p className="text-white/80 text-sm">
                      {prods.length} offerte attive
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                {prods.slice(0, 8).map((prod, prodIdx) => (
                  <div
                    key={prodIdx}
                    className="flex items-center justify-between p-3 bg-orange-50 rounded-xl"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-stone-900 truncate">{prod.nome_prodotto}</p>
                      <p className="text-sm text-stone-500">{prod.brand} - {prod.formato}</p>
                    </div>
                    <div className="text-right ml-3">
                      <div className="flex items-center gap-2">
                        {prod.prezzo_precedente && (
                          <span className="text-sm text-stone-400 line-through">
                            {formatPrice(prod.prezzo_precedente)}
                          </span>
                        )}
                        <span className="font-bold text-orange-600 font-mono">
                          {formatPrice(prod.prezzo)}
                        </span>
                      </div>
                      {prod.sconto_percentuale && (
                        <span className="inline-flex items-center gap-1 text-xs bg-red-500 text-white px-2 py-0.5 rounded-full">
                          <TrendingDown className="w-3 h-3" />
                          -{prod.sconto_percentuale}%
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {prods.length > 8 && (
                <div className="px-4 pb-4">
                  <p className="text-sm text-stone-400 text-center">
                    +{prods.length - 8} altre offerte
                  </p>
                </div>
              )}
            </motion.div>
          ))
        )}
      </div>
    </Layout>
  );
}
