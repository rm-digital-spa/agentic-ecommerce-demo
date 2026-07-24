import { UserBadge } from "@/components/user-badge";

export function TopBar({ children }: { children?: React.ReactNode }) {
  return (
    <header className="flex items-center justify-between gap-4 h-14 shrink-0 px-4 border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
      <div className="min-w-0 flex-1">{children}</div>
      <UserBadge />
    </header>
  );
}
