import { Sprout } from "lucide-react";

export default function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="relative flex flex-col items-center gap-4 rounded-2xl border border-border/50 bg-card/80 p-8 shadow-xl backdrop-blur-xl">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
          <Sprout className="h-6 w-6 animate-pulse text-primary" />
        </div>
        <div className="flex flex-col items-center gap-2">
          <div className="h-2 w-32 animate-pulse rounded-full bg-muted" />
          <div className="h-2 w-24 animate-pulse rounded-full bg-muted" />
        </div>
        <p className="text-sm text-muted-foreground">Loading CropPilot...</p>
      </div>
    </div>
  );
}