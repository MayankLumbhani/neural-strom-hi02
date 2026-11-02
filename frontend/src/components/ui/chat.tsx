import type { ButtonHTMLAttributes, HTMLAttributes } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface ChatBubbleProps extends HTMLAttributes<HTMLDivElement> {
  sender: "citizen" | "bot";
  language: string;
  message: string;
}

export function ChatBubble({
  sender,
  language,
  message,
  className,
  ...props
}: ChatBubbleProps) {
  const isCitizen = sender === "citizen";

  return (
    <div
      className={cn(
        "flex w-full",
        isCitizen ? "justify-end" : "justify-start",
        className,
      )}
      {...props}
    >
      <p
        className={cn(
          "max-w-chat break-words rounded-card border px-4 py-3 text-body",
          isCitizen
            ? "border-primary bg-primary text-on-primary"
            : "border-border bg-surface text-ink",
        )}
        lang={language}
      >
        {message}
      </p>
    </div>
  );
}

export interface QuickReplyProps
  extends Omit<
    ButtonHTMLAttributes<HTMLButtonElement>,
    "onClick" | "onSelect"
  > {
  label: string;
  onSelect: (label: string) => void;
}

export function QuickReply({
  label,
  onSelect,
  className,
  ...props
}: QuickReplyProps) {
  return (
    <Button
      className={cn("rounded-pill text-start", className)}
      onClick={() => onSelect(label)}
      variant="secondary"
      {...props}
    >
      {label}
    </Button>
  );
}
