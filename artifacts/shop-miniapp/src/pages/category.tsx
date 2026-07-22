import { useListProducts, useListCategories } from '@workspace/api-client-react';
import { useRoute } from 'wouter';
import { ProductCard } from '@/components/product-card';

export function Category() {
  const [, params] = useRoute('/category/:id');
  const categoryId = params?.id ? Number(params.id) : undefined;

  const { data: products, isLoading: isLoadingProducts } = useListProducts(
    { category_id: categoryId },
    { query: { enabled: !!categoryId } }
  );

  const { data: categories } = useListCategories();
  const category = categories?.find(c => c.id === categoryId);

  return (
    <div className="flex flex-col gap-6 px-4 py-6">
      <div className="flex flex-col gap-1">
        <h1 className="font-display text-2xl font-bold flex items-center gap-2">
          {category?.emoji} {category?.name || 'Загрузка...'}
        </h1>
        <p className="text-sm text-muted-foreground">
          {products?.length || 0} товаров
        </p>
      </div>

      {isLoadingProducts ? (
        <div className="grid grid-cols-2 gap-x-3 gap-y-6 sm:grid-cols-3">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="flex flex-col gap-2">
              <div className="aspect-[4/5] w-full animate-pulse rounded-xl bg-white/5 border border-white/5" />
              <div className="h-4 w-2/3 animate-pulse bg-white/5 rounded mt-1" />
              <div className="h-5 w-1/3 animate-pulse bg-white/5 rounded" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-x-3 gap-y-6 sm:grid-cols-3">
          {products?.map((product, i) => (
            <ProductCard key={product.id} product={product} index={i} />
          ))}
          {products?.length === 0 && (
            <div className="col-span-full py-12 text-center text-muted-foreground flex flex-col items-center gap-2">
              <span className="text-4xl opacity-50">💨</span>
              <p className="text-sm">В этой категории пока пусто</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
