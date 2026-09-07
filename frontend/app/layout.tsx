import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sehat Samjho — AI Medical Report Analyzer",
  description: "Bilingual lab report explanations for patients in Pakistan",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full antialiased">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,500;0,600;1,500&family=IBM+Plex+Sans:wght@400;500;600&family=Noto+Naskh+Arabic:wght@400;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col" style={{ background: "var(--background)" }}>
        {children}
      </body>
    </html>
  );
}