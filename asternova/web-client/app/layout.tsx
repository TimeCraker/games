import type { Metadata } from "next";
import { Geist, Geist_Mono, Orbitron, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/sonner";
import { GlobalUiClickSfx } from "@/src/components/audio/GlobalUiClickSfx";
import { AnalyticsProvider } from "@/src/components/AnalyticsProvider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const orbitron = Orbitron({
  variable: "--font-orbitron",
  subsets: ["latin"],
  weight: ["400", "600", "700", "900"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: {
    default: "AsterNova Studio · 休闲游戏大厅",
    template: "%s · AsterNova",
  },
  description:
    "AsterNova Studio - Reach Beyond the Stars. 休闲小游戏联机大厅 + 立体三消闯关。",
  openGraph: {
    title: "AsterNova Studio",
    description: "Reach Beyond the Stars - 休闲游戏大厅",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${orbitron.variable} ${jetbrainsMono.variable} antialiased`}
      >
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <AnalyticsProvider>
          {children}
          </AnalyticsProvider>
          <GlobalUiClickSfx />
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  );
}
