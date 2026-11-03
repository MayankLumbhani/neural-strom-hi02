import type { Config } from "tailwindcss";
import animate from "tailwindcss-animate";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        surface: "var(--color-surface)",
        "surface-muted": "var(--color-surface-muted)",
        border: "var(--color-border)",
        "border-strong": "var(--color-border-strong)",
        ink: "var(--color-ink)",
        "ink-muted": "var(--color-ink-muted)",
        primary: "var(--color-primary)",
        "primary-hover": "var(--color-primary-hover)",
        "on-primary": "var(--color-on-primary)",
        accent: "var(--color-accent)",
        "on-accent": "var(--color-on-accent)",
        focus: "var(--color-focus)",
        danger: "var(--color-danger)",
        "danger-hover": "var(--color-danger-hover)",
        "filed-bg": "var(--status-filed-bg)",
        "filed-fg": "var(--status-filed-fg)",
        "assigned-bg": "var(--status-assigned-bg)",
        "assigned-fg": "var(--status-assigned-fg)",
        "progress-bg": "var(--status-progress-bg)",
        "progress-fg": "var(--status-progress-fg)",
        "resolved-bg": "var(--status-resolved-bg)",
        "resolved-fg": "var(--status-resolved-fg)",
        "escalated-bg": "var(--status-escalated-bg)",
        "escalated-fg": "var(--status-escalated-fg)",
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
        mono: ["var(--font-mono)"],
      },
      fontSize: {
        display: ["var(--text-display)", { lineHeight: "var(--line-height-heading)" }],
        title: ["var(--text-title)", { lineHeight: "var(--line-height-heading)" }],
        heading: ["var(--text-heading)", { lineHeight: "var(--line-height-heading)" }],
        body: ["var(--text-body)", { lineHeight: "var(--line-height-body)" }],
        small: ["var(--text-small)", { lineHeight: "var(--line-height-body)" }],
      },
      spacing: {
        1: "var(--space-1)",
        2: "var(--space-2)",
        3: "var(--space-3)",
        4: "var(--space-4)",
        6: "var(--space-6)",
        8: "var(--space-8)",
        12: "var(--space-12)",
        touch: "var(--touch-target)",
      },
      minHeight: {
        textarea: "var(--textarea-min-height)",
      },
      height: {
        chart: "var(--chart-height)",
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        card: "var(--radius-card)",
        pill: "var(--radius-pill)",
      },
      borderWidth: {
        DEFAULT: "var(--border-width)",
        4: "var(--ticket-edge-width)",
      },
      ringWidth: {
        DEFAULT: "var(--focus-ring-width)",
      },
      ringOffsetWidth: {
        DEFAULT: "var(--focus-ring-offset)",
      },
      boxShadow: {
        card: "var(--shadow-card)",
        raised: "var(--shadow-raised)",
      },
      maxWidth: {
        chat: "var(--chat-bubble-max-width)",
        page: "var(--page-max-width)",
      },
      transitionDuration: {
        fast: "var(--motion-fast)",
        base: "var(--motion-base)",
      },
      transitionTimingFunction: {
        civic: "var(--motion-ease)",
      },
      zIndex: {
        drawer: "var(--layer-drawer)",
      },
    },
  },
  plugins: [animate],
} satisfies Config;
