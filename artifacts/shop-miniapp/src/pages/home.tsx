import { useGetShopSettings, useListCategories, useGetCatalogStats } from '@workspace/api-client-react';
import { Link } from 'wouter';
import { motion } from 'framer-motion';
import { Package, Grid2X2, ChevronRight } from 'lucide-react';

export function Home() {
  const { data: settings, isLoading: isLoadingSettings } = useGetShopSettings();
  const { data: categories, isLoading: isLoadingCategories } = useListCategories();
  const { data: stats, isLoading: isLoadingStats } = useGetCatalogStats();

  return (
    <div className="flex flex-col gap-8 px-4 py-6">
      {/* Hero / Welcome */}
      <section className="flex flex-col gap-2">
        {isLoadingSettings ? (
          <div className="h-24 w-full animate-pulse bg-white/5 rounded-2xl border border-white/5" />
        ) : (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-gradient-to-br from-white/5 to-transparent p-5"
          >
            <h1 className="font-display text-2xl font-bold text-foreground">
              {settings?.shop_name || 'veachelsell'}
            </h1>
            {settings?.welcome_text && (
              <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                {settings.welcome_text}
              </p>
            )}
          </motion.div>
        )}
      </section>

      {/* Stats Bar */}
      <section>
        {isLoadingStats ? (
          <div className="flex gap-4">
            <div className="h-16 flex-1 animate-pulse bg-white/5 rounded-xl border border-white/5" />
            <div className="h-16 flex-1 animate-pulse bg-white/5 rounded-xl border border-white/5" />
          </div>
        ) : (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-2 gap-3"
          >
            <div className="flex flex-col items-center justify-center gap-1 rounded-xl border border-white/5 bg-white/[0.02] py-4">
              <Package className="h-5 w-5 text-muted-foreground" strokeWidth={1.5} />
              <div className="flex items-baseline gap-1.5">
                <span className="font-display text-xl font-bold">{stats?.total_products || 0}</span>
                <span className="text-xs text-muted-foreground uppercase tracking-wider">Товаров</span>
              </div>
            </div>
            <div className="flex flex-col items-center justify-center gap-1 rounded-xl border border-white/5 bg-white/[0.02] py-4">
              <Grid2X2 className="h-5 w-5 text-muted-foreground" strokeWidth={1.5} />
              <div className="flex items-baseline gap-1.5">
                <span className="font-display text-xl font-bold">{stats?.total_categories || 0}</span>
                <span className="text-xs text-muted-foreground uppercase tracking-wider">Категорий</span>
              </div>
            </div>
          </motion.div>
        )}
      </section>

      {/* Categories Grid */}
      <section className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-lg font-semibold tracking-tight">Категории</h2>
        </div>
        
        {isLoadingCategories ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-20 animate-pulse bg-white/5 rounded-xl border border-white/5" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {categories?.map((cat, i) => (
              <Link key={cat.id} href={`/category/${cat.id}`}>
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.05 + 0.2 }}
                  className="group flex items-center justify-between rounded-xl border border-white/5 bg-white/5 p-4 active:scale-95 transition-all cursor-pointer hover:bg-white/10"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl" aria-hidden="true">{cat.emoji}</span>
                    <div className="flex flex-col">
                      <span className="font-medium text-foreground">{cat.name}</span>
                      <span className="text-xs text-muted-foreground">
                        {cat.product_count} {cat.product_count === 1 ? 'вещь' : 'вещей'}
                      </span>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground opacity-50 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
                </motion.div>
              </Link>
            ))}
            {categories?.length === 0 && (
              <div className="col-span-full py-8 text-center text-muted-foreground text-sm">
                Нет доступных категорий
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
