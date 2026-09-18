import type { Metadata, Viewport } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import { ThemeProvider } from "next-themes";
import { Toaster } from "sonner";
import { ReactQueryProvider } from "@/components/providers/ReactQueryProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "OneGov AI — One Platform. Every Government Service.",
    template: "%s | OneGov AI",
  },
  description:
    "AI-powered platform helping Indian citizens discover, understand, and access 1000+ government services and schemes instantly.",
  keywords: ["government services", "India", "AI", "schemes", "Aadhaar", "passport"],
  openGraph: {
    type: "website",
    locale: "en_IN",
    title: "OneGov AI",
    description: "AI-powered access to every Indian government service.",
    siteName: "OneGov AI",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: "#030712",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${GeistSans.variable} ${GeistMono.variable}`}
      suppressHydrationWarning
    >
      <body className="min-h-screen bg-background font-sans antialiased">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem disableTransitionOnChange>
          <ReactQueryProvider>
            {children}
            <Toaster
              position="top-right"
              theme="dark"
              richColors
              closeButton
              toastOptions={{
                style: {
                  background: "hsl(222 47% 7%)",
                  border: "1px solid hsl(222 30% 14%)",
                  color: "hsl(210 40% 96%)",
                },
              }}
            />
          </ReactQueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
