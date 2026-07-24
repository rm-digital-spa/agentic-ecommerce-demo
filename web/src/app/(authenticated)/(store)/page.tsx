import Link from "next/link";
import {
  Package,
  ShoppingCart,
  UserPlus,
  Sparkles,
  ArrowRight,
} from "lucide-react";

const cards = [
  {
    href: "/products",
    label: "Products",
    description: "Browse and manage your catalog and inventory.",
    icon: Package,
  },
  {
    href: "/orders",
    label: "Orders",
    description: "Track customer orders and their SII invoices.",
    icon: ShoppingCart,
  },
  {
    href: "/users/new",
    label: "Add Customer",
    description: "Create a customer account with an API login.",
    icon: UserPlus,
  },
];

export default function HomePage() {
  return (
    <div className="h-full overflow-auto p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
            Welcome back
          </h1>
          <p className="text-zinc-600 dark:text-zinc-400">
            Manage your store directly, or let the AI assistant handle it for
            you.
          </p>
        </div>

        {/* Assistant hero */}
        <Link
          href="/chat"
          className="group block rounded-2xl p-6 mb-8 bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-sm hover:from-blue-500 hover:to-indigo-500 transition-colors"
        >
          <div className="flex items-start gap-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white/15">
              <Sparkles className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold">AI Assistant</h2>
              <p className="text-sm text-blue-100/90 mt-1 max-w-lg">
                Ask in plain language to create products, place orders, manage
                customers, or list inventory — the agent does the work.
              </p>
            </div>
            <ArrowRight className="w-5 h-5 mt-1 opacity-80 transition-transform group-hover:translate-x-1" />
          </div>
        </Link>

        <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">
          Manage manually
        </h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cards.map((card) => {
            const Icon = card.icon;
            return (
              <Link
                key={card.href}
                href={card.href}
                className="group rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 shadow-sm hover:border-blue-500 dark:hover:border-blue-500 transition-colors"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 mb-3 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                  <Icon className="w-5 h-5" />
                </div>
                <p className="font-semibold text-zinc-900 dark:text-zinc-100">
                  {card.label}
                </p>
                <p className="text-sm text-zinc-600 dark:text-zinc-400 mt-1">
                  {card.description}
                </p>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
