"use client";

import { useState, useEffect } from "react";
import { Package, RefreshCw, Plus, Pencil } from "lucide-react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";

interface Product {
  id: string;
  name: string;
  price: number;
  stock: number;
  sku: string | null;
  seller_id: string;
  seller_name?: string;
  created_at: string;
  updated_at: string;
}

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProducts = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch("/products");
      if (!response.ok) throw new Error("Failed to fetch products");
      const data = await response.json();
      setProducts(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  return (
    <div className="h-full p-6 overflow-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            <Package className="w-6 h-6" />
            Products
          </h1>
          <p className="text-zinc-600 dark:text-zinc-400">
            View and manage your product inventory
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchProducts}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-zinc-200 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded-lg hover:bg-zinc-300 dark:hover:bg-zinc-700 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <Link
            href="/products/new"
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create Product
          </Link>
          <Link
            href="/chat"
            className="flex items-center gap-2 px-4 py-2 bg-zinc-200 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded-lg hover:bg-zinc-300 dark:hover:bg-zinc-700 transition-colors"
          >
            Create via Chat
          </Link>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 p-4 rounded-lg mb-6">
          {error}
        </div>
      )}

      {loading && products.length === 0 ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : products.length === 0 ? (
        <div className="text-center py-12">
          <Package className="w-12 h-12 text-zinc-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-100">
            No products yet
          </h3>
          <p className="text-zinc-600 dark:text-zinc-400 mb-4">
            Create your first product
          </p>
          <div className="flex gap-3 justify-center">
            <Link
              href="/products/new"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Create Product
            </Link>
            <Link
              href="/chat"
              className="inline-flex items-center gap-2 px-4 py-2 bg-zinc-200 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded-lg hover:bg-zinc-300 dark:hover:bg-zinc-700 transition-colors"
            >
              Create via Chat
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {products.map((product) => (
            <div
              key={product.id}
              className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 shadow-sm"
            >
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">
                  {product.name}
                </h3>
                <span className="text-sm font-mono text-zinc-500">
                  {product.id}
                </span>
              </div>
              <div className="space-y-1 text-sm">
                <p className="text-zinc-600 dark:text-zinc-400">
                  Price:{" "}
                  <span className="font-medium text-zinc-900 dark:text-zinc-100">
                    ${product.price.toFixed(2)}
                  </span>
                </p>
                <p className="text-zinc-600 dark:text-zinc-400">
                  Stock:{" "}
                  <span
                    className={`font-medium ${
                      product.stock > 0
                        ? "text-green-600 dark:text-green-400"
                        : "text-red-600 dark:text-red-400"
                    }`}
                  >
                    {product.stock} units
                  </span>
                </p>
                {product.sku && (
                  <p className="text-zinc-600 dark:text-zinc-400">
                    SKU: <span className="font-mono">{product.sku}</span>
                  </p>
                )}
                {product.seller_name && (
                  <p className="text-zinc-600 dark:text-zinc-400">
                    Seller:{" "}
                    <span className="font-medium text-zinc-900 dark:text-zinc-100">
                      {product.seller_name}
                    </span>
                  </p>
                )}
              </div>
              <div className="mt-3 pt-3 border-t border-zinc-200 dark:border-zinc-800">
                <Link
                  href={`/products/${product.id}/edit`}
                  className="inline-flex items-center gap-2 px-3 py-1.5 text-sm bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded-lg hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors"
                >
                  <Pencil className="w-3.5 h-3.5" />
                  Edit
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
