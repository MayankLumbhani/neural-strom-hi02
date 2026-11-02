import { X } from "lucide-react";
import { useEffect, useId, useRef, type ReactNode } from "react";
import { Button } from "@/components/ui/button";

export interface DrawerProps {
  open: boolean;
  title: string;
  closeLabel: string;
  onClose: () => void;
  children: ReactNode;
}

export function Drawer({
  open,
  title,
  closeLabel,
  onClose,
  children,
}: DrawerProps) {
  const titleId = useId();
  const panelRef = useRef<HTMLDivElement>(null);
  const onCloseRef = useRef(onClose);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!open) {
      return;
    }

    const previousFocus = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    const panel = panelRef.current;
    panel?.focus();
    document.body.style.overflow = "hidden";

    function handleKeyDown(event: KeyboardEvent): void {
      if (event.key === "Escape") {
        onCloseRef.current();
        return;
      }

      if (event.key !== "Tab" || panel === null) {
        return;
      }

      const focusableElements = panel.querySelectorAll<HTMLElement>(
        'a[href], button:not(:disabled), input:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])',
      );
      const firstElement = focusableElements.item(0);
      const lastElement = focusableElements.item(focusableElements.length - 1);
      if (focusableElements.length === 0) {
        event.preventDefault();
      } else if (
        event.shiftKey &&
        (document.activeElement === firstElement || document.activeElement === panel)
      ) {
        event.preventDefault();
        lastElement.focus();
      } else if (
        !event.shiftKey &&
        (document.activeElement === lastElement || document.activeElement === panel)
      ) {
        event.preventDefault();
        firstElement.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
      if (previousFocus instanceof HTMLElement) {
        previousFocus.focus();
      }
    };
  }, [open]);

  if (!open) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-drawer flex justify-end bg-ink/50"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <section
        aria-labelledby={titleId}
        aria-modal="true"
        className="h-full w-full max-w-page overflow-y-auto bg-surface p-6 shadow-raised md:w-2/3"
        ref={panelRef}
        role="dialog"
        tabIndex={-1}
      >
        <header className="mb-6 flex items-start justify-between gap-4">
          <h2 className="text-title font-semibold text-ink" id={titleId}>
            {title}
          </h2>
          <Button
            aria-label={closeLabel}
            className="shrink-0"
            onClick={onClose}
            variant="ghost"
          >
            <X aria-hidden="true" className="icon" />
          </Button>
        </header>
        {children}
      </section>
    </div>
  );
}
