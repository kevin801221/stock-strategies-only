import "./globals.css";
import Navigation from "@/components/Navigation";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Stock Strategies — 策略庫",
  description: "台股每日選股策略庫 + AI 生策略",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-TW">
      <body>
        <div className="min-h-screen flex flex-col">
          <a href="#main-content" className="skip-link">跳至主要內容</a>
          <Navigation />
          <main id="main-content" className="flex-1">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-10">{children}</div>
          </main>
          <footer className="border-t border-line text-xs text-muted">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 py-5">
              本工具僅供研究與紀錄之用，不構成投資建議。
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
