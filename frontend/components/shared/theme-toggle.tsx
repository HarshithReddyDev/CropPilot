"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Sun, Moon, Monitor } from "lucide-react";
import { cn } from "@/lib/utils";

const modes = [
  { value: "light", icon: Sun, label: "Light" },
  { value: "dark", icon: Moon, label: "Dark" },
  { value: "system", icon: Monitor, label: "System" },
] as const;

type Mode = (typeof modes)[number]["value"];

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return (
      <button
        className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-background"
        aria-label="Toggle theme"
      >
        <Sun className="h-4 w-4" />
      </button>
    );
  }

  const currentIndex = modes.findIndex((m) => m.value === theme);
  const nextMode = modes[(currentIndex + 1) % modes.length];

  const handleCycle = () => {
    setTheme(nextMode.value);
  };

  return (
    <button
      onClick={handleCycle}
      className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-background hover:bg-accent transition-colors"
      aria-label={`Current theme: ${theme}. Click for ${nextMode.label}`}
      title={modes.find((m) => m.value === theme)?.label}
    >
      {modes.map(({ value, icon: Icon }) => (
        <Icon
          key={value}
          className={cn(
            "h-4 w-4 transition-all",
            theme === value
              ? "scale-100 opacity-100"
              : "scale-75 opacity-0 absolute"
          )}
        />
      ))}
    </button>
  );
}
