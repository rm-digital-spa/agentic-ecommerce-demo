"use client";

import { createContext, useCallback, useContext, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { fetchSessionMessages, type UiMessage } from "@/lib/chat-runtime";
import { useAuth } from "./auth-context";
import { ChatProvider } from "./chat-provider";

interface SessionContextValue {
  sessionId: string | null;
  initialMessages: UiMessage[] | undefined;
  startNewChat: () => void;
  loadSession: (sessionId: string) => void;
}

const SessionContext = createContext<SessionContextValue>(null!);

export function SessionProvider({
  children,
  username,
}: {
  children: React.ReactNode;
  username: string;
}) {
  const [sessionId, setSessionId] = useState<string | null>(
    username ? `${username}_${uuidv4()}` : null,
  );

  const [initialMessages, setInitialMessages] = useState<
    UiMessage[] | undefined
  >(undefined);

  const startNewChat = useCallback(() => {
    setInitialMessages(undefined);
    setSessionId(`${username}_${uuidv4()}`);
  }, [username]);

  const loadSession = useCallback((prevSessionId: string) => {
    fetchSessionMessages(prevSessionId).then((msgs) => {
      setInitialMessages(msgs);
      setSessionId(prevSessionId);
    });
  }, []);
  return (
    <SessionContext.Provider
      value={{
        sessionId,
        initialMessages,
        startNewChat,
        loadSession,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  return useContext(SessionContext);
}

export function SessionWrapper({ children }: { children: React.ReactNode }) {
  const { username } = useAuth();

  if (!username) {
    return "not authenticated";
  }
  return (
    <SessionProvider username={username}>
      <ChatProvider>{children}</ChatProvider>
    </SessionProvider>
  );
}
