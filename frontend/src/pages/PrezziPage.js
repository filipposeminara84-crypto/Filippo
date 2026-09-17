import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  RefreshCw, Search, Database, Clock, TrendingDown,
  AlertCircle, Check, Loader2, ChevronDown, ChevronUp, Globe, Layers
} from 'lucide-react';
import { scraperAPI } from '../lib/api';
import { formatPrice } from '../lib/utils';
import Layout from '../components/Layout';

const SOURCE_COLORS = {
  doveconviene: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'DoveConviene' },
  pepesto: { bg: 'bg-emerald-100', text: 'text-emerald-700', label: 'Pepesto API' },
  cross_reference: { bg: 'bg-amber-100', text: 'text-amber-700', label: 'Cross-Ref' },
};

function SourceBadge({ fonte }) {
  const cfg = SOURCE_COLORS[fonte] || { bg: 'bg-stone-100', text: 'text-stone-600', label: fonte };
  return (
    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${cfg.bg} ${cfg.text}`} data-testid={`source-badge-${fonte}`}>
      {cfg.label}
    </span>
  );
}

export default function PrezziPage() {
  const [status, setStatus] = useState(null);
  const [logs, setLogs] = useState([]);
  const [categories, setCategories] = useState({});
  const [availableSources, setAvailableSources] = useState([]);
  const [activeSources, setActiveSources] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [preview, setPreview] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [loadingScrape, setLoadingScrape] = useState(false);
  const [expandedCat, setExpandedCat] = useState(null);
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    let interval;
    if (polling) {
      interval = setInterval(async () => {
        try {
          const res = await scraperAPI.status();
          setStatus(res.data);
          if (!res.data.in_corso) {
            setPolling(false);
            loadData();
          }
        } catch (err) { /* ignore */ }
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [polling]);

  const loadData = async () => {
    try {
      const [statusRes, logsRes, catRes] = await Promise.all([
        scraperAPI.status(),
        scraperAPI.log(10),
        scraperAPI.categories(),
      ]);
      setStatus(statusRes.data);
      setLogs(logsRes.data);
      const catData = catRes.data;
      setCategories(catData.categorie || catData);
      const srcs = catData.fonti_disponibili || ['doveconviene'];
      setAvailableSources(srcs);
      setActiveSources(srcs);
    } catch (err) {
      console.error(err);
    }
  };

  const toggleSource = (src) => {
    setActiveSources(prev =>
      prev.includes(src) ? prev.filter(s => s !== src) : [...prev, src]
    );
  };

  const handleFullScrape = async () => {
    if (activeSources.length === 0) return;
    setLoadingScrape(true);
    try {
      await scraperAPI.run(null, activeSources);
      setPolling(true);
      setStatus(prev => ({ ...prev, in_corso: true, log: ['Scraping multi-fonte avviato...'] }));
    } catch (err) {
      alert(err.response?.data?.detail || 'Errore avvio scraping');
    } finally {
      setLoadingScrape(false);
    }
  };

  const handleSingleScrape = async (term) => {
    setLoadingScrape(true);
    try {
      await scraperAPI.run(term, activeSources);
      setPolling(true);
      setStatus(prev => ({ ...prev, in_corso: true, log: [`Scraping "${term}" avviato...`] }));
    } catch (err) {
      alert(err.response?.data?.detail || 'Errore avvio scraping');
    } finally {
      setLoadingScrape(false);
    }
  };

  const handlePreview = async () => {
    if (!searchTerm.trim()) return;
    setLoadingPreview(true);
    setPreview(null);
    try {
      const res = await scraperAPI.searchPreview(searchTerm.trim(), activeSources);
      setPreview(res.data);
    } catch (err) {
      alert('Errore nella ricerca');
    } finally {
      setLoadingPreview(false);
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-stone-900" data-testid="prezzi-page-title">
            Gestione Prezzi
          </h1>
          <p className="text-stone-500 mt-1">Aggiorna i prezzi da fonti multiple in tempo reale</p>
        </div>

        {/* Status Banner */}
        {status?.in_corso && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-orange-50 border border-orange-200 rounded-2xl p-4 flex items-center gap-3"
            data-testid="scraping-status-banner"
          >
            <Loader2 className="w-5 h-5 text-orange-500 animate-spin" />
            <div className="flex-1">
              <p className="font-medium text-orange-700">Scraping in corso...</p>
              {status.log?.length > 0 && (
                <p className="text-sm text-orange-600 mt-1">{status.log[status.log.length - 1]}</p>
              )}
            </div>
          </motion.div>
        )}

        {/* Source Selection + Quick Actions */}
        <div className="bg-white rounded-2xl shadow-sm border border-stone-100 p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
              <Layers className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 className="font-semibold text-stone-900">Fonti Dati</h2>
              <p className="text-sm text-stone-500">Seleziona le fonti per lo scraping dei prezzi</p>
            </div>
          </div>

          {/* Source Toggles */}
          <div className="flex flex-wrap gap-2 mb-5" data-testid="source-toggles">
            {availableSources.map(src => {
              const cfg = SOURCE_COLORS[src] || { bg: 'bg-stone-100', text: 'text-stone-600', label: src };
              const active = activeSources.includes(src);
              return (
                <button
                  key={src}
                  onClick={() => toggleSource(src)}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-all border ${
                    active
                      ? `${cfg.bg} ${cfg.text} border-current`
                      : 'bg-stone-50 text-stone-400 border-stone-200'
                  }`}
                  data-testid={`source-toggle-${src}`}
                >
                  <div className={`w-2 h-2 rounded-full ${active ? 'bg-current' : 'bg-stone-300'}`} />
                  {cfg.label}
                </button>
              );
            })}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <button
              onClick={handleFullScrape}
              disabled={status?.in_corso || loadingScrape || activeSources.length === 0}
              className="flex items-center justify-center gap-2 h-12 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/30 transition-all active:scale-[0.98] disabled:opacity-50"
              data-testid="full-scrape-btn"
            >
              {loadingScrape ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <RefreshCw className="w-5 h-5" />
              )}
              Aggiorna Tutti i Prezzi ({activeSources.length} {activeSources.length === 1 ? 'fonte' : 'fonti'})
            </button>

            <div className="flex gap-2">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handlePreview()}
                placeholder="Cerca prodotto (es. latte, pasta)..."
                className="flex-1 h-12 px-4 rounded-xl border border-stone-200 bg-stone-50 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                data-testid="search-product-input"
              />
              <button
                onClick={handlePreview}
                disabled={loadingPreview || !searchTerm.trim()}
                className="h-12 px-4 bg-blue-500 hover:bg-blue-600 text-white rounded-xl transition-all disabled:opacity-50 flex items-center gap-1"
                data-testid="search-preview-btn"
              >
                {loadingPreview ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Last Update Info */}
          {status?.ultimo_scraping && (
            <div className="flex items-center gap-2 text-sm text-stone-500">
              <Clock className="w-4 h-4" />
              Ultimo aggiornamento: {new Date(status.ultimo_scraping).toLocaleString('it-IT')}
            </div>
          )}
        </div>

        {/* Preview Results */}
        <AnimatePresence>
          {preview && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="bg-white rounded-2xl shadow-sm border border-stone-100 p-5"
              data-testid="preview-results"
            >
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-stone-900">
                    Risultati per "{preview.search_term}" ({preview.risultati_totali || preview.risultati || 0})
                  </h3>
                  {preview.per_fonte && (
                    <div className="flex flex-wrap gap-1.5 mt-1">
                      {Object.entries(preview.per_fonte).map(([src, count]) => (
                        <span key={src} className="flex items-center gap-1">
                          <SourceBadge fonte={src} />
                          <span className="text-xs text-stone-400">{count}</span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <button
                  onClick={() => handleSingleScrape(preview.search_term)}
                  disabled={status?.in_corso}
                  className="text-sm bg-emerald-100 text-emerald-700 px-3 py-1.5 rounded-lg hover:bg-emerald-200 transition-colors disabled:opacity-50"
                  data-testid="apply-preview-btn"
                >
                  Applica Prezzi
                </button>
              </div>

              {preview.prodotti?.length === 0 ? (
                <p className="text-stone-400 text-center py-4">Nessun risultato trovato</p>
              ) : (
                <div className="space-y-2 max-h-80 overflow-y-auto">
                  {preview.prodotti?.map((p, idx) => (
                    <div key={idx} className="flex items-center justify-between bg-stone-50 px-4 py-3 rounded-xl">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-stone-700 truncate">{p.nome_prodotto}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <p className="text-xs text-stone-500">{p.negozio_originale}</p>
                          <SourceBadge fonte={p.fonte} />
                        </div>
                      </div>
                      <div className="text-right ml-3">
                        <p className="font-semibold text-emerald-600">{formatPrice(p.prezzo)}</p>
                        {p.in_offerta && p.prezzo_precedente && (
                          <p className="text-xs text-stone-400 line-through">{formatPrice(p.prezzo_precedente)}</p>
                        )}
                        {p.sconto_percentuale && (
                          <span className="text-xs bg-red-100 text-red-600 px-1.5 py-0.5 rounded-full">
                            -{p.sconto_percentuale}%
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Categories */}
        <div className="bg-white rounded-2xl shadow-sm border border-stone-100 p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
              <Database className="w-5 h-5 text-purple-600" />
            </div>
            <h2 className="font-semibold text-stone-900">Categorie Disponibili</h2>
          </div>

          <div className="space-y-2">
            {Object.entries(categories).map(([cat, terms]) => (
              <div key={cat} className="border border-stone-100 rounded-xl overflow-hidden">
                <button
                  onClick={() => setExpandedCat(expandedCat === cat ? null : cat)}
                  className="w-full flex items-center justify-between px-4 py-3 hover:bg-stone-50 transition-colors"
                  data-testid={`category-${cat}`}
                >
                  <span className="font-medium text-stone-700">{cat}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-stone-400">{Array.isArray(terms) ? terms.length : 0} termini</span>
                    {expandedCat === cat ? (
                      <ChevronUp className="w-4 h-4 text-stone-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-stone-400" />
                    )}
                  </div>
                </button>

                <AnimatePresence>
                  {expandedCat === cat && Array.isArray(terms) && (
                    <motion.div
                      initial={{ height: 0 }}
                      animate={{ height: 'auto' }}
                      exit={{ height: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="px-4 pb-3 flex flex-wrap gap-2">
                        {terms.map((term) => (
                          <button
                            key={term}
                            onClick={() => {
                              setSearchTerm(term);
                              handleSingleScrape(term);
                            }}
                            disabled={status?.in_corso}
                            className="text-sm bg-stone-100 hover:bg-blue-100 text-stone-600 hover:text-blue-600 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
                            data-testid={`term-${term}`}
                          >
                            {term}
                          </button>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </div>

        {/* Scraping Log */}
        <div className="bg-white rounded-2xl shadow-sm border border-stone-100 p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-orange-100 rounded-xl flex items-center justify-center">
              <Clock className="w-5 h-5 text-orange-600" />
            </div>
            <h2 className="font-semibold text-stone-900">Storico Aggiornamenti</h2>
          </div>

          {logs.length === 0 ? (
            <p className="text-stone-400 text-center py-6">Nessun aggiornamento effettuato</p>
          ) : (
            <div className="space-y-2">
              {logs.map((log) => (
                <div key={log.id} className="flex items-center justify-between bg-stone-50 px-4 py-3 rounded-xl">
                  <div className="flex items-center gap-3">
                    {log.errori > 0 ? (
                      <AlertCircle className="w-5 h-5 text-orange-500" />
                    ) : (
                      <Check className="w-5 h-5 text-emerald-500" />
                    )}
                    <div>
                      <p className="text-sm font-medium text-stone-700">
                        {log.tipo === 'completo' ? 'Aggiornamento Completo' : `Ricerca: ${log.search_term}`}
                      </p>
                      <div className="flex items-center gap-2">
                        <p className="text-xs text-stone-500">
                          {new Date(log.data).toLocaleString('it-IT')}
                        </p>
                        {log.fonti && (
                          <div className="flex gap-1">
                            {log.fonti.map(f => <SourceBadge key={f} fonte={f} />)}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-stone-700">
                      {log.prodotti_aggiornati} aggiornati
                    </p>
                    <div className="flex gap-2 text-xs">
                      {log.nuove_offerte > 0 && (
                        <span className="text-emerald-600 flex items-center gap-1">
                          <TrendingDown className="w-3 h-3" />
                          {log.nuove_offerte} offerte
                        </span>
                      )}
                      {log.errori > 0 && (
                        <span className="text-red-500">{log.errori} errori</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
