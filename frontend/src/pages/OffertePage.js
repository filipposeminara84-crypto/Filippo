import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Tag, TrendingDown, Store, RefreshCw, Loader2, Sparkles, Plus, Check, ShoppingCart } from 'lucide-react';
import { prodottiAPI, supermercatiAPI, prezziAPI } from '../lib/api';
import { formatPrice } from '../lib/utils';
import Layout from '../components/Layout';
import ProductTooltip from '../components/ProductTooltip';

// Helper to read/write quick list from localStorage
const LISTA_KEY = 'shopply_quick_list';
function getQuickList() {
  try { return JSON.parse(localStorage.getItem(LISTA_KEY) || '[]'); } catch { return []; }
}
function saveQuickList(list) {
  localStorage.setItem(LISTA_KEY, JSON.stringify(list));
}

export default function OffertePage() {
  const [offerte, setOfferte] = useState({});
  const [supermercati, setSupermercati] = useState({});
  const [loading, setLoading] = useState(true);
  const [aggiornando, setAggiornando] = useState(false);
  const [ultimoAggiornamento, setUltimoAggiornamento] = useState(null);
  const [filtroCategoria, setFiltroCategoria] = useState('tutte');
  const [categorie, setCategorie] = useState([]);
  const [addedProducts, setAddedProducts] = useState(new Set());
  const [showToast, setShowToast] = useState(null);

  useEffect(() => {
    loadData();
    // Initialize addedProducts from existing quick list
    const existing = getQuickList();
    setAddedProducts(new Set(existing.map(p => p.toLowerCase())));
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
      setTimeout(async () => {
        await loadData();
        setAggiornando(false);
      }, 2000);
    } catch (err) {
      console.error(err);
      setAggiornando(false);
    }
  };

  const handleAddToList = (productName) => {
    const list = getQuickList();
    const lower = productName.toLowerCase();
    if (!list.some(p => p.toLowerCase() === lower)) {
      list.push(productName);
      saveQuickList(list);
    }
    setAddedProducts(prev => new Set([...prev, lower]));
    // Show toast
    setShowToast(productName);
    setTimeout(() => setShowToast(null), 2000);
  };

  const handleRemoveFromList = (productName) => {
    const lower = productName.toLowerCase();
    const list = getQuickList().filter(p => p.toLowerCase() !== lower);
    saveQuickList(list);
    setAddedProducts(prev => {
      const next = new Set(prev);
      next.delete(lower);
      return next;
    });
  };

  const getTotaleOfferte = () => {
    return Object.values(offerte).reduce((acc, prods) => acc + prods.length, 0);
  };

  const getOfferteFiltered = () => {
    if (filtroCategoria === 'tutte') return offerte;
    const filtered = {};
    Object.entries(offerte).forEach(([storeId, prods]) => {
      const filteredProds = prods.filter(p => p.categoria === filtroCategoria);
      if (filteredProds.length > 0) filtered[storeId] = filteredProds;
    });
    return filtered;
  };

  const quickListCount = getQuickList().length;

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
            <h1 className="text-2xl font-bold text-stone-900 flex items-center gap-2" data-testid="offerte-page-title">
              <Sparkles className="w-6 h-6 text-orange-500" />
              Offerte del Giorno
            </h1>
            <p className="text-stone-500">{getTotaleOfferte()} prodotti in promozione</p>
          </div>
          <div className="flex items-center gap-2">
            {quickListCount > 0 && (
              <a
                href="/"
                className="flex items-center gap-1.5 px-3 py-2 bg-emerald-100 text-emerald-700 rounded-xl text-sm font-medium hover:bg-emerald-200 transition-colors"
                data-testid="go-to-list-btn"
              >
                <ShoppingCart className="w-4 h-4" />
                Lista ({quickListCount})
              </a>
            )}
            <button
              onClick={handleAggiornaPrezzi}
              disabled={aggiornando}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white rounded-xl hover:bg-emerald-600 transition-colors disabled:opacity-50"
              data-testid="refresh-prices-btn"
            >
              {aggiornando ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              Aggiorna
            </button>
          </div>
        </div>

        {/* Info banner */}
        <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-3 text-sm text-blue-700 flex items-center gap-2" data-testid="add-info-banner">
          <Plus className="w-4 h-4 flex-shrink-0" />
          Tocca un prodotto per aggiungerlo alla tua lista della spesa
        </div>

        {/* Ultimo aggiornamento */}
        {ultimoAggiornamento?.timestamp && (
          <div className="text-sm text-stone-400">
            Ultimo aggiornamento: {new Date(ultimoAggiornamento.timestamp).toLocaleString('it-IT')}
            {ultimoAggiornamento.nuove_offerte > 0 && (
              <span className="ml-2 text-orange-500">({ultimoAggiornamento.nuove_offerte} nuove offerte)</span>
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
                    <h3 className="font-bold text-white">{supermercati[storeId]?.nome || storeId}</h3>
                    <p className="text-white/80 text-sm">{prods.length} offerte attive</p>
                  </div>
                </div>
              </div>

              <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                {prods.slice(0, 8).map((prod, prodIdx) => {
                  const isAdded = addedProducts.has(prod.nome_prodotto.toLowerCase());
                  return (
                    <button
                      key={prodIdx}
                      onClick={() => isAdded ? handleRemoveFromList(prod.nome_prodotto) : handleAddToList(prod.nome_prodotto)}
                      className={`flex items-center justify-between p-3 rounded-xl text-left transition-all group ${
                        isAdded
                          ? 'bg-emerald-50 border-2 border-emerald-300 ring-1 ring-emerald-200'
                          : 'bg-orange-50 border-2 border-transparent hover:border-emerald-300 hover:shadow-md active:scale-[0.98]'
                      }`}
                      data-testid={`offerta-product-${prodIdx}`}
                    >
                      <div className="flex-1 min-w-0">
                        <ProductTooltip productName={prod.nome_prodotto}>
                          <p className="font-medium text-stone-900 truncate">{prod.nome_prodotto}</p>
                        </ProductTooltip>
                        <p className="text-sm text-stone-500">{prod.brand} - {prod.formato}</p>
                      </div>
                      <div className="flex items-center gap-2 ml-3">
                        <div className="text-right">
                          <div className="flex items-center gap-2">
                            {prod.prezzo_precedente && (
                              <span className="text-sm text-stone-400 line-through">{formatPrice(prod.prezzo_precedente)}</span>
                            )}
                            <span className="font-bold text-orange-600 font-mono">{formatPrice(prod.prezzo)}</span>
                          </div>
                          {prod.sconto_percentuale && (
                            <span className="inline-flex items-center gap-1 text-xs bg-red-500 text-white px-2 py-0.5 rounded-full">
                              <TrendingDown className="w-3 h-3" />-{prod.sconto_percentuale}%
                            </span>
                          )}
                        </div>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-all ${
                          isAdded
                            ? 'bg-emerald-500 text-white'
                            : 'bg-white text-stone-400 group-hover:text-emerald-500 group-hover:bg-emerald-100 border border-stone-200 group-hover:border-emerald-300'
                        }`}>
                          {isAdded ? <Check className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>

              {prods.length > 8 && (
                <div className="px-4 pb-4">
                  <p className="text-sm text-stone-400 text-center">+{prods.length - 8} altre offerte</p>
                </div>
              )}
            </motion.div>
          ))
        )}

        {/* Toast notification */}
        {showToast && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-stone-900 text-white px-5 py-3 rounded-2xl shadow-2xl flex items-center gap-3"
            data-testid="add-to-list-toast"
          >
            <div className="w-7 h-7 bg-emerald-500 rounded-full flex items-center justify-center">
              <Check className="w-4 h-4" />
            </div>
            <span className="font-medium">{showToast}</span>
            <span className="text-stone-400">aggiunto alla lista</span>
          </motion.div>
        )}
      </div>
    </Layout>
  );
}
