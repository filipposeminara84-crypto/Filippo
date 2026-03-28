import React, { useState, useRef, useEffect } from 'react';
import { Package, Tag } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// In-memory cache to avoid repeated fetches per session
const imageCache = {};

export default function ProductTooltip({ productName, children }) {
  const [show, setShow] = useState(false);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const wrapRef = useRef(null);
  const timeoutRef = useRef(null);

  const fetchData = async () => {
    if (imageCache[productName]) {
      setData(imageCache[productName]);
      return;
    }
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/prodotti/immagine?q=${encodeURIComponent(productName)}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const json = await res.json();
        imageCache[productName] = json;
        setData(json);
      }
    } catch {
      // silent fail
    } finally {
      setLoading(false);
    }
  };

  const handleEnter = (e) => {
    const rect = wrapRef.current?.getBoundingClientRect();
    if (rect) {
      setPos({
        x: Math.min(rect.left, window.innerWidth - 260),
        y: rect.top - 8,
      });
    }
    timeoutRef.current = setTimeout(() => {
      setShow(true);
      fetchData();
    }, 300);
  };

  const handleLeave = () => {
    clearTimeout(timeoutRef.current);
    setShow(false);
  };

  // Touch support
  const handleTouch = (e) => {
    if (show) {
      setShow(false);
    } else {
      const rect = wrapRef.current?.getBoundingClientRect();
      if (rect) {
        setPos({
          x: Math.min(rect.left, window.innerWidth - 260),
          y: rect.top - 8,
        });
      }
      setShow(true);
      fetchData();
      // Auto-hide after 3s on mobile
      setTimeout(() => setShow(false), 3000);
    }
  };

  useEffect(() => {
    return () => clearTimeout(timeoutRef.current);
  }, []);

  return (
    <span
      ref={wrapRef}
      className="relative cursor-pointer"
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
      onTouchStart={handleTouch}
      data-testid={`product-tooltip-trigger-${productName.toLowerCase().replace(/\s+/g, '-')}`}
    >
      {children}

      {show && (
        <div
          className="fixed z-[9999] animate-in fade-in-0 zoom-in-95 duration-150"
          style={{
            left: `${pos.x}px`,
            top: `${pos.y}px`,
            transform: 'translateY(-100%)',
          }}
          data-testid="product-tooltip"
        >
          <div className="bg-white rounded-xl shadow-xl border border-stone-200 p-3 w-[240px]">
            <div className="flex gap-3">
              {/* Image */}
              <div className="w-16 h-16 rounded-lg bg-stone-100 flex-shrink-0 overflow-hidden flex items-center justify-center">
                {loading ? (
                  <div className="w-5 h-5 border-2 border-stone-300 border-t-emerald-500 rounded-full animate-spin" />
                ) : data?.image_url ? (
                  <img
                    src={data.image_url}
                    alt={productName}
                    className="w-full h-full object-contain"
                    onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
                  />
                ) : null}
                <div className={`items-center justify-center ${data?.image_url ? 'hidden' : 'flex'}`}>
                  <Package className="w-6 h-6 text-stone-300" />
                </div>
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-stone-800 leading-tight truncate">
                  {data?.nome || productName}
                </p>
                {(data?.brand) && (
                  <div className="flex items-center gap-1 mt-1">
                    <Tag className="w-3 h-3 text-stone-400" />
                    <span className="text-xs text-stone-500 truncate">{data.brand}</span>
                  </div>
                )}
                {(data?.formato) && (
                  <span className="inline-block mt-1 text-[10px] bg-stone-100 text-stone-500 px-1.5 py-0.5 rounded-full">
                    {data.formato}
                  </span>
                )}
              </div>
            </div>

            {/* Arrow */}
            <div className="absolute -bottom-1.5 left-6 w-3 h-3 bg-white border-r border-b border-stone-200 transform rotate-45" />
          </div>
        </div>
      )}
    </span>
  );
}
