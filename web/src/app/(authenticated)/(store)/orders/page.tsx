"use client";

import { useState, useEffect } from "react";
import {
  ShoppingCart,
  RefreshCw,
  Plus,
  ChevronDown,
  ChevronUp,
  FileText,
} from "lucide-react";
import { apiFetch } from "@/lib/api-client";
import Link from "next/link";

interface OrderItem {
  product_id: string;
  name: string;
  unit_price: number;
  quantity: number;
  line_total: number;
  seller_id?: string;
}

interface Invoice {
  id: string;
  order_id: string;
  invoice_number: string;
  seller_rut: string;
  total: number;
  status: number;
  status_label: string;
  created_at: string;
}

interface Order {
  id: string;
  customer_id: string;
  items: OrderItem[];
  total: number;
  status: string;
  invoice_id: string | null;
  invoice?: Invoice;
  created_at: string;
  updated_at: string;
}

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedOrder, setExpandedOrder] = useState<string | null>(null);

  const fetchOrders = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch("/orders");
      if (!response.ok) throw new Error("Failed to fetch orders");
      const data = await response.json();
      setOrders(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "created":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400";
      case "submitted":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400";
      case "invoiced":
        return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400";
      case "fulfilled":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400";
      case "completed":
        return "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400";
      default:
        return "bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-400";
    }
  };

  const getInvoiceStatusColor = (status: number) => {
    switch (status) {
      case 0: // Pending
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400";
      case 1: // In Progress
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400";
      case 2: // Completed
        return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400";
      case 3: // Failed
        return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400";
      default:
        return "bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-400";
    }
  };

  return (
    <div className="h-full p-6 overflow-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            <ShoppingCart className="w-6 h-6" />
            Orders
          </h1>
          <p className="text-zinc-600 dark:text-zinc-400">
            View and track customer orders
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchOrders}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-zinc-200 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded-lg hover:bg-zinc-300 dark:hover:bg-zinc-700 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <Link
            href="/chat"
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create via Chat
          </Link>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 p-4 rounded-lg mb-6">
          {error}
        </div>
      )}

      {loading && orders.length === 0 ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : orders.length === 0 ? (
        <div className="text-center py-12">
          <ShoppingCart className="w-12 h-12 text-zinc-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-100">
            No orders yet
          </h3>
          <p className="text-zinc-600 dark:text-zinc-400 mb-4">
            Create your first order using the chat assistant
          </p>
          <Link
            href="/chat"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Go to Chat
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((order) => (
            <div
              key={order.id}
              className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl shadow-sm overflow-hidden"
            >
              <div
                className="p-4 cursor-pointer flex items-center justify-between"
                onClick={() =>
                  setExpandedOrder(expandedOrder === order.id ? null : order.id)
                }
              >
                <div className="flex items-center gap-4">
                  <div>
                    <p className="font-semibold text-zinc-900 dark:text-zinc-100">
                      {order.id}
                    </p>
                    <p className="text-sm text-zinc-500">
                      Customer: {order.customer_id}
                    </p>
                  </div>
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
                      order.status,
                    )}`}
                  >
                    {order.status}
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <p className="font-bold text-zinc-900 dark:text-zinc-100">
                    ${order.total.toFixed(2)}
                  </p>
                  {expandedOrder === order.id ? (
                    <ChevronUp className="w-5 h-5 text-zinc-500" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-zinc-500" />
                  )}
                </div>
              </div>

              {expandedOrder === order.id && (
                <div className="border-t border-zinc-200 dark:border-zinc-800 p-4 bg-zinc-50 dark:bg-zinc-950">
                  <h4 className="font-medium text-zinc-900 dark:text-zinc-100 mb-3">
                    Order Items
                  </h4>
                  <div className="space-y-2">
                    {order.items.map((item, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between text-sm"
                      >
                        <div>
                          <span className="text-zinc-900 dark:text-zinc-100">
                            {item.name}
                          </span>
                          <span className="text-zinc-500 ml-2">
                            x{item.quantity} @ ${item.unit_price.toFixed(2)}
                          </span>
                        </div>
                        <span className="font-medium text-zinc-900 dark:text-zinc-100">
                          ${item.line_total.toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Invoice Section */}
                  {order.invoice && (
                    <div className="mt-4 pt-4 border-t border-zinc-200 dark:border-zinc-800">
                      <h4 className="font-medium text-zinc-900 dark:text-zinc-100 mb-3 flex items-center gap-2">
                        <FileText className="w-4 h-4" />
                        SII Invoice
                      </h4>
                      <div className="bg-white dark:bg-zinc-900 rounded-lg p-3 border border-zinc-200 dark:border-zinc-700">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-zinc-600 dark:text-zinc-400">
                            Invoice Number
                          </span>
                          <span className="font-mono text-sm text-zinc-900 dark:text-zinc-100">
                            {order.invoice.invoice_number}
                          </span>
                        </div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-zinc-600 dark:text-zinc-400">
                            Seller RUT
                          </span>
                          <span className="font-mono text-sm text-zinc-900 dark:text-zinc-100">
                            {order.invoice.seller_rut}
                          </span>
                        </div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-zinc-600 dark:text-zinc-400">
                            Total
                          </span>
                          <span className="font-medium text-zinc-900 dark:text-zinc-100">
                            ${order.invoice.total.toFixed(2)}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-zinc-600 dark:text-zinc-400">
                            Invoice Status
                          </span>
                          <span
                            className={`px-2 py-1 text-xs font-medium rounded-full ${getInvoiceStatusColor(
                              order.invoice.status,
                            )}`}
                          >
                            {order.invoice.status_label}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {order.invoice_id && !order.invoice && (
                    <p className="mt-4 text-sm text-zinc-600 dark:text-zinc-400">
                      Invoice ID:{" "}
                      <span className="font-mono">{order.invoice_id}</span>
                    </p>
                  )}

                  <p className="mt-4 text-xs text-zinc-500">
                    Created: {new Date(order.created_at).toLocaleString()}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
