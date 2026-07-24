"use client";

import { useState } from "react";
import { useAui } from "@assistant-ui/react";
import {
  ChevronDown,
  ChevronUp,
  Minus,
  Plus,
  ShoppingCart,
  Trash2,
} from "lucide-react";
import { useShoppingList } from "@/components/shopping-list-context";

function formatPrice(price: number): string {
  return `$${price.toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
}

export function ShoppingListPanel() {
  const { items, removeItem, setQuantity, clear, total } = useShoppingList();
  const [expanded, setExpanded] = useState(true);
  const aui = useAui();

  if (items.length === 0) return null;

  const placeOrder = () => {
    const lines = items.map(
      (i) => `- ${i.quantity} x ${i.name} (product_id: ${i.id})`,
    );
    const text = [
      "Please create an order for me with the following items from my shopping list:",
      ...lines,
      "Follow the full order creation workflow, including the SII invoice.",
    ].join("\n");
    aui.thread().append({
      role: "user",
      content: [{ type: "text", text }],
    });
    clear();
  };

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pt-3">
      <div className="rounded-xl border border-blue-200 dark:border-blue-900 bg-blue-50/50 dark:bg-blue-950/30 overflow-hidden">
        <button
          type="button"
          onClick={() => setExpanded((e) => !e)}
          className="flex w-full items-center gap-2 px-4 py-2.5 text-left"
        >
          <ShoppingCart className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            Shopping list
          </span>
          <span className="rounded-full bg-blue-100 dark:bg-blue-900 px-2 py-0.5 text-xs font-medium text-blue-700 dark:text-blue-300">
            {items.reduce((n, i) => n + i.quantity, 0)}
          </span>
          <span className="ml-auto text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            {formatPrice(total)}
          </span>
          {expanded ? (
            <ChevronDown className="h-4 w-4 text-zinc-500" />
          ) : (
            <ChevronUp className="h-4 w-4 text-zinc-500" />
          )}
        </button>

        {expanded && (
          <div className="border-t border-blue-200 dark:border-blue-900">
            <ul className="max-h-48 overflow-y-auto divide-y divide-blue-100 dark:divide-blue-900/50">
              {items.map((item) => (
                <li
                  key={item.id}
                  className="flex items-center gap-3 px-4 py-2"
                >
                  <div className="min-w-0 flex-1">
                    <p
                      className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-100"
                      title={item.name}
                    >
                      {item.name}
                    </p>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">
                      {formatPrice(item.price)} each
                    </p>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => setQuantity(item.id, item.quantity - 1)}
                      disabled={item.quantity <= 1}
                      className="flex h-6 w-6 items-center justify-center rounded-md border border-zinc-300 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300 hover:bg-white dark:hover:bg-zinc-800 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                      aria-label={`Decrease quantity of ${item.name}`}
                    >
                      <Minus className="h-3 w-3" />
                    </button>
                    <span className="w-6 text-center text-sm text-zinc-900 dark:text-zinc-100">
                      {item.quantity}
                    </span>
                    <button
                      type="button"
                      onClick={() => setQuantity(item.id, item.quantity + 1)}
                      disabled={item.quantity >= item.stock}
                      className="flex h-6 w-6 items-center justify-center rounded-md border border-zinc-300 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300 hover:bg-white dark:hover:bg-zinc-800 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                      aria-label={`Increase quantity of ${item.name}`}
                    >
                      <Plus className="h-3 w-3" />
                    </button>
                  </div>
                  <span className="w-16 text-right text-sm font-medium text-zinc-900 dark:text-zinc-100">
                    {formatPrice(item.price * item.quantity)}
                  </span>
                  <button
                    type="button"
                    onClick={() => removeItem(item.id)}
                    className="flex h-6 w-6 items-center justify-center rounded-md text-zinc-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                    aria-label={`Remove ${item.name} from shopping list`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </li>
              ))}
            </ul>
            <div className="flex items-center justify-between gap-2 border-t border-blue-200 dark:border-blue-900 px-4 py-2.5">
              <button
                type="button"
                onClick={clear}
                className="text-xs text-zinc-500 dark:text-zinc-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
              >
                Clear list
              </button>
              <button
                type="button"
                onClick={placeOrder}
                className="rounded-lg bg-blue-600 hover:bg-blue-700 px-4 py-1.5 text-sm font-medium text-white transition-colors"
              >
                Place order · {formatPrice(total)}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
