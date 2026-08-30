import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authAPI } from '../lib/api';

export default function AuthCallback() {
  const hasProcessed = useRef(false);
  const navigate = useNavigate();
  const { loginWithGoogle } = useAuth();

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const hash = window.location.hash;
    const match = hash.match(/session_id=([^&]+)/);
    if (!match) {
      navigate('/login');
      return;
    }

    const sessionId = match[1];

    (async () => {
      try {
        const res = await authAPI.googleSession(sessionId);
        const { user, session_token } = res.data;
        if (user) {
          // Store session_token as fallback for API calls
          if (session_token) {
            localStorage.setItem('shopply_token', session_token);
          }
          loginWithGoogle(user);
          // Clean URL hash
          window.history.replaceState(null, '', window.location.pathname);
          navigate('/', { state: { user }, replace: true });
        } else {
          navigate('/login');
        }
      } catch (err) {
        console.error('Google auth failed:', err);
        navigate('/login');
      }
    })();
  }, [navigate, loginWithGoogle]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-stone-50">
      <div className="text-center">
        <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-stone-500">Accesso con Google in corso...</p>
      </div>
    </div>
  );
}
