import React, { useState, useEffect, useMemo, useRef } from 'react';
import { motion } from 'framer-motion';
import { Tag, TrendingDown, Store, RefreshCw, Loader2, Sparkles, Plus, Check, ShoppingCart, MapPin, Repeat, Star, Zap, Heart, Map, List } from 'lucide-react';
import { prodottiAPI, supermercatiAPI, prezziAPI, raccomandazioniAPI } from '../lib/api';
import { formatPrice } from '../lib/utils';
import Layout from '../components/Layout';
import ProductTooltip from '../components/ProductTooltip';
import StoreMap from '../components/StoreMap';

const LISTA_KEY = 'shopply_quick_list';
function getQuickList() {
  try { return JSON.parse(localStorage.getItem(LISTA_KEY) || '[]'); } catch { return []; }
}
function saveQuickList(list) {
  localStorage.setItem(LISTA_KEY, JSON.stringify(list));
}

const REASON_CONFIG = {
  'Comprato spesso': { bg: 'bg-violet-100', text: 'text-violet-700', Icon: Repeat },
  'In base ai tuoi acquisti': { bg: 'bg-blue-100', text: 'text-blue-700', Icon: Star },
  'Vicino a te': { bg: 'bg-emerald-100', text: 'text-emerald-700', Icon: MapPin },
  'Ottimo sconto': { bg: 'bg-red-100', text: 'text-red-700', Icon: Zap },
  'Da riordinare': { bg: 'bg-amber-100', text: 'text-amber-700', Icon: Repeat },
  'Prodotto correlato': { bg: 'bg-teal-100', text: 'text-teal-700', Icon: Heart },
};

