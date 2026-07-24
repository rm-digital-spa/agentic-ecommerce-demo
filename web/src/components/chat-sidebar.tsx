"use client";

import Link from "next/link";
import { useEffect, useState, useCallback } from "react";
import { PlusCircle, History, RefreshCw, ArrowLeft, MessageSquare, Trash2 } from "lucide-react";
import { useSession } from "@/components/session-context";
import {
  fetchChatHistoryList,
  deleteChatSession,
  type ChatHistoryEntry,
} from "@/lib/chat-runtime";

export function ChatSidebar() {
  const { sessionId, startNewChat, loadSession } = useSession();
  const [conversations, setConversations] = useState<ChatHistoryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const refreshHistory = useCallback(() => {
    setLoading(true);
    fetchChatHistoryList()
      .then(setConversations)
      .catch(() => setConversations([]))
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = useCallback(
    async (convSessionId: string) => {
      setDeletingId(convSessionId);
      try {
        await deleteChatSession(convSessionId);
        setConversations((prev) =>
          prev.filter((c) => c.session_id !== convSessionId),
        );
        // If the active conversation was deleted, reset to a fresh chat.
        if (convSessionId === sessionId) {
          startNewChat();
        }
      } catch {
        // Re-sync with the backend if the delete failed.
        refreshHistory();
      } finally {
        setDeletingId(null);
      }
    },
    [sessionId, startNewChat, refreshHistory],
  );

  useEffect(() => {
    refreshHistory();
  }, [refreshHistory]);

  return (
    <nav className="w-72 shrink-0 bg-zinc-100 dark:bg-zinc-900 border-r border-zinc-200 dark:border-zinc-800 p-4 flex flex-col h-full">
      <div className="mb-6 flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 text-white">
          <MessageSquare className="w-4 h-4" />
        </div>
        <div>
          <h1 className="text-base font-bold text-zinc-900 dark:text-zinc-100 leading-tight">
            AI Assistant
          </h1>
          <p className="text-xs text-zinc-500 leading-tight">Ecommerce POC</p>
        </div>
      </div>

      <button
        onClick={startNewChat}
        className="flex items-center gap-3 w-full px-3 py-2 mb-4 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
      >
        <PlusCircle className="w-5 h-5" />
        New Chat
      </button>

      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-zinc-500 uppercase tracking-wider">
            <History className="w-3.5 h-3.5" />
            History
          </div>
          <button
            onClick={refreshHistory}
            disabled={loading}
            className="p-1 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors disabled:opacity-50"
            title="Refresh history"
          >
            <RefreshCw
              className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`}
            />
          </button>
        </div>
        <ul className="space-y-1 overflow-y-auto flex-1 -mr-1 pr-1">
          {conversations.length === 0 && !loading && (
            <li className="text-xs text-zinc-400 px-2 py-1">
              No conversations yet
            </li>
          )}
          {conversations.map((conv) => {
            const isActive = conv.session_id === sessionId;
            const isDeleting = conv.session_id === deletingId;
            return (
              <li key={conv.session_id} className="group relative">
                <button
                  onClick={() => loadSession(conv.session_id)}
                  className={`w-full text-left pl-3 pr-9 py-2 rounded-lg text-sm truncate transition-colors ${
                    isActive
                      ? "bg-zinc-300 dark:bg-zinc-700 text-zinc-900 dark:text-zinc-100"
                      : "text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-800"
                  }`}
                  title={conv.label}
                >
                  {conv.label}
                </button>
                <button
                  onClick={() => handleDelete(conv.session_id)}
                  disabled={isDeleting}
                  className={`absolute right-1.5 top-1/2 -translate-y-1/2 p-1.5 rounded-md text-zinc-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-zinc-300/60 dark:hover:bg-zinc-700 transition-all disabled:opacity-50 ${
                    isActive
                      ? "opacity-100"
                      : "opacity-0 group-hover:opacity-100 focus:opacity-100"
                  }`}
                  title="Delete conversation"
                  aria-label={`Delete conversation ${conv.label}`}
                >
                  <Trash2
                    className={`w-3.5 h-3.5 ${isDeleting ? "animate-pulse" : ""}`}
                  />
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      <Link
        href="/"
        className="mt-4 flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-800 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to store
      </Link>
    </nav>
  );
}
