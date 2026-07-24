import { ChatSidebar } from "@/components/chat-sidebar";
import { TopBar } from "@/components/top-bar";
import { Sparkles } from "lucide-react";

export function ChatShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen">
      <ChatSidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar>
          <div className="flex items-center gap-2 text-sm font-medium text-zinc-900 dark:text-zinc-100">
            <Sparkles className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            Ecommerce Assistant
          </div>
        </TopBar>
        <main className="flex-1 overflow-hidden">{children}</main>
      </div>
    </div>
  );
}