function ReasonBadge({ label }) {
  if (!label) return null;
  const cfg = REASON_CONFIG[label] || { bg: 'bg-stone-100', text: 'text-stone-600', Icon: Tag };
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-semibold ${cfg.bg} ${cfg.text}`} data-testid="reason-badge">
      <cfg.Icon className="w-2.5 h-2.5" />
      {label}
    </span>
  );
}

function ScoreDebug({ breakdown }) {
  if (!breakdown) return null;
  return (
    <div className="mt-1.5 p-1.5 bg-stone-900 text-stone-300 rounded-lg text-[10px] font-mono leading-tight" data-testid="score-debug">
      <span className="text-emerald-400 font-bold">Score: {breakdown.finalScore}</span>
      {breakdown.fallback && <span className="text-amber-400 ml-2">FALLBACK</span>}
      {breakdown.blended && <span className="text-amber-400 ml-2">BLENDED</span>}
      <div>Cat:{breakdown.categoryAffinity ?? '-'} Br:{breakdown.brandAffinity ?? '-'} Pr:{breakdown.productAffinity ?? '-'} Rec:{breakdown.recencyScore ?? '-'}</div>
      <div>Prc:{breakdown.priceFitScore ?? '-'} Dst:{breakdown.distanceScore ?? '-'} Dsc:{breakdown.discountScore ?? '-'}</div>
    </div>
  );
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
  const [location, setLocation] = useState(null);
  const [locationLabel, setLocationLabel] = useState('');
  const [locationReady, setLocationReady] = useState(false);

  const [topPicks, setTopPicks] = useState([]);
  const [rankingMeta, setRankingMeta] = useState(null);
  const [isPersonalized, setIsPersonalized] = useState(false);
  const [debugMode, setDebugMode] = useState(false);
  const [showMap, setShowMap] = useState(false);
  const [allStoresForMap, setAllStoresForMap] = useState({});
  const storeRefs = useRef({});

  useEffect(() => {
    const existing = getQuickList();
    setAddedProducts(new Set(existing.map(p => p.toLowerCase())));
    const savedLoc = localStorage.getItem('shopply_location');
    if (savedLoc) {
      try {
        const loc = JSON.parse(savedLoc);
        setLocation(loc);
        setLocationLabel(loc.label || `${loc.lat.toFixed(2)}, ${loc.lng.toFixed(2)}`);
      } catch {}
    }
    setLocationReady(true);
    const params = new URLSearchParams(window.location.search);
    setDebugMode(params.get('debug') === 'true');
  }, []);

  useEffect(() => {
    if (!locationReady) return;
    loadData(location);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locationReady, location]);

  const loadData = async (loc) => {
    setLoading(true);
    try {
      // Step 1: If location is set, discover real stores first
      if (loc) {
        try {
          const discoverRes = await supermercatiAPI.discover(loc.lat, loc.lng, 15);
          if (discoverRes.data?.supermercati) {
            const mapStores = {};
            discoverRes.data.supermercati.forEach(s => { mapStores[s.id] = s; });
            setAllStoresForMap(mapStores);
          }
        } catch (err) {
          console.log('Discovery skipped:', err.message);
        }
      }

      const token = localStorage.getItem('shopply_token');
      let personalized = false;

      if (token) {
        try {
          const params = { debug: debugMode };
          if (loc) { params.lat = loc.lat; params.lng = loc.lng; params.raggio_km = 15; }
          const res = await raccomandazioniAPI.getPersonalizzate(params);
          const data = res.data;

          if (data.offers && data.offers.length > 0) {
            setRankingMeta(data.meta || {});

            const top = data.offers.slice(0, 10);
            setTopPicks(top);

            const byStore = {};
            const supMap = {};
            data.offers.forEach(o => {
              const sid = o.supermarketId;
              if (!byStore[sid]) byStore[sid] = [];
              byStore[sid].push({
                nome_prodotto: o.productName,
                categoria: o.categoryName,
                brand: o.brand || '',
                formato: o.formato || '',
                supermercato_id: sid,
                prezzo: o.offerPrice,
                prezzo_precedente: o.originalPrice,
                sconto_percentuale: o.discountPercent,
                _score: o.score,
                _reasonLabel: o.reasonLabel,
                _breakdown: o.scoreBreakdown || null,
              });
              if (!supMap[sid]) {
                supMap[sid] = {
                  id: sid,
                  nome: o.supermarketName,
                  distanza_km: o.distanceKm,
                  indirizzo: allStoresForMap[sid]?.indirizzo || '',
                  lat: allStoresForMap[sid]?.lat,
                  lng: allStoresForMap[sid]?.lng,
                  catena: allStoresForMap[sid]?.catena || '',
                };
              }
            });
            setOfferte(byStore);
            setSupermercati(supMap);
            personalized = true;
          }
        } catch (err) {
          console.log('Personalized unavailable:', err.message);
        }
      }

      if (!personalized) {
        let nearbyIds = null;
        const supMap = {};
        if (loc) {
          const nearbyRes = await supermercatiAPI.nearby(loc.lat, loc.lng, 15);
          nearbyRes.data.forEach(s => { supMap[s.id] = s; });
          nearbyIds = new Set(nearbyRes.data.map(s => s.id));
        } else {
          const supRes = await supermercatiAPI.getAll();
          supRes.data.forEach(s => { supMap[s.id] = s; });
        }
        setSupermercati(supMap);

        const offerteRes = await prodottiAPI.getOfferte();
        const all = offerteRes.data;
        if (nearbyIds) {
          const filtered = {};
          Object.entries(all).forEach(([sid, prods]) => {
            if (nearbyIds.has(sid)) filtered[sid] = prods;
          });
          setOfferte(filtered);
        } else {
          setOfferte(all);
        }
        setTopPicks([]);
        setRankingMeta(null);
      }

      setIsPersonalized(personalized);
      const [catRes, aggRes] = await Promise.all([
        prodottiAPI.getCategorie(),
        prezziAPI.ultimoAggiornamento(),
      ]);
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
        await loadData(location);
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

  const getTotaleOfferte = () =>
    Object.values(offerte).reduce((acc, prods) => acc + prods.length, 0);

  const getOfferteFiltered = () => {
    if (filtroCategoria === 'tutte') return offerte;
    const filtered = {};
    Object.entries(offerte).forEach(([sid, prods]) => {
      const f = prods.filter(p => p.categoria === filtroCategoria);
      if (f.length > 0) filtered[sid] = f;
    });
    return filtered;
  };

  const sortedStoreEntries = useMemo(() => {
    const entries = Object.entries(getOfferteFiltered());
    if (isPersonalized) {
      entries.sort(([, a], [, b]) => {
        const maxA = Math.max(...a.map(p => p._score || 0));
        const maxB = Math.max(...b.map(p => p._score || 0));
        return maxB - maxA;
      });
      entries.forEach(([, prods]) => {
        prods.sort((a, b) => (b._score || 0) - (a._score || 0));
      });
    }
    return entries;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offerte, filtroCategoria, isPersonalized]);

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
            {locationLabel && (
              <div className="flex items-center gap-1.5 mt-1 text-sm text-emerald-600" data-testid="offerte-location">
                <MapPin className="w-3.5 h-3.5" />
                <span>{locationLabel}</span>
                <span className="text-stone-400">— raggio 15 km</span>
              </div>
            )}
            {isPersonalized && rankingMeta && (
              <div className="flex items-center gap-1.5 mt-1 text-xs text-violet-600" data-testid="ranking-status">
                <Star className="w-3 h-3" />
                {rankingMeta.isColdStart
                  ? (rankingMeta.isBlended ? 'Ranking misto (personalizzazione parziale)' : 'Ranking generico (nuovo utente)')
                  : 'Personalizzato per te'}
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            {quickListCount > 0 && (
              <a href="/" className="flex items-center gap-1.5 px-3 py-2 bg-emerald-100 text-emerald-700 rounded-xl text-sm font-medium hover:bg-emerald-200 transition-colors" data-testid="go-to-list-btn">
                <ShoppingCart className="w-4 h-4" />
                Lista ({quickListCount})
              </a>
            )}
            <button onClick={handleAggiornaPrezzi} disabled={aggiornando} className="flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white rounded-xl hover:bg-emerald-600 transition-colors disabled:opacity-50" data-testid="refresh-prices-btn">
              {aggiornando ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              Aggiorna
            </button>
            {location && Object.keys(allStoresForMap).length > 0 && (
              <button
                onClick={() => setShowMap(v => !v)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors ${
                  showMap
                    ? 'bg-stone-800 text-white'
                    : 'bg-white text-stone-600 border border-stone-200 hover:bg-stone-50'
                }`}
                data-testid="toggle-map-btn"
              >
                {showMap ? <List className="w-4 h-4" /> : <Map className="w-4 h-4" />}
                {showMap ? 'Lista' : 'Mappa'}
              </button>
            )}
          </div>
        </div>

        {/* Banners */}
        {!location && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-sm text-amber-700 flex items-center gap-2" data-testid="no-location-warning">
            <MapPin className="w-4 h-4 flex-shrink-0" />
            <span>Imposta la tua posizione dalla <a href="/" className="font-semibold underline">Home</a> per vedere solo le offerte dei supermercati vicini a te</span>
          </div>
        )}
        <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-3 text-sm text-blue-700 flex items-center gap-2" data-testid="add-info-banner">
          <Plus className="w-4 h-4 flex-shrink-0" />
          Tocca un prodotto per aggiungerlo alla tua lista della spesa
        </div>

        {ultimoAggiornamento?.timestamp && (
          <div className="text-sm text-stone-400">
            Ultimo aggiornamento: {new Date(ultimoAggiornamento.timestamp).toLocaleString('it-IT')}
            {ultimoAggiornamento.nuove_offerte > 0 && (
              <span className="ml-2 text-orange-500">({ultimoAggiornamento.nuove_offerte} nuove offerte)</span>
            )}
          </div>
        )}

        {/* Interactive Map */}
        {showMap && location && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
            <StoreMap
              stores={allStoresForMap}
              userLat={location.lat}
              userLng={location.lng}
              offerte={offerte}
              onStoreClick={(storeId) => {
                setShowMap(false);
                setTimeout(() => {
                  const el = storeRefs.current[storeId];
                  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 200);
              }}
            />
          </motion.div>
        )}

        {/* Consigliati Per Te section */}
        {topPicks.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="space-y-3" data-testid="recommended-section">
            <h2 className="text-base font-bold text-stone-800 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-violet-500" />
              Consigliati per te
            </h2>
            <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1 snap-x">
              {topPicks.map((pick, i) => {
                const isAdded = addedProducts.has(pick.productName.toLowerCase());
                return (
                  <button
                    key={pick.offerId || i}
                    onClick={() => isAdded ? handleRemoveFromList(pick.productName) : handleAddToList(pick.productName)}
                    className={`flex-shrink-0 w-52 snap-start rounded-2xl p-3 text-left transition-all ${
                      isAdded
                        ? 'bg-emerald-50 border-2 border-emerald-300 ring-1 ring-emerald-200'
                        : 'bg-white border-2 border-stone-100 hover:border-violet-300 hover:shadow-md active:scale-[0.98]'
                    }`}
                    data-testid={`recommended-pick-${i}`}
                  >
                    <div className="flex items-start justify-between mb-1.5">
                      <ReasonBadge label={pick.reasonLabel} />
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                        isAdded ? 'bg-emerald-500 text-white' : 'bg-stone-100 text-stone-400'
                      }`}>
                        {isAdded ? <Check className="w-3 h-3" /> : <Plus className="w-3 h-3" />}
                      </div>
                    </div>
                    <ProductTooltip productName={pick.productName}>
                      <p className="font-medium text-stone-900 text-sm truncate">{pick.productName}</p>
                    </ProductTooltip>
                    <p className="text-xs text-stone-500 truncate">{pick.brand} {pick.formato && `- ${pick.formato}`}</p>
                    <div className="flex items-center justify-between mt-2">
                      <div className="flex items-center gap-1.5">
                        {pick.originalPrice && (
                          <span className="text-xs text-stone-400 line-through">{formatPrice(pick.originalPrice)}</span>
                        )}
                        <span className="font-bold text-orange-600 text-sm">{formatPrice(pick.offerPrice)}</span>
                      </div>
                      {pick.discountPercent && (
                        <span className="text-[10px] bg-red-500 text-white px-1.5 py-0.5 rounded-full font-bold">-{pick.discountPercent}%</span>
                      )}
                    </div>
                    <p className="text-[10px] text-stone-400 mt-1 truncate flex items-center gap-0.5">
                      <Store className="w-2.5 h-2.5" /> {pick.supermarketName}
                      {pick.distanceKm != null && <span> ({pick.distanceKm} km)</span>}
                    </p>
                    {debugMode && pick.scoreBreakdown && <ScoreDebug breakdown={pick.scoreBreakdown} />}
                  </button>
                );
              })}
            </div>
          </motion.div>
        )}

        {/* Category filter */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          <button
            onClick={() => setFiltroCategoria('tutte')}
            className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
              filtroCategoria === 'tutte' ? 'bg-emerald-500 text-white' : 'bg-white text-stone-600 border border-stone-200 hover:bg-stone-50'
            }`}
          >
            Tutte
          </button>
          {categorie.map(cat => (
            <button
              key={cat}
              onClick={() => setFiltroCategoria(cat)}
              className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
                filtroCategoria === cat ? 'bg-emerald-500 text-white' : 'bg-white text-stone-600 border border-stone-200 hover:bg-stone-50'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Store-grouped offers */}
        {sortedStoreEntries.length === 0 ? (
          <div className="bg-white rounded-2xl border border-stone-100 p-12 text-center">
            <Tag className="w-12 h-12 mx-auto text-stone-300 mb-4" />
            <p className="text-stone-500">Nessuna offerta disponibile</p>
            <p className="text-sm text-stone-400 mt-1">Prova ad aggiornare i prezzi</p>
          </div>
        ) : (
          sortedStoreEntries.map(([storeId, prods], idx) => (
            <motion.div
              key={storeId}
              ref={el => { storeRefs.current[storeId] = el; }}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              className="bg-white rounded-2xl border border-stone-100 overflow-hidden"
            >
              <div className="bg-gradient-to-r from-orange-500 to-red-500 px-5 py-4">
                <div className="flex items-center gap-3">
                  <Store className="w-5 h-5 text-white" />
                  <div className="flex-1">
                    <h3 className="font-bold text-white">{supermercati[storeId]?.nome || storeId}</h3>
                    <div className="flex items-center gap-3 flex-wrap">
                      <p className="text-white/80 text-sm">{prods.length} offerte attive</p>
                      {supermercati[storeId]?.distanza_km != null && (
                        <span className="text-white/70 text-sm flex items-center gap-1">
                          <MapPin className="w-3 h-3" /> {supermercati[storeId].distanza_km} km
                        </span>
                      )}
                      {supermercati[storeId]?.indirizzo && (
                        <span className="text-white/60 text-xs">{supermercati[storeId].indirizzo}</span>
                      )}
                    </div>
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
                      className={`flex flex-col p-3 rounded-xl text-left transition-all group ${
                        isAdded
                          ? 'bg-emerald-50 border-2 border-emerald-300 ring-1 ring-emerald-200'
                          : 'bg-orange-50 border-2 border-transparent hover:border-emerald-300 hover:shadow-md active:scale-[0.98]'
                      }`}
                      data-testid={`offerta-product-${prodIdx}`}
                    >
                      <div className="flex items-center justify-between w-full">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5 mb-0.5 flex-wrap">
                            {prod._reasonLabel && <ReasonBadge label={prod._reasonLabel} />}
                          </div>
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
                      </div>
                      {debugMode && prod._breakdown && <ScoreDebug breakdown={prod._breakdown} />}
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

        {/* Toast */}
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
