import { Eye, ShieldCheck, PenLine, Brain, type LucideIcon } from "lucide-react";

export type LensDef = {
  key: string;
  name: string;
  subtitle: string;
  description: string;
  icon: LucideIcon;
  /** CSS color token, one of --chart-1..5, kept distinct per lens for visual variety on an otherwise dark UI. */
  color: string;
};

export const LENSES: LensDef[] = [
  {
    key: "design-eye",
    name: "Design Eye",
    subtitle: "Layout & structure",
    description:
      "A vision model reviews hierarchy, whitespace, and call-to-action clarity, the way a senior designer would.",
    icon: Eye,
    color: "var(--chart-2)",
  },
  {
    key: "rule-book",
    name: "Rule Book",
    subtitle: "Accessibility & readability",
    description:
      "Real WCAG contrast math on sampled pixel colors, plus target-size checks. Deterministic, not a guess.",
    icon: ShieldCheck,
    color: "var(--chart-1)",
  },
  {
    key: "copy-editor",
    name: "Copy Editor",
    subtitle: "Text & content",
    description:
      "OCR pulls every visible string; flagged low-readability copy gets a clearer rewrite suggestion.",
    icon: PenLine,
    color: "var(--chart-3)",
  },
  {
    key: "psychologist",
    name: "Psychologist",
    subtitle: "User attention",
    description:
      "A real saliency model predicts where eyes actually go, so you can check it against where you want them to go.",
    icon: Brain,
    color: "var(--chart-4)",
  },
];
