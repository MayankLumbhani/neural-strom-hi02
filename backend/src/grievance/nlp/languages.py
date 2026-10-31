"""Registry for every supported language and its detection metadata."""

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class Language:
    """Metadata for one supported language."""

    code: str
    name_en: str
    name_native: str
    script: str
    tier: int
    font_family: str
    template_file: str
    verified: bool
    detection_markers: tuple[str, ...] = ()
    default_for_script: bool = False
    enabled: bool = True


SCRIPT_RANGES: Final[dict[str, tuple[tuple[int, int], ...]]] = {
    "Latin": ((ord("A"), ord("Z")), (ord("a"), ord("z"))),
    "Devanagari": ((0x0900, 0x097F),),
    "Bengali": ((0x0980, 0x09FF),),
    "Gurmukhi": ((0x0A00, 0x0A7F),),
    "Gujarati": ((0x0A80, 0x0AFF),),
    "Tamil": ((0x0B80, 0x0BFF),),
    "Telugu": ((0x0C00, 0x0C7F),),
    "Kannada": ((0x0C80, 0x0CFF),),
    "Malayalam": ((0x0D00, 0x0D7F),),
}

FALLBACK_LANGUAGE_CODES: Final[tuple[str, ...]] = ("en", "hi")

LANGUAGES: Final[dict[str, Language]] = {
    "en": Language(
        code="en",
        name_en="English",
        name_native="English",
        script="Latin",
        tier=1,
        font_family="Noto Sans",
        template_file="en.toml",
        verified=True,
        default_for_script=True,
    ),
    "hi": Language(
        code="hi",
        name_en="Hindi",
        name_native="हिन्दी",
        script="Devanagari",
        tier=1,
        font_family="Noto Sans Devanagari",
        template_file="hi.toml",
        verified=True,
        detection_markers=("है", "हैं", "नहीं", "मुझे", "मेरे", "रहा", "रही"),
        default_for_script=True,
    ),
    "gu": Language(
        code="gu",
        name_en="Gujarati",
        name_native="ગુજરાતી",
        script="Gujarati",
        tier=1,
        font_family="Noto Sans Gujarati",
        template_file="gu.toml",
        verified=True,
        default_for_script=True,
    ),
    "hinglish": Language(
        code="hinglish",
        name_en="Hinglish",
        name_native="Hinglish",
        script="Latin",
        tier=1,
        font_family="Noto Sans",
        template_file="hinglish.toml",
        verified=True,
        detection_markers=(
            "nahi",
            "nahin",
            "paani",
            "pani",
            "mere",
            "mujhe",
            "hai",
            "hain",
            "raha",
            "rahi",
        ),
    ),
    "mr": Language(
        code="mr",
        name_en="Marathi",
        name_native="मराठी",
        script="Devanagari",
        tier=2,
        font_family="Noto Sans Devanagari",
        template_file="mr.toml",
        verified=False,
        detection_markers=("आहे", "नाही", "मला", "माझा", "माझ्या", "मध्ये", "करा"),
    ),
    "bn": Language(
        code="bn",
        name_en="Bengali",
        name_native="বাংলা",
        script="Bengali",
        tier=2,
        font_family="Noto Sans Bengali",
        template_file="bn.toml",
        verified=False,
        default_for_script=True,
    ),
    "ta": Language(
        code="ta",
        name_en="Tamil",
        name_native="தமிழ்",
        script="Tamil",
        tier=2,
        font_family="Noto Sans Tamil",
        template_file="ta.toml",
        verified=False,
        default_for_script=True,
    ),
    "te": Language(
        code="te",
        name_en="Telugu",
        name_native="తెలుగు",
        script="Telugu",
        tier=2,
        font_family="Noto Sans Telugu",
        template_file="te.toml",
        verified=False,
        default_for_script=True,
    ),
    "kn": Language(
        code="kn",
        name_en="Kannada",
        name_native="ಕನ್ನಡ",
        script="Kannada",
        tier=2,
        font_family="Noto Sans Kannada",
        template_file="kn.toml",
        verified=False,
        default_for_script=True,
    ),
    "ml": Language(
        code="ml",
        name_en="Malayalam",
        name_native="മലയാളം",
        script="Malayalam",
        tier=2,
        font_family="Noto Sans Malayalam",
        template_file="ml.toml",
        verified=False,
        default_for_script=True,
    ),
    "pa": Language(
        code="pa",
        name_en="Punjabi",
        name_native="ਪੰਜਾਬੀ",
        script="Gurmukhi",
        tier=2,
        font_family="Noto Sans Gurmukhi",
        template_file="pa.toml",
        verified=False,
        default_for_script=True,
    ),
}
