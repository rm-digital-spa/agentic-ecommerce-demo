import { StoreSidebar } from "@/components/store-sidebar";
import { TopBar } from "@/components/top-bar";

export function StoreShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen">
      <StoreSidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-hidden">{children}</main>
      </div>
    </div>
  );
}
