import type { Metadata } from "next";
import { Fira_Sans, Fira_Code } from "next/font/google";
import { ConvexClientProvider } from "@/components/convex-client-provider";
import { SiteHeader } from "@/components/site-header";
import "./globals.css";

const firaSans = Fira_Sans({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const firaCode = Fira_Code({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Aura — AI UX Auditor",
  description:
    "Upload a screenshot or paste a URL and get an actionable UX audit: layout critique, real WCAG accessibility checks, copy clarity suggestions, and a genuine attention heatmap.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${firaSans.variable} ${firaCode.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col">
        <ConvexClientProvider>
          <SiteHeader />
          {children}
        </ConvexClientProvider>
      </body>
    </html>
  );
}
