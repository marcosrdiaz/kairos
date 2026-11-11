import type { NewsCategory } from "../../../../api/generated/schema";
import { NEWS_CATEGORY_ICON_PATH } from "./newsCategoryIconPaths";

export function NewsCategoryIcon({ category, className = "size-4" }: {
  category: NewsCategory;
  className?: string;
}) {
  return (
    <svg
      viewBox="0 0 12 12"
      aria-hidden="true"
      focusable="false"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.25"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d={NEWS_CATEGORY_ICON_PATH[category]} />
    </svg>
  );
}
