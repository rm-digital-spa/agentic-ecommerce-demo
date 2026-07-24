import type { Metadata } from "next";
import { SessionWrapper } from "@/components/session-context";

export const metadata: Metadata = {
  title: "Ecommerce POC",
  description: "AI-powered ecommerce assistant",
};

// This layout only wires up the shared providers (auth session + chat runtime).
// The visual chrome is split per-area: the store pages use StoreShell, and the
// assistant uses ChatShell, so chat controls never bleed into store screens.
export default function AuthenticatedLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <SessionWrapper>{children}</SessionWrapper>;
}
