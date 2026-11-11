import type { NewsCategory } from "../../../../api/generated/schema";

export const NEWS_CATEGORY_ICON_PATH: Record<NewsCategory, string> = {
  company: "M2 11V2h8v9M4.5 4.5h1M7 4.5h1M4.5 7h1M7 7h1M1 11h10M4 11V8.5h4V11",
  earnings: "M1.5 10.5h9M3 10V6.5M6 10V3.5M9 10V5",
  central_bank: "M1 4.5 6 1.5l5 3M2 5v4.5M4.67 5v4.5M7.33 5v4.5M10 5v4.5M1 10.5h10",
  politics: "M1 4.5 6 1.5l5 3M1 4.5h10M2 5v4.5M4.67 5v4.5M7.33 5v4.5M10 5v4.5M1 10.5h10",
  commodities: "M6 1C6 1 2.5 5 2.5 7.5a3.5 3.5 0 0 0 7 0C9.5 5 6 1 6 1Z",
  fx: "M1.5 4h8l-2-2M10.5 8H2.5l2 2",
  other: "M2 1.5h8v9H2zM4 4h4M4 6h4M4 8h2",
};
