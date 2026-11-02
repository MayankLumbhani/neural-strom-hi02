import { AlertCircle } from "lucide-react";
import { useId, type InputHTMLAttributes, type TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface ControlProps {
  label: string;
  error?: string;
  className?: string;
}

type InputProps = ControlProps & Omit<InputHTMLAttributes<HTMLInputElement>, "className">;

export function Input({ label, error, id, ...props }: InputProps) {
  const generatedId = useId();
  const controlId = id ?? generatedId;
  const errorId = `${controlId}-error`;

  return (
    <div className="grid gap-2">
      <label className="font-semibold text-ink" htmlFor={controlId}>
        {label}
      </label>
      <input
        {...props}
        id={controlId}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
        className={cn(
          "min-h-touch w-full rounded-sm border border-strong bg-surface px-3 text-body text-ink placeholder:text-ink-muted",
          "focus-visible:ring-2 focus-visible:ring-focus focus-visible:ring-offset-2",
          error && "border-danger",
          props.className,
        )}
      />
      {error ? <FieldError id={errorId} message={error} /> : null}
    </div>
  );
}

type TextareaProps = ControlProps &
  Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "className">;

export function Textarea({ label, error, id, ...props }: TextareaProps) {
  const generatedId = useId();
  const controlId = id ?? generatedId;
  const errorId = `${controlId}-error`;

  return (
    <div className="grid gap-2">
      <label className="font-semibold text-ink" htmlFor={controlId}>
        {label}
      </label>
      <textarea
        {...props}
        id={controlId}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
        className={cn(
          "min-h-textarea w-full resize-y rounded-sm border border-strong bg-surface px-3 py-2 text-body text-ink placeholder:text-ink-muted",
          "focus-visible:ring-2 focus-visible:ring-focus focus-visible:ring-offset-2",
          error && "border-danger",
          props.className,
        )}
      />
      {error ? <FieldError id={errorId} message={error} /> : null}
    </div>
  );
}

function FieldError({ id, message }: { id: string; message: string }) {
  return (
    <p
      className="flex items-start gap-2 text-small text-danger"
      id={id}
      role="alert"
    >
      <AlertCircle aria-hidden="true" className="icon mt-1" />
      <span>{message}</span>
    </p>
  );
}
