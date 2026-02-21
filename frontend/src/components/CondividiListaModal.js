import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Share2, X, UserPlus, Check, Loader2, Users } from 'lucide-react';
import { listeAPI } from '../lib/api';

export default function CondividiListaModal({ lista, isOpen, onClose, onSuccess }) {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleCondividi = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;
    
    setLoading(true);
    setError('');
    
    try {
      await listeAPI.condividi(lista.id, email);
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        setEmail('');
        onSuccess?.();
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore durante la condivisione');
    } finally {
      setLoading(false);
    }
  };

  const handleRimuovi = async (emailToRemove) => {
    try {
      await listeAPI.rimuoviCondivisione(lista.id, emailToRemove);
      onSuccess?.();
    } catch (err) {
      console.error(err);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-white rounded-2xl p-6 w-full max-w-md"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                <Share2 className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h3 className="font-bold text-stone-900">Condividi Lista</h3>
                <p className="text-sm text-stone-500">{lista.nome}</p>
              </div>
            </div>
            <button onClick={onClose} className="p-2 hover:bg-stone-100 rounded-lg">
              <X className="w-5 h-5 text-stone-500" />
            </button>
          </div>

          <form onSubmit={handleCondividi} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-stone-700 mb-2">
                Email del familiare
              </label>
              <div className="flex gap-2">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="email@esempio.com"
                  className="flex-1 h-12 px-4 rounded-xl border border-stone-200 bg-stone-50 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  data-testid="share-email-input"
                />
                <button
                  type="submit"
                  disabled={loading || !email.trim()}
                  className="h-12 px-4 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors disabled:opacity-50 flex items-center gap-2"
                  data-testid="share-submit-btn"
                >
                  {loading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : success ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    <UserPlus className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>

            {error && (
              <p className="text-sm text-red-500 bg-red-50 px-4 py-2 rounded-lg">{error}</p>
            )}

            {success && (
              <p className="text-sm text-emerald-600 bg-emerald-50 px-4 py-2 rounded-lg flex items-center gap-2">
                <Check className="w-4 h-4" />
                Lista condivisa con successo!
              </p>
            )}
          </form>

          {lista.membri_condivisi?.length > 0 && (
            <div className="mt-6 pt-6 border-t border-stone-100">
              <h4 className="text-sm font-medium text-stone-700 mb-3 flex items-center gap-2">
                <Users className="w-4 h-4" />
                Condivisa con
              </h4>
              <div className="space-y-2">
                {lista.membri_condivisi.map((memberEmail) => (
                  <div
                    key={memberEmail}
                    className="flex items-center justify-between bg-stone-50 px-4 py-2 rounded-lg"
                  >
                    <span className="text-sm text-stone-600">{memberEmail}</span>
                    <button
                      onClick={() => handleRimuovi(memberEmail)}
                      className="text-stone-400 hover:text-red-500"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
