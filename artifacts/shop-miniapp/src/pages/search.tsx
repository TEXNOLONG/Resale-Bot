import { useState } from 'react';
import { useListProducts } from '@workspace/api-client-react';
import { useDebounce } from '@/hooks/use-debounce';
import { ProductCard } from '@/components/product-card';
import { Search as SearchIcon, X, Frown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export function SearchPage() {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 400);

  const { data: products, isLoading } = useListProducts(
    { q: debouncedQuery },
    { query: { enabled: debouncedQuery.length > 0 } }
  );

  return (
    <div className="flex flex-col min-h-full">
      <div className="sticky top-14 z-40 bg-background/95 backdrop-blur px-4 py-3 border-b border-white/5">
        <div className="relative flex items-center">
          <SearchIcon className="absolute left-3.5 h-4 w-4 text-muted-foreground" />
          <input
            autoFocus
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Поиск по названию..."
            className="w-full h-11 bg-white/5 border border-white/10 rounded-xl pl-10 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all"
          />
          <AnimatePresence>
            {query && (
              <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                onClick={() => setQuery('')}
                className="absolute right-3 h-5 w-5 rounded-full bg-white/10 flex items-center justify-center text-muted-foreground hover:text-foreground active:scale-95"
              >
                <X className="h-3 w-3" />
              </motion.button>
            )}
          </AnimatePresence>
        </div>
      </div>

      <div className="flex-1 px-4 py-6">
        {!debouncedQuery ? (
          <div className="flex flex-col items-center justify-center h-48 gap-3 text-muted-foreground">
            <SearchIcon className="h-8 w-8 opacity-20" />
            <p className="text-sm">Введите название товара</p>
          </div>
        ) : isLoading ? (
          <div className="grid grid-cols-2 gap-x-3 gap-y-6 sm:grid-cols-3">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="flex flex-col gap-2">
                <div className="aspect-[4/5] w-full animate-pulse rounded-xl bg-white/5 border border-white/5" />
                <div className="h-4 w-2/3 animate-pulse bg-white/5 rounded mt-1" />
              </div>
            ))}
          </div>
        ) : products && products.length > 0 ? (
          <div className="grid grid-cols-2 gap-x-3 gap-y-6 sm:grid-cols-3">
            {products.map((product, i) => (
              <ProductCard key={product.id} product={product} index={i} />
            ))}
          </div>
        ) : (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center h-64 gap-4"
          >
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-white/5 border border-white/10">
              <Frown className="h-8 w-8 text-muted-foreground" />
            </div>
            <div className="flex flex-col items-center text-center gap-1">
              <h3 className="font-medium text-foreground">Ничего не найдено</h3>
              <p className="text-sm text-muted-foreground">
                Попробуйте изменить запрос
              </p>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
