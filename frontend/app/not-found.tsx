import Link from "next/link";
import { Compass } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="relative w-full max-w-md overflow-hidden rounded-2xl border border-border/50 bg-card/80 p-8 shadow-xl backdrop-blur-xl text-center">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent pointer-events-none" />
        <div className="relative flex flex-col items-center">
          <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
            <Compass className="h-8 w-8 text-primary" />
          </div>
          <h1 className="mb-2 text-2xl font-bold text-foreground">Page not found</h1>
          <p className="mb-6 text-sm text-muted-foreground">
            The page you&apos;re looking for doesn&apos;t exist.
          </p>
          <div className="flex gap-3">
            <Button asChild variant="default" size="lg">
              <Link href="/dashboard">Go to Dashboard</Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/">Go Home</Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}