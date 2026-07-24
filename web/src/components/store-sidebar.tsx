"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  Users,
  Sparkles,
} from "lucide-react";

const navItems = [
  { href: "/", label: "Home", icon: LayoutDashboard },
  { href: "/products", label: "Products", icon: Package },
  { href: "/orders", label: "Orders", icon: ShoppingCart },
  { href: "/users", label: "Customers", icon: Users },
];

export function StoreSidebar() {
  const pathname = usePathname();

  return (
    <nav className="w-64 shrink-0 bg-zinc-100 dark:bg-zinc-900 border-r border-zinc-200 dark:border-zinc-800 p-4 flex flex-col h-full">
      <div className="mb-8">
        <h1 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
          Ecommerce POC
        </h1>
        <p className="text-sm text-zinc-500">Agent-powered store</p>
      </div>

      <ul className="space-y-1">
        {navItems.map((item) => {
          // Treat the section as active for nested routes (e.g. /products/new),
          // but keep Home exact so it doesn't stay lit everywhere.
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                  isActive
                    ? "bg-blue-600 text-white"
                    : "text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-800"
                }`}
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>

      {/* Assistant launcher — the single entry point into the chat workspace. */}
      <Link
        href="/chat"
        className="mt-auto group flex items-center gap-3 rounded-xl p-3 bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-sm hover:from-blue-500 hover:to-indigo-500 transition-colors"
      >
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/15">
          <Sparkles className="w-5 h-5" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold leading-tight">AI Assistant</p>
          <p className="text-xs text-blue-100/90 leading-tight">
            Chat to manage your store
          </p>
        </div>
      </Link>
    </nav>
  );
}
