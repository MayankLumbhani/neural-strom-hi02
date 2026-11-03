import { Button } from "@/components/ui/button";
import { UI_LANGUAGES, type UiLanguage } from "@/lib/i18n";

interface LanguageSwitcherProps {
  language: UiLanguage;
  label: string;
  onLanguageChange: (language: UiLanguage) => void;
}

/** Render the accessible Tier 1 interface language selector. */
export function LanguageSwitcher({
  language,
  label,
  onLanguageChange,
}: LanguageSwitcherProps) {
  return (
    <fieldset className="flex flex-wrap items-center gap-2">
      <legend className="sr-only">{label}</legend>
      {UI_LANGUAGES.map(({ code, label: languageName }) => (
        <Button
          aria-pressed={language === code}
          key={code}
          onClick={() => onLanguageChange(code)}
          type="button"
          variant={language === code ? "primary" : "secondary"}
        >
          {languageName}
        </Button>
      ))}
    </fieldset>
  );
}
