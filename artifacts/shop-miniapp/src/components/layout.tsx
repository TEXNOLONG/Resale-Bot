import { useEffect } from 'react';
import { Link, useLocation } from 'wouter';
import { Search, ChevronLeft } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const [location, setLocation] = useLocation();
  const isHome = location === '/';

  useEffect(() => {
    // Initialize Telegram WebApp
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
    }
  }, []);

  return (
    <div className="min-h-[100dvh] flex flex-col bg-background text-foreground selection:bg-primary selection:text-primary-foreground dark">
      <header className="sticky top-0 z-50 w-full border-b border-white/5 bg-background/80 backdrop-blur-md">
        <div className="flex h-14 items-center justify-between px-4">
          <div className="flex items-center gap-3">
            <AnimatePresence mode="popLayout">
              {!isHome && (
                <motion.button
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  onClick={() => window.history.back()}
                  className="flex h-8 w-8 items-center justify-center rounded-full bg-white/5 hover:bg-white/10 active:scale-95 transition-all"
                >
                  <ChevronLeft className="h-5 w-5" />
                </motion.button>
              )}
            </AnimatePresence>
            <Link href="/">
              <span className="font-display text-xl font-bold tracking-tighter cursor-pointer">
                veachelsell
              </span>
            </Link>
          </div>
          <Link href="/search" className="flex h-8 w-8 items-center justify-center rounded-full bg-white/5 hover:bg-white/10 active:scale-95 transition-all">
            <Search className="h-4 w-4" />
          </Link>
        </div>
      </header>

      <main className="flex-1 pb-safe">
        {children}
      </main>
    </div>
  );
}
