"use client";

import {
  ThreadPrimitive,
  ComposerPrimitive,
  MessagePrimitive,
} from "@assistant-ui/react";
import { SendIcon, Sparkles, ArrowDown } from "lucide-react";
import { ShoppingListPanel } from "@/components/shopping-list-panel";

export function ChatInterface() {
  return (
    <ThreadPrimitive.Root className="flex flex-col h-full bg-white dark:bg-zinc-950">
      <ThreadPrimitive.Viewport className="flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-3xl px-4 py-6">
          <ThreadPrimitive.Empty>
            <div className="text-center space-y-4 py-16">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white">
                <Sparkles className="w-7 h-7" />
              </div>
              <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
                Ecommerce Assistant
              </h2>
              <p className="text-zinc-600 dark:text-zinc-400 max-w-md mx-auto">
                Ask me to create products, manage customers, place orders, or
                list your inventory. I can help you with your ecommerce
                operations.
              </p>
              <div className="flex flex-wrap justify-center gap-2 pt-4">
                <SuggestionChip text="List all products" />
                <SuggestionChip text="Create a new product" />
                <SuggestionChip text="Show all orders" />
                <SuggestionChip text="Create a customer" />
              </div>
            </div>
          </ThreadPrimitive.Empty>
          <ThreadPrimitive.Messages
            components={{
              UserMessage: UserMessage,
              AssistantMessage: AssistantMessage,
            }}
          />
        </div>
      </ThreadPrimitive.Viewport>

      <div className="relative border-t border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
        <ThreadPrimitive.ScrollToBottom className="absolute -top-12 left-1/2 -translate-x-1/2 flex h-9 w-9 items-center justify-center rounded-full border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-600 dark:text-zinc-300 shadow-sm hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors disabled:invisible">
          <ArrowDown className="w-4 h-4" />
        </ThreadPrimitive.ScrollToBottom>
        <ShoppingListPanel />
        <div className="mx-auto w-full max-w-3xl px-4 py-4">
          <ComposerPrimitive.Root className="flex items-end gap-2 rounded-2xl border border-zinc-200 dark:border-zinc-700 bg-zinc-100 dark:bg-zinc-900 p-2 focus-within:border-blue-500 dark:focus-within:border-blue-500 transition-colors">
            <ComposerPrimitive.Input
              placeholder="Message the assistant…"
              className="flex-1 bg-transparent border-0 outline-none resize-none text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-500 px-2 py-2 min-h-[40px] max-h-[200px]"
            />
            <ComposerPrimitive.Send className="p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
              <SendIcon className="w-5 h-5" />
            </ComposerPrimitive.Send>
          </ComposerPrimitive.Root>
          <p className="mt-2 text-center text-xs text-zinc-400 dark:text-zinc-600">
            The assistant can make mistakes. Verify important actions.
          </p>
        </div>
      </div>
    </ThreadPrimitive.Root>
  );
}

function UserMessage() {
  return (
    <MessagePrimitive.Root className="flex justify-end mb-5">
      <div className="bg-blue-600 text-white rounded-2xl rounded-br-md px-4 py-2.5 max-w-[80%] whitespace-pre-wrap break-words">
        <MessagePrimitive.Content />
      </div>
    </MessagePrimitive.Root>
  );
}

function AssistantMessage() {
  return (
    <MessagePrimitive.Root className="flex justify-start gap-3 mb-5">
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 text-white">
        <Sparkles className="w-4 h-4" />
      </div>
      <div className="text-zinc-900 dark:text-zinc-100 leading-relaxed max-w-[80%] whitespace-pre-wrap break-words pt-1">
        <MessagePrimitive.Content />
      </div>
    </MessagePrimitive.Root>
  );
}

function SuggestionChip({ text }: { text: string }) {
  return (
    <ThreadPrimitive.Suggestion
      prompt={text}
      send
      clearComposer
      className="px-3 py-1.5 text-sm bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded-full border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors cursor-pointer"
    >
      {text}
    </ThreadPrimitive.Suggestion>
  );
}
