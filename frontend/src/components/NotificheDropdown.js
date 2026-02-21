import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, X, Check, Gift, Users, Info, Trash2 } from 'lucide-react';
import { notificheAPI } from '../lib/api';
import { formatDate } from '../lib/utils';

export default function NotificheDropdown() {
  const [isOpen, setIsOpen] = useState(false);
  const [notifiche, setNotifiche] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    loadNotifiche();
    const interval = setInterval(loadUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadNotifiche = async () => {
    try {
      const res = await notificheAPI.getAll();
      setNotifiche(res.data);
      setUnreadCount(res.data.filter(n => !n.letta).length);
    } catch (err) {
      console.error(err);
    }
  };

  const loadUnreadCount = async () => {
    try {
      const res = await notificheAPI.getNonLette();
      setUnreadCount(res.data.count);
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkRead = async (id) => {
    try {
      await notificheAPI.segnaLetta(id);
      setNotifiche(notifiche.map(n => n.id === id ? { ...n, letta: true } : n));
      setUnreadCount(Math.max(0, unreadCount - 1));
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificheAPI.leggiTutte();
      setNotifiche(notifiche.map(n => ({ ...n, letta: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id) => {
    try {
      await notificheAPI.elimina(id);
      setNotifiche(notifiche.filter(n => n.id !== id));
    } catch (err) {
      console.error(err);
    }
  };

  const getIcon = (tipo) => {
    switch (tipo) {
      case 'offerta': return <Gift className="w-5 h-5 text-orange-500" />;
      case 'condivisione': return <Users className="w-5 h-5 text-blue-500" />;
      default: return <Info className="w-5 h-5 text-emerald-500" />;
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg hover:bg-stone-100 transition-colors"
        data-testid="notifications-btn"
      >
        <Bell className="w-5 h-5 text-stone-600" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              className="absolute right-0 top-full mt-2 w-80 md:w-96 bg-white rounded-2xl shadow-xl border border-stone-200 z-50 overflow-hidden"
            >
              <div className="flex items-center justify-between p-4 border-b border-stone-100">
                <h3 className="font-semibold text-stone-900">Notifiche</h3>
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllRead}
                    className="text-sm text-emerald-600 hover:text-emerald-700"
                  >
                    Segna tutte come lette
                  </button>
                )}
              </div>

              <div className="max-h-96 overflow-y-auto">
                {notifiche.length === 0 ? (
                  <div className="p-8 text-center text-stone-400">
                    <Bell className="w-10 h-10 mx-auto mb-2 opacity-30" />
                    <p>Nessuna notifica</p>
                  </div>
                ) : (
                  notifiche.slice(0, 10).map((notifica) => (
                    <div
                      key={notifica.id}
                      className={`p-4 border-b border-stone-50 hover:bg-stone-50 transition-colors ${
                        !notifica.letta ? 'bg-emerald-50/50' : ''
                      }`}
                    >
                      <div className="flex gap-3">
                        <div className="flex-shrink-0 mt-1">
                          {getIcon(notifica.tipo)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-stone-900 text-sm">{notifica.titolo}</p>
                          <p className="text-sm text-stone-500 mt-1">{notifica.messaggio}</p>
                          <p className="text-xs text-stone-400 mt-2">{formatDate(notifica.data)}</p>
                        </div>
                        <div className="flex-shrink-0 flex flex-col gap-1">
                          {!notifica.letta && (
                            <button
                              onClick={() => handleMarkRead(notifica.id)}
                              className="p-1 text-stone-400 hover:text-emerald-500"
                              title="Segna come letta"
                            >
                              <Check className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={() => handleDelete(notifica.id)}
                            className="p-1 text-stone-400 hover:text-red-500"
                            title="Elimina"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
