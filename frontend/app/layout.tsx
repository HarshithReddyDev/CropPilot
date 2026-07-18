import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Toaster } from "react-hot-toast";
import { AppProvider } from "@/providers/app-provider";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "CropPilot — Intelligent Agriculture Platform",
  description:
    "AI-powered platform for modern farming — crop health monitoring, disease detection, weather intelligence, market insights, and government scheme advisory.",
  keywords: [
    "agriculture",
    "farming",
    "AI",
    "crop health",
    "disease detection",
    "weather",
    "India",
  ],
  openGraph: {
    title: "CropPilot — Intelligent Agriculture Platform",
    description:
      "AI-powered platform for modern farming — crop health monitoring, disease detection, weather intelligence, market insights, and government scheme advisory.",
    type: "website",
    siteName: "CropPilot",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <AppProvider>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                borderRadius: "var(--radius)",
                background: "hsl(var(--background))",
                color: "hsl(var(--foreground))",
                border: "1px solid hsl(var(--border))",
              },
              success: {
                iconTheme: { primary: "#22c55e", secondary: "#fff" },
              },
              error: {
                iconTheme: { primary: "#ef4444", secondary: "#fff" },
              },
            }}
          />
        </AppProvider>
      </body>
    </html>
  );
}
