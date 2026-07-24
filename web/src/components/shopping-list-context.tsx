"use client";

import { createContext, useCallback, useContext, useMemo, useState } from "react";

export type ShoppingListItem = {
  id: string;
  name: string;
  price: number;
  stock: number;
  quantity: number;
};

type ShoppingListContextValue = {
  items: ShoppingListItem[];
  addItem: (item: Omit<ShoppingListItem, "quantity">) => void;
  removeItem: (id: string) => void;
  setQuantity: (id: string, quantity: number) => void;
  clear: () => void;
  total: number;
};

const ShoppingListContext = createContext<ShoppingListContextValue | null>(
  null,
);

export function ShoppingListProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [items, setItems] = useState<ShoppingListItem[]>([]);

  const addItem = useCallback(
    (item: Omit<ShoppingListItem, "quantity">) => {
      setItems((prev) => {
        const existing = prev.find((i) => i.id === item.id);
        if (existing) {
          return prev.map((i) =>
            i.id === item.id
              ? { ...i, quantity: Math.min(i.quantity + 1, i.stock) }
              : i,
          );
        }
        return [...prev, { ...item, quantity: 1 }];
      });
    },
    [],
  );

  const removeItem = useCallback((id: string) => {
    setItems((prev) => prev.filter((i) => i.id !== id));
  }, []);

  const setQuantity = useCallback((id: string, quantity: number) => {
    setItems((prev) =>
      prev
        .map((i) =>
          i.id === id
            ? { ...i, quantity: Math.max(1, Math.min(quantity, i.stock)) }
            : i,
        )
        .filter((i) => i.quantity > 0),
    );
  }, []);

  const clear = useCallback(() => setItems([]), []);

  const total = useMemo(
    () => items.reduce((sum, i) => sum + i.price * i.quantity, 0),
    [items],
  );

  const value = useMemo(
    () => ({ items, addItem, removeItem, setQuantity, clear, total }),
    [items, addItem, removeItem, setQuantity, clear, total],
  );

  return (
    <ShoppingListContext.Provider value={value}>
      {children}
    </ShoppingListContext.Provider>
  );
}

export function useShoppingList(): ShoppingListContextValue {
  const ctx = useContext(ShoppingListContext);
  if (!ctx) {
    throw new Error("useShoppingList must be used within ShoppingListProvider");
  }
  return ctx;
}
