"use client";

import { useMemo } from "react";
import { AssistantRuntimeProvider, useLocalRuntime } from "@assistant-ui/react";
import { createEcommerceModelAdapter } from "@/lib/chat-runtime";
import { useSession } from "@/components/session-context";
import { useAuth } from "./auth-context";
import { ProductCardToolUI } from "./tool-ui/ProductCard";
import { ShoppingListProvider } from "./shopping-list-context";

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const { sessionId } = useSession();
  // Remount the runtime owner on every session switch. `useLocalRuntime` only
  // reads `initialMessages` once (in a useState initializer), so a fresh mount
  // is the only way to load a previously stored session's messages and rebind
  // the composer store. Keying a child of this component is not enough.
  // The shopping list lives outside the keyed runtime so it survives session
  // switches.
  return (
    <ShoppingListProvider>
      <ChatRuntime key={sessionId ?? "new"}>{children}</ChatRuntime>
    </ShoppingListProvider>
  );
}

function ChatRuntime({ children }: { children: React.ReactNode }) {
  const { username } = useAuth();
  const { sessionId, initialMessages } = useSession();
  const adapter = useMemo(
    () => createEcommerceModelAdapter(username!, sessionId),
    [username, sessionId],
  );
  const runtime = useLocalRuntime(adapter, { initialMessages });
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ProductCardToolUI />
      {children}
    </AssistantRuntimeProvider>
  );
}
