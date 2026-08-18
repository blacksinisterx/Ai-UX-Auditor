import Link from "next/link";
import { Sparkles } from "lucide-react";

export function SiteHeader() {
  return (
    <header className="border-b border-border">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-(--space-lg) py-(--space-sm)">
        <Link href="/" className="flex items-center gap-(--space-xs) font-semibold">
          <span className="flex size-7 items-center justify-center rounded-(--radius-md) bg-primary text-primary-foreground">
            <Sparkles className="size-4" />
          </span>
          Aura
        </Link>
        <Link
          href="/audit/new"
          className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          New audit
        </Link>
      </div>
    </header>
  );
}
