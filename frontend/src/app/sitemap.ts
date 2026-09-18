import { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://onegov.ai";

  const staticRoutes = [
    "",
    "/services",
    "/schemes",
    "/categories",
    "/search",
    "/about",
    "/faq",
    "/contact",
    "/privacy",
    "/terms",
    "/login",
    "/register",
  ].map((route) => ({
    url: `${baseUrl}${route}`,
    lastModified: new Date(),
    changeFrequency: "daily" as const,
    priority: route === "" ? 1.0 : 0.8,
  }));

  return staticRoutes;
}
