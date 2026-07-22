import { useGetProduct } from '@workspace/api-client-react';
import { useRoute } from 'wouter';
import useEmblaCarousel from 'embla-carousel-react';
import { motion } from 'framer-motion';
import { MessageCircle, Info, ShieldCheck, Eye } from 'lucide-react';
import { useEffect, useState } from 'react';

export function Product() {
  const [, params] = useRoute('/product/:id');
  const id = params?.id ? Number(params.id) : undefined;

  const { data: product, isLoading } = useGetProduct(id!, {
    query: { enabled: !!id }
  });

  const [emblaRef, emblaApi] = useEmblaCarousel({ loop: true });
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    if (!emblaApi) return;
    const onSelect = () => setSelectedIndex(emblaApi.selectedScrollSnap());
    emblaApi.on('select', onSelect);
    return () => { emblaApi.off('select', onSelect); };
  }, [emblaApi]);

  if (isLoading || !product) {
    return (
      <div className="flex flex-col gap-6 animate-pulse px-4 py-6">
        <div className="aspect-[4/5] w-full rounded-2xl bg-white/5" />
        <div className="flex flex-col gap-3">
          <div className="h-8 w-3/4 bg-white/5 rounded" />
          <div className="h-6 w-1/4 bg-white/5 rounded" />
        </div>
      </div>
    );
  }

  const priceDisplay = product.price === 0 ? 'Цена по запросу' : `${product.price.toLocaleString('ru-RU')} ₽`;
  const tgDomain = 'veachelsell'; // Hardcoded per instruction

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col pb-24" // padding bottom for fixed CTA
    >
      {/* Photo Carousel */}
      <div className="relative w-full aspect-[4/5] bg-black">
        {product.photos && product.photos.length > 0 ? (
          <div className="overflow-hidden h-full w-full" ref={emblaRef}>
            <div className="flex h-full w-full">
              {product.photos.map((photoId, idx) => (
                <div key={idx} className="relative flex-[0_0_100%] min-w-0 h-full">
                  <img
                    src={`/api/catalog/photo?file_id=${encodeURIComponent(photoId)}`}
                    alt={`${product.name} - Фото ${idx + 1}`}
                    className="absolute block h-full w-full object-cover"
                  />
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex h-full w-full items-center justify-center text-muted-foreground bg-white/5">
            Нет фото
          </div>
        )}

        {/* Indicators */}
        {product.photos && product.photos.length > 1 && (
          <div className="absolute bottom-4 left-0 right-0 flex justify-center gap-2 z-10">
            {product.photos.map((_, idx) => (
              <div 
                key={idx} 
                className={`h-1.5 rounded-full transition-all ${
                  idx === selectedIndex ? 'w-4 bg-white' : 'w-1.5 bg-white/40'
                }`} 
              />
            ))}
          </div>
        )}

        {/* Stock Badge */}
        {!product.in_stock && (
          <div className="absolute top-4 right-4 bg-background/80 backdrop-blur-md px-3 py-1.5 text-xs font-medium uppercase tracking-widest text-foreground rounded-full border border-white/10 z-10">
            Sold Out
          </div>
        )}
      </div>

      {/* Details */}
      <div className="flex flex-col gap-6 px-4 py-6">
        <div className="flex flex-col gap-2">
          {product.category_name && (
            <span className="text-xs font-medium text-primary uppercase tracking-widest">
              {product.category_name}
            </span>
          )}
          <h1 className="font-display text-2xl font-bold leading-tight">
            {product.name}
          </h1>
          <div className="flex items-center justify-between mt-1">
            <span className="font-display text-2xl font-semibold text-primary">
              {priceDisplay}
            </span>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground bg-white/5 px-2.5 py-1 rounded-full border border-white/5">
              <Eye className="h-3.5 w-3.5" />
              <span>{product.views}</span>
            </div>
          </div>
        </div>

        {/* Trust markers */}
        <div className="flex gap-3 py-4 border-y border-white/10">
          <div className="flex flex-1 items-center gap-2 text-sm text-foreground/80">
            <ShieldCheck className="h-4 w-4 text-primary" />
            <span>100% Оригинал</span>
          </div>
          <div className="w-[1px] bg-white/10" />
          <div className="flex flex-1 items-center gap-2 text-sm text-foreground/80">
            <Info className="h-4 w-4 text-primary" />
            <span>Любые проверки</span>
          </div>
        </div>

        {/* Description */}
        <div className="flex flex-col gap-3">
          <h3 className="font-semibold text-sm uppercase tracking-wider text-muted-foreground">Описание</h3>
          <div className="text-sm leading-relaxed text-foreground/90 whitespace-pre-wrap">
            {product.description || 'Описание отсутствует.'}
          </div>
        </div>
      </div>

      {/* Fixed Bottom CTA */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-background via-background/95 to-transparent pt-12 pb-safe z-50">
        <a 
          href={`tg://resolve?domain=${tgDomain}`}
          className={`flex w-full items-center justify-center gap-2 rounded-xl py-4 font-semibold text-primary-foreground shadow-lg transition-transform active:scale-95 ${
            product.in_stock 
              ? 'bg-primary shadow-primary/20' 
              : 'bg-white/10 text-white/50 cursor-not-allowed'
          }`}
          onClick={(e) => {
            if (!product.in_stock) e.preventDefault();
          }}
        >
          <MessageCircle className="h-5 w-5" />
          {product.in_stock ? 'Написать продавцу' : 'Нет в наличии'}
        </a>
      </div>
    </motion.div>
  );
}
