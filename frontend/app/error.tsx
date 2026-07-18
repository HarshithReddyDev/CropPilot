"use client";

import { useEffect } from "react";
import { motion } from "framer-motion";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="relative w-full max-w-md overflow-hidden rounded-2xl border border-border/50 bg-card/80 p-8 shadow-xl backdrop-blur-xl"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-destructive/5 via-transparent to-transparent pointer-events-none" />
        <div className="relative flex flex-col items-center text-center">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 300, damping: 20, delay: 0.1 }}
            className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10"
          >
            <AlertTriangle className="h-8 w-8 text-destructive" />
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mb-2 text-2xl font-bold text-foreground"
          >
            Something went wrong
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mb-6 text-sm text-muted-foreground"
          >
            {error.message || "An unexpected error occurred. Please try again."}
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Button onClick={reset} variant="default" size="lg">
              Try again
            </Button>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}