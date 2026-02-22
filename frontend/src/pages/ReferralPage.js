import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Gift, Users, Copy, Check, Share2, Trophy, 
  ArrowRight, Loader2, Send, Coins, Star
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { referralAPI } from '../lib/api';
import { formatPrice } from '../lib/utils';
import Layout from '../components/Layout';

export default function ReferralPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [inviti, setInviti] = useState([]);
  const [classifica, setClassifica] = useState([]);
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState('');
  const [sending, setSending] = useState(false);
  const [copied, setCopied] = useState(false);
  const [riscattando, setRiscattando] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsRes, invitiRes, classificaRes] = await Promise.all([
        referralAPI.getStats(),
        referralAPI.getInviti(),
        referralAPI.getClassifica()
      ]);
      setStats(statsRes.data);
      setInviti(invitiRes.data);
      setClassifica(classificaRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(stats?.referral_code || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleShare = async () => {
    const shareData = {
      title: 'Shopply - Risparmia sulla spesa!',
      text: `Usa il mio codice ${stats?.referral_code} per registrarti su Shopply e ricevi ${stats?.punti_per_registrazione} punti bonus!`,
      url: `${window.location.origin}/register?ref=${stats?.referral_code}`
    };
    
    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (err) {
        console.log('Share cancelled');
      }
    } else {
      handleCopyCode();
    }
  };

  const handleInvita = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;
    
    setSending(true);
    try {
      await referralAPI.invita(email);
      setEmail('');
      await loadData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Errore nell\'invio');
    } finally {
      setSending(false);
    }
  };

  const handleRiscatta = async () => {
    if (!stats?.punti_totali || stats.punti_totali < 10) return;
    
    setRiscattando(true);
    try {
      const puntiDaRiscattare = Math.floor(stats.punti_totali / 10) * 10; // Round to nearest 10
      await referralAPI.riscatta(puntiDaRiscattare);
      await loadData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Errore nel riscatto');
    } finally {
      setRiscattando(false);
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
        {/* Header */}
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl mx-auto flex items-center justify-center mb-4 shadow-lg shadow-purple-500/30">
            <Gift className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-stone-900">Programma Referral</h1>
          <p className="text-stone-500 mt-1">Invita amici e familiari, guadagna punti!</p>
        </div>

        {/* Referral Code Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-purple-600 to-pink-600 rounded-2xl p-6 text-white"
        >
          <p className="text-purple-200 text-sm mb-2">Il tuo codice referral</p>
          <div className="flex items-center justify-between">
            <span className="text-3xl font-bold font-mono tracking-wider" data-testid="referral-code">
              {stats?.referral_code}
            </span>
            <div className="flex gap-2">
              <button
                onClick={handleCopyCode}
                className="p-3 bg-white/20 rounded-xl hover:bg-white/30 transition-colors"
                data-testid="copy-code-btn"
              >
                {copied ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
              </button>
              <button
                onClick={handleShare}
                className="p-3 bg-white/20 rounded-xl hover:bg-white/30 transition-colors"
                data-testid="share-btn"
              >
                <Share2 className="w-5 h-5" />
              </button>
            </div>
          </div>
          <p className="text-purple-200 text-sm mt-4">
            Condividi il codice e guadagna <strong>{stats?.punti_per_invito} punti</strong> per ogni amico che si registra!
          </p>
        </motion.div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-2xl border border-stone-100 p-4"
          >
            <div className="flex items-center gap-2 text-stone-500 mb-1">
              <Coins className="w-4 h-4" />
              <span className="text-sm">Punti</span>
            </div>
            <p className="text-2xl font-bold text-purple-600" data-testid="total-points">
              {stats?.punti_totali || 0}
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-emerald-50 rounded-2xl border border-emerald-100 p-4"
          >
            <div className="flex items-center gap-2 text-emerald-600 mb-1">
              <Gift className="w-4 h-4" />
              <span className="text-sm">Bonus</span>
            </div>
            <p className="text-2xl font-bold text-emerald-600" data-testid="bonus-value">
              {formatPrice(stats?.bonus_disponibile || 0)}
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-2xl border border-stone-100 p-4"
          >
            <div className="flex items-center gap-2 text-stone-500 mb-1">
              <Users className="w-4 h-4" />
              <span className="text-sm">Inviti</span>
            </div>
            <p className="text-2xl font-bold text-stone-900">
              {stats?.inviti_completati || 0}
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white rounded-2xl border border-stone-100 p-4"
          >
            <div className="flex items-center gap-2 text-stone-500 mb-1">
              <Send className="w-4 h-4" />
              <span className="text-sm">Pendenti</span>
            </div>
            <p className="text-2xl font-bold text-orange-500">
              {stats?.inviti_pendenti || 0}
            </p>
          </motion.div>
        </div>

        {/* Redeem Button */}
        {stats?.punti_totali >= 10 && (
          <motion.button
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            onClick={handleRiscatta}
            disabled={riscattando}
            className="w-full h-14 bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-bold rounded-2xl shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/40 transition-all active:scale-[0.98] flex items-center justify-center gap-3 disabled:opacity-50"
            data-testid="redeem-btn"
          >
            {riscattando ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <Gift className="w-5 h-5" />
                Riscatta {formatPrice(stats?.bonus_disponibile || 0)} di Sconto
              </>
            )}
          </motion.button>
        )}

        {/* How it works */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-white rounded-2xl border border-stone-100 p-5"
        >
          <h3 className="font-semibold text-stone-900 mb-4">Come funziona</h3>
          <div className="space-y-4">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <span className="text-purple-600 font-bold">1</span>
              </div>
              <div>
                <p className="font-medium text-stone-900">Condividi il codice</p>
                <p className="text-sm text-stone-500">Invia il tuo codice a amici e familiari</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 bg-pink-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <span className="text-pink-600 font-bold">2</span>
              </div>
              <div>
                <p className="font-medium text-stone-900">Si registrano</p>
                <p className="text-sm text-stone-500">Inseriscono il codice durante la registrazione</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <span className="text-emerald-600 font-bold">3</span>
              </div>
              <div>
                <p className="font-medium text-stone-900">Guadagnate entrambi!</p>
                <p className="text-sm text-stone-500">
                  Tu ricevi <strong>{stats?.punti_per_invito} punti</strong>, loro <strong>{stats?.punti_per_registrazione} punti</strong>
                </p>
              </div>
            </div>
          </div>
          <div className="mt-4 p-3 bg-stone-50 rounded-xl">
            <p className="text-sm text-stone-600 text-center">
              <strong>{stats?.punti_per_euro || 10} punti</strong> = <strong>1€</strong> di sconto sulla spesa
            </p>
          </div>
        </motion.div>

        {/* Invite Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="bg-white rounded-2xl border border-stone-100 p-5"
        >
          <h3 className="font-semibold text-stone-900 mb-4 flex items-center gap-2">
            <Send className="w-5 h-5 text-purple-500" />
            Invita via Email
          </h3>
          <form onSubmit={handleInvita} className="flex gap-2">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="email@esempio.com"
              className="flex-1 h-12 px-4 rounded-xl border border-stone-200 bg-stone-50 focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500"
              data-testid="invite-email-input"
            />
            <button
              type="submit"
              disabled={sending || !email.trim()}
              className="h-12 px-6 bg-purple-500 text-white font-medium rounded-xl hover:bg-purple-600 transition-colors disabled:opacity-50 flex items-center gap-2"
              data-testid="send-invite-btn"
            >
              {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              Invia
            </button>
          </form>
        </motion.div>

        {/* Leaderboard */}
        {classifica.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="bg-white rounded-2xl border border-stone-100 p-5"
          >
            <h3 className="font-semibold text-stone-900 mb-4 flex items-center gap-2">
              <Trophy className="w-5 h-5 text-yellow-500" />
              Top Referrer
            </h3>
            <div className="space-y-2">
              {classifica.map((item, idx) => (
                <div
                  key={idx}
                  className={`flex items-center justify-between p-3 rounded-xl ${
                    idx === 0 ? 'bg-yellow-50' : idx === 1 ? 'bg-stone-100' : idx === 2 ? 'bg-orange-50' : 'bg-stone-50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                      idx === 0 ? 'bg-yellow-500 text-white' : 
                      idx === 1 ? 'bg-stone-400 text-white' : 
                      idx === 2 ? 'bg-orange-400 text-white' : 
                      'bg-stone-200 text-stone-600'
                    }`}>
                      {item.posizione}
                    </span>
                    <span className="font-medium text-stone-700">{item.nome}</span>
                  </div>
                  <div className="flex items-center gap-1 text-purple-600 font-bold">
                    <Star className="w-4 h-4" />
                    {item.punti}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Invite History */}
        {inviti.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
            className="bg-white rounded-2xl border border-stone-100 p-5"
          >
            <h3 className="font-semibold text-stone-900 mb-4">I tuoi inviti</h3>
            <div className="space-y-2">
              {inviti.slice(0, 5).map((inv) => (
                <div
                  key={inv.id}
                  className="flex items-center justify-between p-3 bg-stone-50 rounded-xl"
                >
                  <div>
                    <p className="font-medium text-stone-700">{inv.invitato_email}</p>
                    <p className="text-sm text-stone-500">
                      {new Date(inv.data_invito).toLocaleDateString('it-IT')}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    inv.stato === 'completed' 
                      ? 'bg-emerald-100 text-emerald-700' 
                      : 'bg-orange-100 text-orange-700'
                  }`}>
                    {inv.stato === 'completed' ? `+${inv.punti_assegnati} punti` : 'In attesa'}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </Layout>
  );
}
