"use client";

import {
  type ChatModelAdapter,
  type ChatModelRunOptions,
} from "@assistant-ui/react";
import { apiFetch } from "@/lib/api-client";

// ==================== Message part types ====================

type JSONValue =
  | string
  | number
  | boolean
  | null
  | readonly JSONValue[]
  | JSONObject;
type JSONObject = { readonly [key: string]: JSONValue };

type ToolCallPart = {
  type: "tool-call";
  toolCallId: string;
  toolName: string;
  args: JSONObject;
  argsText: string;
  result?: unknown;
};

export type Part = { type: "text"; text: string } | ToolCallPart;

export type UiMessage = {
  role: "user" | "assistant";
  content: Part[];
};

// ==================== Backend (Strands) message format ====================

interface BackendToolUse {
  toolUseId: string;
  name: string;
  input?: JSONObject;
}

interface BackendToolResult {
  toolUseId: string;
  status?: string;
  content?: Array<Record<string, unknown>>;
}

interface BackendBlock {
  text?: string;
  toolUse?: BackendToolUse;
  toolResult?: BackendToolResult;
}

interface BackendMessage {
  role: string;
  content?: BackendBlock[];
}

function parseToolResult(toolResult: BackendToolResult): unknown {
  const values = (toolResult.content ?? []).map((b) => {
    if (b.json !== undefined) return b.json;
    if (typeof b.text === "string") {
      try {
        return JSON.parse(b.text);
      } catch {
        return b.text;
      }
    }
    return b;
  });
  return values.length === 1 ? values[0] : values;
}

function toolUseToPart(toolUse: BackendToolUse): ToolCallPart {
  return {
    type: "tool-call",
    toolCallId: toolUse.toolUseId,
    toolName: toolUse.name,
    args: toolUse.input ?? {},
    argsText: JSON.stringify(toolUse.input ?? {}),
  };
}

// ==================== Chat History API ====================

export interface ChatHistoryEntry {
  session_id: string;
  agent_id: string;
  user_id: string;
  label: string;
}

export async function fetchChatHistoryList(): Promise<ChatHistoryEntry[]> {
  const res = await apiFetch("/chat-history");
  if (!res.ok) throw new Error(`Failed to fetch chat history: ${res.status}`);
  return res.json();
}

export async function deleteChatSession(sessionId: string): Promise<void> {
  const res = await apiFetch(`/chat-history/${encodeURIComponent(sessionId)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Failed to delete session: ${res.status}`);
}

export async function fetchSessionMessages(
  sessionId: string,
): Promise<UiMessage[]> {
  const res = await apiFetch(`/chat-history/${encodeURIComponent(sessionId)}`);
  if (!res.ok) throw new Error(`Failed to fetch session: ${res.status}`);
  const data: { session_id: string; messages: BackendMessage[] } =
    await res.json();

  // Convert Strands messages to assistant-ui parts. Tool results arrive in
  // separate user-role messages; attach them to the originating tool-call
  // part (in the previous assistant message) instead of emitting a message.
  const messages: UiMessage[] = [];
  const pendingToolCalls = new Map<string, ToolCallPart>();

  for (const m of data.messages) {
    if (m.role !== "user" && m.role !== "assistant") continue;

    const parts: Part[] = [];
    for (const block of m.content ?? []) {
      if (typeof block.text === "string") {
        parts.push({ type: "text", text: block.text });
      } else if (block.toolUse) {
        const part = toolUseToPart(block.toolUse);
        pendingToolCalls.set(part.toolCallId, part);
        parts.push(part);
      } else if (block.toolResult) {
        const pending = pendingToolCalls.get(block.toolResult.toolUseId);
        if (pending) {
          pending.result = parseToolResult(block.toolResult);
        }
      }
    }

    if (parts.length > 0) {
      messages.push({ role: m.role, content: parts });
    }
  }

  return messages;
}

// ==================== Streaming model adapter ====================

export function createEcommerceModelAdapter(
  username: string,
  sessionId: string | null,
): ChatModelAdapter {
  return {
    async *run({ messages, abortSignal }: ChatModelRunOptions) {
      if (!sessionId) {
        throw new Error("Session ID is required to run the model");
      }
      const lastMessage = messages[messages.length - 1];
      const rawQuery =
        lastMessage?.content
          .filter((c): c is { type: "text"; text: string } => c.type === "text")
          .map((c) => c.text)
          .join("\n") || "";

      console.log("Sending query to API as :", username, sessionId);

      const response = await apiFetch("/invoke", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "User-Email": username,
          "Session-Id": sessionId,
        },
        body: JSON.stringify({ query: rawQuery }),
        signal: abortSignal,
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      if (!response.body) {
        throw new Error("No response body");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      const parts: Part[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          const chunk = line.trim();
          if (!chunk) {
            continue;
          }
          try {
            const chunkObj = JSON.parse(chunk) as BackendMessage;

            for (const block of chunkObj.content ?? []) {
              if (
                typeof block.text === "string" &&
                chunkObj.role === "assistant"
              ) {
                parts.push({ type: "text", text: block.text });
                yield { content: [...parts] };
              } else if (block.toolUse) {
                console.log("Received tool use:", block.toolUse);
                parts.push(toolUseToPart(block.toolUse));
                yield { content: [...parts] };
              } else if (block.toolResult) {
                console.log("Received tool result:", block.toolResult);
                const toolResult = block.toolResult;
                const i = parts.findIndex(
                  (p) =>
                    p.type === "tool-call" &&
                    p.toolCallId === toolResult.toolUseId,
                );
                const existing = parts[i];
                if (existing && existing.type === "tool-call") {
                  parts[i] = {
                    ...existing,
                    result: parseToolResult(toolResult),
                  };
                  yield { content: [...parts] };
                }
              }
            }
          } catch (e) {
            console.error("Failed to parse chunk as JSON:", chunk, e);
          }
        }
      }

      // Final yield with the complete accumulated parts
      if (parts.length === 0) {
        parts.push({ type: "text", text: "No response received from API" });
      }
      yield { content: [...parts] };
    },
  };
}
