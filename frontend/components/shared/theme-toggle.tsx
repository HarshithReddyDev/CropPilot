"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Sun, Moon, Monitor } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

const modes = [
  { value: "light", icon: Sun, key: "assistant.themeLight" },
  { value: "dark", icon: Moon, key: "assistant.themeDark" },
  { value: "system", icon: Monitor, key: "assistant.themeSystem" },
] as const;

type Mode = (typeof modes)[number]["value"];

export function ThemeToggle() {
  const { t } = useTranslation();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return (
      <button
        className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-background"
        aria-label={t("assistant.themeToggle")}
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
      aria-label={t("assistant.themeCurrent", { theme: theme ?? "system", next: t(nextMode.key) })}
      title={t(modes.find((m) => m.value === theme)?.key ?? "assistant.themeSystem")}
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
