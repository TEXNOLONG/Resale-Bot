import { Link } from 'wouter';
import { motion } from 'framer-motion';
import type { Product } from '@workspace/api-client-react';

interface ProductCardProps {
  product: Product;
  index?: number;
}

export function ProductCard({ product, index = 0 }: ProductCardProps) {
  const coverPhoto = product.photos?.[0];
  const photoUrl = coverPhoto ? `/api/catalog/photo?file_id=${encodeURIComponent(coverPhoto)}` : '';

  const priceDisplay = product.price === 0 ? 'Цена по запросу' : `${product.price.toLocaleString('ru-RU')} ₽`;

  return (
    <Link href={`/product/${product.id}`}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.05, duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
        className="group relative flex flex-col gap-3 cursor-pointer active:scale-[0.98] transition-transform"
      >
        <div className="relative aspect-[4/5] w-full overflow-hidden rounded-xl bg-white/5 border border-white/5">
          {photoUrl ? (
            <img
              src={photoUrl}
              alt={product.name}
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
              loading="lazy"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-muted-foreground text-sm">
              Нет фото
            </div>
          )}
          {!product.in_stock && (
            <div className="absolute inset-0 bg-background/60 backdrop-blur-[2px] flex items-center justify-center">
              <span className="bg-background/80 px-3 py-1 text-xs font-medium uppercase tracking-widest text-foreground rounded border border-white/10">
                Нет в наличии
              </span>
            </div>
          )}
        </div>
        <div className="flex flex-col gap-1 px-1">
          <div className="flex justify-between items-start gap-2">
            <h3 className="text-sm font-medium leading-tight line-clamp-2 text-foreground/90 group-hover:text-foreground">
              {product.name}
            </h3>
          </div>
          <p className="font-display font-semibold text-primary">{priceDisplay}</p>
        </div>
      </motion.div>
    </Link>
  );
}
