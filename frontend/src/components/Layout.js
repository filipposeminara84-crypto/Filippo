import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Home, Clock, Settings, LogOut, ShoppingCart, Tag, Gift } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { cn } from '../lib/utils';
import NotificheDropdown from './NotificheDropdown';

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { to: '/', icon: Home, label: 'Home' },
    { to: '/offerte', icon: Tag, label: 'Offerte' },
    { to: '/referral', icon: Gift, label: 'Referral' },
    { to: '/storico', icon: Clock, label: 'Storico' },
    { to: '/impostazioni', icon: Settings, label: 'Impostazioni' },
  ];

  return (
    <div className="min-h-screen bg-stone-50 pb-20 md:pb-0">
      {/* Header Desktop */}
      <header className="hidden md:flex items-center justify-between px-8 py-4 bg-white border-b border-stone-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-emerald-500 rounded-xl flex items-center justify-center">
            <ShoppingCart className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-stone-900">Shopply</span>
        </div>
        
        <nav className="flex items-center gap-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-2 px-4 py-2 rounded-lg transition-colors',
                  isActive
                    ? 'bg-emerald-50 text-emerald-600'
                    : 'text-stone-600 hover:bg-stone-100'
                )
              }
            >
              <Icon className="w-4 h-4" />
              <span className="text-sm font-medium">{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-4">
          <NotificheDropdown />
          <span className="text-sm text-stone-600">Ciao, {user?.nome}</span>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-3 py-2 text-sm text-stone-600 hover:text-red-600 transition-colors"
            data-testid="logout-btn"
          >
            <LogOut className="w-4 h-4" />
            Esci
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 py-6 md:py-8">
        {children}
      </main>

      {/* Mobile Bottom Nav */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white/90 backdrop-blur-lg border-t border-stone-200 z-50 safe-bottom">
        <div className="flex items-center justify-around h-16">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  'flex flex-col items-center gap-1 px-3 py-2 rounded-lg transition-colors',
                  isActive ? 'text-emerald-600' : 'text-stone-500'
                )
              }
            >
              <Icon className="w-5 h-5" />
              <span className="text-xs font-medium">{label}</span>
            </NavLink>
          ))}
          <button
            onClick={handleLogout}
            className="flex flex-col items-center gap-1 px-3 py-2 text-stone-500"
            data-testid="mobile-logout-btn"
          >
            <LogOut className="w-5 h-5" />
            <span className="text-xs font-medium">Esci</span>
          </button>
        </div>
      </nav>
    </div>
  );
}
