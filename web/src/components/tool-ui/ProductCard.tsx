"use client";

import { useState } from "react";
import { makeAssistantToolUI } from "@assistant-ui/react";
import { Check, ChevronLeft, ChevronRight, Package, Plus } from "lucide-react";
import { useShoppingList } from "@/components/shopping-list-context";

type Product = {
  id: string;
  name: string;
  price: number;
  stock: number;
  sku?: string | null;
  seller_id?: string | null;
};

const PAGE_SIZE = 6;

function formatPrice(price: number): string {
  return `$${price.toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
}

function StockBadge({ stock }: { stock: number }) {
  if (stock <= 0) {
    return (
      <span className="inline-flex items-center rounded-full bg-red-50 dark:bg-red-950 px-2 py-0.5 text-xs font-medium text-red-700 dark:text-red-400">
        Out of stock
      </span>
    );
  }
  if (stock <= 10) {
    return (
      <span className="inline-flex items-center rounded-full bg-amber-50 dark:bg-amber-950 px-2 py-0.5 text-xs font-medium text-amber-700 dark:text-amber-400">
        {stock} left
      </span>
    );
  }
  return (
    <span className="inline-flex items-center rounded-full bg-emerald-50 dark:bg-emerald-950 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-400">
      {stock} in stock
    </span>
  );
}

function AddToListButton({ product }: { product: Product }) {
  const { items, addItem } = useShoppingList();
  const inList = items.find((i) => i.id === product.id);
  const atStockLimit = inList !== undefined && inList.quantity >= product.stock;
  const disabled = product.stock <= 0 || atStockLimit;

  return (
    <button
      type="button"
      onClick={() =>
        addItem({
          id: product.id,
          name: product.name,
          price: product.price,
          stock: product.stock,
        })
      }
      disabled={disabled}
      className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
        inList
          ? "bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-900"
          : "bg-blue-600 hover:bg-blue-700 text-white"
      }`}
      aria-label={`Add ${product.name} to shopping list`}
    >
      {inList ? (
        <>
          <Check className="h-3 w-3" />
          {inList.quantity} in list
        </>
      ) : (
        <>
          <Plus className="h-3 w-3" />
          Add
        </>
      )}
    </button>
  );
}

function ProductGrid({ products }: { products: Product[] }) {
  const [page, setPage] = useState(0);
  const pageCount = Math.ceil(products.length / PAGE_SIZE);
  const start = page * PAGE_SIZE;
  const visible = products.slice(start, start + PAGE_SIZE);

  return (
    <div className="my-2 w-full rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 overflow-hidden">
      <div className="flex items-center gap-2 border-b border-zinc-200 dark:border-zinc-800 px-4 py-2.5">
        <Package className="h-4 w-4 text-blue-600 dark:text-blue-400" />
        <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
          Products
        </span>
        <span className="rounded-full bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 text-xs font-medium text-zinc-600 dark:text-zinc-400">
          {products.length}
        </span>
      </div>

      {products.length === 0 ? (
        <p className="px-4 py-6 text-center text-sm text-zinc-500 dark:text-zinc-400">
          No products found.
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-2 p-3 sm:grid-cols-2">
          {visible.map((p) => (
            <div
              key={p.id}
              className="flex flex-col gap-1.5 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 p-3 transition-colors hover:border-blue-400 dark:hover:border-blue-600"
            >
              <div className="flex items-start justify-between gap-2">
                <span
                  className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-100"
                  title={p.name}
                >
                  {p.name}
                </span>
                <span className="shrink-0 text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                  {formatPrice(p.price)}
                </span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <StockBadge stock={p.stock} />
                {p.sku && (
                  <span className="truncate text-xs text-zinc-400 dark:text-zinc-500">
                    SKU {p.sku}
                  </span>
                )}
                <AddToListButton product={p} />
              </div>
            </div>
          ))}
        </div>
      )}

      {pageCount > 1 && (
        <div className="flex items-center justify-between border-t border-zinc-200 dark:border-zinc-800 px-4 py-2">
          <span className="text-xs text-zinc-500 dark:text-zinc-400">
            {start + 1}–{Math.min(start + PAGE_SIZE, products.length)} of{" "}
            {products.length}
          </span>
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setPage((p) => p - 1)}
              disabled={page === 0}
              className="flex h-7 w-7 items-center justify-center rounded-md border border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              aria-label="Previous page"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="px-1.5 text-xs text-zinc-500 dark:text-zinc-400">
              {page + 1}/{pageCount}
            </span>
            <button
              type="button"
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= pageCount - 1}
              className="flex h-7 w-7 items-center justify-center rounded-md border border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              aria-label="Next page"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="my-2 w-full animate-pulse rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-3">
      <div className="mb-3 h-4 w-32 rounded bg-zinc-200 dark:bg-zinc-800" />
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="h-16 rounded-lg bg-zinc-100 dark:bg-zinc-800"
          />
        ))}
      </div>
    </div>
  );
}

export const ProductCardToolUI = makeAssistantToolUI<object, Product[]>({
  toolName: "show_products",
  render: ({ status, result, ...rest }) => {
    console.log("ProductCardToolUI render", { status, result, rest });
    if (status.type === "running") {
      return <LoadingSkeleton />;
    }
    if (!Array.isArray(result)) {
      return (
        <pre className="my-2 max-h-48 overflow-auto rounded-lg bg-zinc-100 dark:bg-zinc-800 p-3 text-xs text-zinc-700 dark:text-zinc-300">
          {JSON.stringify(result, null, 2)}
        </pre>
      );
    }
    return <ProductGrid products={result} />;
  },
});
