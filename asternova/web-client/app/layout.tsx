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
        {/* skip link：首个 Tab 落点，跳到页面主内容（各页 main#main-content，tabIndex -1 可聚焦） */}
        <a
          href="#main-content"
          className="fixed left-4 top-4 z-[200] -translate-y-24 rounded-full border border-white/20 bg-space-black px-5 py-2.5 text-sm font-medium text-white shadow-lg outline-none transition-transform duration-fast focus:translate-y-0 focus-visible:ring-2 focus-visible:ring-violet-400/70"
        >
          跳到主内容
        </a>
        {/* 站点为深空黑单主题设计（Stage A）；enableSystem 关闭，避免浅色系统用户
            落入从未设计的浅色 token 拼盘（白底 + 硬编码白字不可读） */}
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false} forcedTheme="dark">
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
