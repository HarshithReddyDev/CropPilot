"use client";

import { useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Check, Copy } from "lucide-react";
import { cn } from "@/lib/utils";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div className={cn("prose prose-sm dark:prose-invert max-w-none break-words", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ className, children, ...props }) {
            const isInline = !className;
            const codeStr = String(children).replace(/\n$/, "");
            if (isInline) {
              return (
                <code
                  className="rounded bg-muted px-1.5 py-0.5 text-sm font-mono text-foreground"
                  {...props}
                >
                  {children}
                </code>
              );
            }
            return <CodeBlock code={codeStr} language={className?.replace("language-", "")} />;
          },
          a({ href, children, ...props }) {
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary underline underline-offset-2 hover:text-primary/80"
                {...props}
              >
                {children}
              </a>
            );
          },
          table({ children }) {
            return (
              <div className="overflow-x-auto my-2">
                <table className="min-w-full border-collapse border border-border text-sm">
                  {children}
                </table>
              </div>
            );
          },
          th({ children }) {
            return (
              <th className="border border-border bg-muted/50 px-3 py-2 text-left font-semibold">
                {children}
              </th>
            );
          },
          td({ children }) {
            return <td className="border border-border px-3 py-2">{children}</td>;
          },
          blockquote({ children }) {
            return (
              <blockquote className="border-l-4 border-primary/30 bg-muted/30 pl-4 italic text-muted-foreground">
                {children}
              </blockquote>
            );
          },
          img({ src, alt }) {
            return (
              <img
                src={src}
                alt={alt || ""}
                className="rounded-lg max-w-full h-auto my-2"
                loading="lazy"
              />
            );
          },
        }}
      />
    </div>
  );
}

function CodeBlock({ code, language }: { code: string; language?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative my-3 rounded-lg border border-border overflow-hidden">
      <div className="flex items-center justify-between bg-muted/80 px-4 py-1.5 text-xs text-muted-foreground">
        <span>{language || "code"}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors"
        >
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="overflow-x-auto bg-card p-4 text-sm">
        <code className="text-foreground">{code}</code>
      </pre>
    </div>
  );
}
