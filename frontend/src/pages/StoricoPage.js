import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Clock, Calendar, ShoppingCart, TrendingDown, ChevronRight, CheckCircle } from 'lucide-react';
import { storicoAPI } from '../lib/api';
import { formatPrice, formatDate, formatTime } from '../lib/utils';
import Layout from '../components/Layout';

export default function StoricoPage() {
  const [storico, setStorico] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStorico();
  }, []);

  const loadStorico = async () => {
    try {
      const res = await storicoAPI.getAll();
      setStorico(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const markAsCompleted = async (id) => {
    try {
      await storicoAPI.markEseguita(id);
      await loadStorico();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-2xl border border-stone-100 p-5 animate-pulse">
              <div className="h-5 bg-stone-200 rounded w-1/3 mb-3"></div>
              <div className="h-4 bg-stone-100 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-stone-900">Storico Ricerche</h1>
          <p className="text-stone-500">Le tue ultime 10 ottimizzazioni</p>
        </div>

        {storico.length === 0 ? (
          <div className="bg-white rounded-2xl border border-stone-100 p-12 text-center">
            <Clock className="w-12 h-12 mx-auto text-stone-300 mb-4" />
            <p className="text-stone-500">Nessuna ricerca effettuata</p>
            <p className="text-sm text-stone-400 mt-1">Inizia ottimizzando la tua lista della spesa</p>
          </div>
        ) : (
          <div className="space-y-3">
            {storico.map((item, idx) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className={`bg-white rounded-2xl border ${item.eseguita ? 'border-emerald-200 bg-emerald-50/30' : 'border-stone-100'} p-5`}
                data-testid={`history-item-${idx}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Calendar className="w-4 h-4 text-stone-400" />
                      <span className="text-sm text-stone-500">{formatDate(item.timestamp)}</span>
                      {item.eseguita && (
                        <span className="flex items-center gap-1 text-xs text-emerald-600 bg-emerald-100 px-2 py-0.5 rounded-full">
                          <CheckCircle className="w-3 h-3" />
                          Completata
                        </span>
                      )}
                    </div>
                    
                    <div className="flex flex-wrap gap-1 mb-3">
                      {item.input_lista.slice(0, 5).map((prod, i) => (
                        <span
                          key={i}
                          className="text-xs bg-stone-100 text-stone-600 px-2 py-1 rounded-lg"
                        >
                          {prod}
                        </span>
                      ))}
                      {item.input_lista.length > 5 && (
                        <span className="text-xs text-stone-400 px-2 py-1">
                          +{item.input_lista.length - 5} altri
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-4 text-sm">
                      <div className="flex items-center gap-1">
                        <ShoppingCart className="w-4 h-4 text-stone-400" />
                        <span className="text-stone-600">{item.num_supermercati} negozi</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4 text-stone-400" />
                        <span className="text-stone-600">{formatTime(item.tempo_totale_min)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="text-right">
                    <p className="text-xl font-bold text-stone-900 font-mono">
                      {formatPrice(item.costo_totale)}
                    </p>
                    {item.risparmio > 0 && (
                      <p className="text-sm text-emerald-600 flex items-center justify-end gap-1">
                        <TrendingDown className="w-4 h-4" />
                        -{formatPrice(item.risparmio)}
                      </p>
                    )}
                  </div>
                </div>

                {!item.eseguita && (
                  <button
                    onClick={() => markAsCompleted(item.id)}
                    className="mt-4 w-full py-2 text-sm text-emerald-600 hover:bg-emerald-50 rounded-xl transition-colors flex items-center justify-center gap-2"
                    data-testid={`mark-complete-${idx}`}
                  >
                    <CheckCircle className="w-4 h-4" />
                    Segna come completata
                  </button>
                )}
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
