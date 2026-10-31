"""Generate deterministic synthetic complaint data for classifier training."""

import argparse
import csv
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypedDict

from grievance.core.config import get_settings
from grievance.core.logging import configure_logging, logger
from grievance.nlp.languages import LANGUAGES
from grievance.seed import DEPARTMENTS


@dataclass(frozen=True)
class GenerationConfig:
    """Reproducible dataset size, split, and randomness settings."""

    seed: int = 20261031
    validation_fraction: float = 0.2
    tier1_samples_per_class_language: int = 50
    tier2_samples_per_class_language: int = 10

    def __post_init__(self) -> None:
        """Validate dataset generation settings."""
        if not 0 < self.validation_fraction < 1:
            raise ValueError("validation_fraction must be between 0 and 1")
        if self.tier1_samples_per_class_language < 2:
            raise ValueError("tier1_samples_per_class_language must be at least 2")
        if self.tier2_samples_per_class_language < 2:
            raise ValueError("tier2_samples_per_class_language must be at least 2")


class DatasetRow(TypedDict):
    """One synthetic complaint and its classification metadata."""

    text: str
    label: str
    language: str
    tier: int
    variation: str
    verified: bool


@dataclass(frozen=True)
class DatasetSplit:
    """Stratified training and validation rows."""

    train: list[DatasetRow]
    validation: list[DatasetRow]


DEPARTMENT_CODES: Final[tuple[str, ...]] = tuple(department.code for department in DEPARTMENTS)

COMPLAINTS: Final[dict[str, dict[str, str]]] = {
    "en": {
        "WATER": "There is no water supply at my home",
        "ROADS": "A pothole has damaged the road",
        "SANITATION": "The garbage has not been collected",
        "ELECTRICITY": "The power supply keeps cutting out",
        "STREETLIGHT": "The street light is not working",
        "DRAINAGE": "The drain is blocked and overflowing",
        "HEALTH": "Mosquitoes are breeding near the houses",
        "TAX": "My property tax bill has the wrong amount",
        "OTHER": "I need help with a municipal problem",
    },
    "hi": {
        "WATER": "मेरे घर में पानी की आपूर्ति नहीं हो रही है",
        "ROADS": "सड़क पर गहरा गड्ढा हो गया है",
        "SANITATION": "कचरा कई दिनों से नहीं उठाया गया है",
        "ELECTRICITY": "बिजली बार बार चली जाती है",
        "STREETLIGHT": "गली की स्ट्रीट लाइट काम नहीं कर रही है",
        "DRAINAGE": "नाली बंद है और पानी बाहर बह रहा है",
        "HEALTH": "घरों के पास मच्छर पनप रहे हैं",
        "TAX": "मेरे संपत्ति कर के बिल में गलत राशि है",
        "OTHER": "मुझे नगर निगम की समस्या में मदद चाहिए",
    },
    "gu": {
        "WATER": "મારા ઘરે પાણીનો પુરવઠો આવતો નથી",
        "ROADS": "રસ્તા પર મોટો ખાડો પડી ગયો છે",
        "SANITATION": "કચરો ઘણા દિવસથી ઉપાડવામાં આવ્યો નથી",
        "ELECTRICITY": "વીજળી વારંવાર જતી રહે છે",
        "STREETLIGHT": "શેરીની સ્ટ્રીટ લાઇટ કામ કરતી નથી",
        "DRAINAGE": "ગટર બંધ છે અને પાણી બહાર વહી રહ્યું છે",
        "HEALTH": "ઘરો પાસે મચ્છરો વધી રહ્યા છે",
        "TAX": "મારા મિલકત વેરાના બિલમાં ખોટી રકમ છે",
        "OTHER": "મને નગરપાલિકાની સમસ્યામાં મદદ જોઈએ છે",
    },
    "hinglish": {
        "WATER": "Mere ghar mein paani supply nahi aa rahi hai",
        "ROADS": "Road par bada pothole ho gaya hai",
        "SANITATION": "Kachra kai din se collect nahi hua",
        "ELECTRICITY": "Bijli baar baar ja rahi hai",
        "STREETLIGHT": "Gali ki street light kaam nahi kar rahi",
        "DRAINAGE": "Naali block hai aur paani overflow ho raha hai",
        "HEALTH": "Ghar ke paas machhar badh rahe hain",
        "TAX": "Mere property tax bill mein amount galat hai",
        "OTHER": "Mujhe municipal problem mein help chahiye",
    },
    "mr": {
        "WATER": "माझ्या घरी पाणीपुरवठा होत नाही",
        "ROADS": "रस्त्यावर मोठा खड्डा पडला आहे",
        "SANITATION": "कचरा अनेक दिवसांपासून उचलला नाही",
        "ELECTRICITY": "वीज वारंवार जाते",
        "STREETLIGHT": "रस्त्यावरील दिवा काम करत नाही",
        "DRAINAGE": "नाला तुंबला आहे आणि पाणी बाहेर वाहत आहे",
        "HEALTH": "घरांजवळ डास वाढत आहेत",
        "TAX": "माझ्या मालमत्ता कराच्या बिलात चुकीची रक्कम आहे",
        "OTHER": "मला महानगरपालिकेच्या समस्येसाठी मदत हवी आहे",
    },
    "bn": {
        "WATER": "আমার বাড়িতে জল সরবরাহ হচ্ছে না",
        "ROADS": "রাস্তায় বড় গর্ত হয়েছে",
        "SANITATION": "অনেক দিন ধরে আবর্জনা সরানো হয়নি",
        "ELECTRICITY": "বারবার বিদ্যুৎ চলে যাচ্ছে",
        "STREETLIGHT": "রাস্তার বাতি কাজ করছে না",
        "DRAINAGE": "নর্দমা বন্ধ এবং জল উপচে পড়ছে",
        "HEALTH": "বাড়ির কাছে মশা বাড়ছে",
        "TAX": "আমার সম্পত্তি করের বিলে ভুল অঙ্ক রয়েছে",
        "OTHER": "পৌরসভার একটি সমস্যায় আমার সাহায্য দরকার",
    },
    "ta": {
        "WATER": "எங்கள் வீட்டில் தண்ணீர் விநியோகம் இல்லை",
        "ROADS": "சாலையில் பெரிய பள்ளம் ஏற்பட்டுள்ளது",
        "SANITATION": "பல நாட்களாக குப்பை அகற்றப்படவில்லை",
        "ELECTRICITY": "மின்சாரம் அடிக்கடி துண்டிக்கப்படுகிறது",
        "STREETLIGHT": "தெரு விளக்கு வேலை செய்யவில்லை",
        "DRAINAGE": "சாக்கடை அடைந்து நீர் வெளியே வழிகிறது",
        "HEALTH": "வீடுகளுக்கு அருகில் கொசுக்கள் பெருகுகின்றன",
        "TAX": "என் சொத்து வரி ரசீதில் தவறான தொகை உள்ளது",
        "OTHER": "நகராட்சி பிரச்சினைக்கு எனக்கு உதவி தேவை",
    },
    "te": {
        "WATER": "మా ఇంటికి నీటి సరఫరా రావడం లేదు",
        "ROADS": "రోడ్డుపై పెద్ద గుంత ఏర్పడింది",
        "SANITATION": "చాలా రోజులుగా చెత్తను తొలగించలేదు",
        "ELECTRICITY": "విద్యుత్ తరచుగా నిలిచిపోతోంది",
        "STREETLIGHT": "వీధి దీపం పనిచేయడం లేదు",
        "DRAINAGE": "మురుగు కాలువ మూసుకుపోయి నీరు బయటకు వస్తోంది",
        "HEALTH": "ఇళ్ల దగ్గర దోమలు పెరుగుతున్నాయి",
        "TAX": "నా ఆస్తి పన్ను బిల్లులో తప్పు మొత్తం ఉంది",
        "OTHER": "మున్సిపల్ సమస్యలో నాకు సహాయం కావాలి",
    },
    "kn": {
        "WATER": "ನಮ್ಮ ಮನೆಗೆ ನೀರಿನ ಸರಬರಾಜು ಆಗುತ್ತಿಲ್ಲ",
        "ROADS": "ರಸ್ತೆಯಲ್ಲಿ ದೊಡ್ಡ ಗುಂಡಿ ಬಿದ್ದಿದೆ",
        "SANITATION": "ಹಲವು ದಿನಗಳಿಂದ ಕಸವನ್ನು ತೆಗೆದಿಲ್ಲ",
        "ELECTRICITY": "ವಿದ್ಯುತ್ ಪದೇ ಪದೇ ಕಡಿತವಾಗುತ್ತಿದೆ",
        "STREETLIGHT": "ಬೀದಿ ದೀಪ ಕೆಲಸ ಮಾಡುತ್ತಿಲ್ಲ",
        "DRAINAGE": "ಚರಂಡಿ ಮುಚ್ಚಿಕೊಂಡು ನೀರು ಹೊರಗೆ ಹರಿಯುತ್ತಿದೆ",
        "HEALTH": "ಮನೆಗಳ ಬಳಿ ಸೊಳ್ಳೆಗಳು ಹೆಚ್ಚಾಗುತ್ತಿವೆ",
        "TAX": "ನನ್ನ ಆಸ್ತಿ ತೆರಿಗೆ ಬಿಲ್‌ನಲ್ಲಿ ತಪ್ಪಾದ ಮೊತ್ತವಿದೆ",
        "OTHER": "ಪುರಸಭೆಯ ಸಮಸ್ಯೆಯಲ್ಲಿ ನನಗೆ ಸಹಾಯ ಬೇಕು",
    },
    "ml": {
        "WATER": "ഞങ്ങളുടെ വീട്ടിൽ വെള്ളം ലഭിക്കുന്നില്ല",
        "ROADS": "റോഡിൽ വലിയ കുഴി രൂപപ്പെട്ടിട്ടുണ്ട്",
        "SANITATION": "നിരവധി ദിവസമായി മാലിന്യം നീക്കം ചെയ്തിട്ടില്ല",
        "ELECTRICITY": "വൈദ്യുതി പലപ്പോഴും മുടങ്ങുന്നു",
        "STREETLIGHT": "തെരുവുവിളക്ക് പ്രവർത്തിക്കുന്നില്ല",
        "DRAINAGE": "ഓട അടഞ്ഞ് വെള്ളം പുറത്തേക്ക് ഒഴുകുന്നു",
        "HEALTH": "വീടുകൾക്ക് സമീപം കൊതുകുകൾ പെരുകുന്നു",
        "TAX": "എന്റെ വസ്തുനികുതി ബില്ലിൽ തെറ്റായ തുകയുണ്ട്",
        "OTHER": "മുനിസിപ്പൽ പ്രശ്നത്തിൽ എനിക്ക് സഹായം വേണം",
    },
    "pa": {
        "WATER": "ਸਾਡੇ ਘਰ ਪਾਣੀ ਦੀ ਸਪਲਾਈ ਨਹੀਂ ਆ ਰਹੀ",
        "ROADS": "ਸੜਕ ਉੱਤੇ ਵੱਡਾ ਟੋਆ ਪੈ ਗਿਆ ਹੈ",
        "SANITATION": "ਕਈ ਦਿਨਾਂ ਤੋਂ ਕੂੜਾ ਨਹੀਂ ਚੁੱਕਿਆ ਗਿਆ",
        "ELECTRICITY": "ਬਿਜਲੀ ਵਾਰ ਵਾਰ ਬੰਦ ਹੋ ਜਾਂਦੀ ਹੈ",
        "STREETLIGHT": "ਗਲੀ ਦੀ ਬੱਤੀ ਕੰਮ ਨਹੀਂ ਕਰਦੀ",
        "DRAINAGE": "ਨਾਲੀ ਬੰਦ ਹੈ ਅਤੇ ਪਾਣੀ ਬਾਹਰ ਵਹਿ ਰਿਹਾ ਹੈ",
        "HEALTH": "ਘਰਾਂ ਨੇੜੇ ਮੱਛਰ ਵਧ ਰਹੇ ਹਨ",
        "TAX": "ਮੇਰੇ ਜਾਇਦਾਦ ਕਰ ਦੇ ਬਿੱਲ ਵਿੱਚ ਗਲਤ ਰਕਮ ਹੈ",
        "OTHER": "ਮੈਨੂੰ ਨਗਰ ਨਿਗਮ ਦੀ ਸਮੱਸਿਆ ਵਿੱਚ ਮਦਦ ਚਾਹੀਦੀ ਹੈ",
    },
}

VARIATIONS: Final[tuple[str, ...]] = (
    "clean",
    "typo",
    "slang",
    "code_mixed",
    "missing_location",
    "ambiguous",
)

HELP_SUFFIXES: Final[dict[str, str]] = {
    "en": " pls help",
    "hi": " कृपया जल्दी मदद करें",
    "gu": " કૃપા કરીને જલ્દી મદદ કરો",
    "hinglish": " pls jaldi help karo",
    "mr": " कृपया लवकर मदत करा",
    "bn": " দয়া করে তাড়াতাড়ি সাহায্য করুন",
    "ta": " தயவுசெய்து விரைவாக உதவுங்கள்",
    "te": " దయచేసి త్వరగా సహాయం చేయండి",
    "kn": " ದಯವಿಟ್ಟು ಬೇಗ ಸಹಾಯ ಮಾಡಿ",
    "ml": " ദയവായി വേഗം സഹായിക്കൂ",
    "pa": " ਕਿਰਪਾ ਕਰਕੇ ਜਲਦੀ ਮਦਦ ਕਰੋ",
}

AMBIGUOUS_PREFIXES: Final[dict[str, str]] = {
    "en": "I think maybe ",
    "hi": "शायद ",
    "gu": "કદાચ ",
    "hinglish": "Shayad ",
    "mr": "कदाचित ",
    "bn": "হয়তো ",
    "ta": "ஒருவேளை ",
    "te": "బహుశా ",
    "kn": "ಬಹುಶಃ ",
    "ml": "ഒരുപക്ഷേ ",
    "pa": "ਸ਼ਾਇਦ ",
}

LOCATION_SUFFIXES: Final[dict[str, str]] = {
    "en": " near Ward {ward}",
    "hi": " वार्ड {ward} में",
    "gu": " વોર્ડ {ward}માં",
    "hinglish": " Ward {ward} mein",
    "mr": " प्रभाग {ward} जवळ",
    "bn": " ওয়ার্ড {ward}-এর কাছে",
    "ta": " வார்டு {ward} அருகில்",
    "te": " వార్డు {ward} దగ్గర",
    "kn": " ವಾರ್ಡ್ {ward} ಬಳಿ",
    "ml": " വാർഡ് {ward} സമീപം",
    "pa": " ਵਾਰਡ {ward} ਨੇੜੇ",
}

MISSING_LOCATION_DETAILS: Final[dict[str, str]] = {
    "en": " for {days} days",
    "hi": " पिछले {days} दिनों से",
    "gu": " છેલ્લા {days} દિવસથી",
    "hinglish": " pichhle {days} din se",
    "mr": " मागील {days} दिवसांपासून",
    "bn": " গত {days} দিন ধরে",
    "ta": " கடந்த {days} நாட்களாக",
    "te": " గత {days} రోజులుగా",
    "kn": " ಕಳೆದ {days} ದಿನಗಳಿಂದ",
    "ml": " കഴിഞ്ഞ {days} ദിവസമായി",
    "pa": " ਪਿਛਲੇ {days} ਦਿਨਾਂ ਤੋਂ",
}


def _validate_catalogs() -> None:
    """Ensure every registry language and seeded department has source phrases."""
    language_codes = set(LANGUAGES)
    if set(COMPLAINTS) != language_codes:
        raise ValueError("Complaint phrase languages must match the language registry")
    if set(HELP_SUFFIXES) != language_codes or set(AMBIGUOUS_PREFIXES) != language_codes:
        raise ValueError("Variation text languages must match the language registry")
    if set(LOCATION_SUFFIXES) != language_codes or set(MISSING_LOCATION_DETAILS) != language_codes:
        raise ValueError("Variation text languages must match the language registry")
    for language_code, phrases in COMPLAINTS.items():
        if set(phrases) != set(DEPARTMENT_CODES):
            raise ValueError(f"Complaint labels are incomplete for language {language_code}")


def _apply_variation(
    phrase: str,
    language_code: str,
    variation: str,
    ward_number: int,
    duration_days: int,
) -> str:
    """Apply one deterministic synthetic language or complaint-quality variation."""
    if variation == "typo":
        words = phrase.split(maxsplit=1)
        if len(words) == 1:
            phrase = f"{words[0]} {words[0]}"
        else:
            phrase = f"{words[0]} {words[0]} {words[1]}"
    elif variation == "slang":
        phrase += HELP_SUFFIXES[language_code]
    elif variation == "code_mixed":
        phrase += " paani nahi aa raha" if language_code == "en" else " urgent please help"
    elif variation == "ambiguous":
        phrase = AMBIGUOUS_PREFIXES[language_code] + phrase
    elif variation == "missing_location":
        phrase += MISSING_LOCATION_DETAILS[language_code].format(days=duration_days)

    if variation != "missing_location":
        phrase += LOCATION_SUFFIXES[language_code].format(ward=ward_number)
    return phrase


def _generate_stratum(
    language_code: str,
    tier: int,
    label: str,
    sample_count: int,
) -> list[DatasetRow]:
    """Generate an equal-sized synthetic sample group for one label and language."""
    phrase = COMPLAINTS[language_code][label]
    rows: list[DatasetRow] = []
    for sample_index in range(sample_count):
        variation = VARIATIONS[sample_index % len(VARIATIONS)]
        ward_number = sample_index // len(VARIATIONS) + 1
        rows.append(
            {
                "text": _apply_variation(
                    phrase,
                    language_code,
                    variation,
                    ward_number,
                    duration_days=sample_index // len(VARIATIONS) + 1,
                ),
                "label": label,
                "language": language_code,
                "tier": tier,
                "variation": variation,
                "verified": False,
            }
        )
    return rows


def generate_dataset(config: GenerationConfig | None = None) -> DatasetSplit:
    """Generate balanced, stratified training and validation examples."""
    config = config or GenerationConfig()
    _validate_catalogs()
    rng = random.Random(config.seed)
    train_rows: list[DatasetRow] = []
    validation_rows: list[DatasetRow] = []

    for language_code, language in LANGUAGES.items():
        if not language.enabled:
            continue
        sample_count = (
            config.tier1_samples_per_class_language
            if language.tier == 1
            else config.tier2_samples_per_class_language
        )
        for label in DEPARTMENT_CODES:
            stratum = _generate_stratum(language_code, language.tier, label, sample_count)
            rng.shuffle(stratum)
            validation_count = max(1, round(sample_count * config.validation_fraction))
            validation_rows.extend(stratum[:validation_count])
            train_rows.extend(stratum[validation_count:])

    rng.shuffle(train_rows)
    rng.shuffle(validation_rows)
    return DatasetSplit(train=train_rows, validation=validation_rows)


def write_split(path: Path, rows: list[DatasetRow]) -> None:
    """Write one dataset split as UTF-8 CSV with a stable column order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ("text", "label", "language", "tier", "variation", "verified")
    with path.open("w", encoding="utf-8-sig", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({**row, "verified": str(row["verified"]).lower()} for row in rows)


def write_dataset(output_dir: Path, split: DatasetSplit) -> tuple[Path, Path]:
    """Write training and validation CSV files under the requested directory."""
    train_path = output_dir / "train.csv"
    validation_path = output_dir / "validation.csv"
    write_split(train_path, split.train)
    write_split(validation_path, split.validation)
    return train_path, validation_path


def _parse_args() -> argparse.Namespace:
    """Parse command-line settings for repeatable dataset generation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("ml/data/processed"),
        help="directory for generated train.csv and validation.csv",
    )
    parser.add_argument("--seed", type=int, default=GenerationConfig.seed)
    parser.add_argument(
        "--validation-fraction",
        type=float,
        default=GenerationConfig.validation_fraction,
    )
    parser.add_argument(
        "--tier1-samples-per-class-language",
        type=int,
        default=GenerationConfig.tier1_samples_per_class_language,
    )
    parser.add_argument(
        "--tier2-samples-per-class-language",
        type=int,
        default=GenerationConfig.tier2_samples_per_class_language,
    )
    return parser.parse_args()


def main() -> None:
    """Generate and write both dataset splits from the command line."""
    args = _parse_args()
    settings = get_settings()
    configure_logging(settings.log_level)
    config = GenerationConfig(
        seed=args.seed,
        validation_fraction=args.validation_fraction,
        tier1_samples_per_class_language=args.tier1_samples_per_class_language,
        tier2_samples_per_class_language=args.tier2_samples_per_class_language,
    )
    split = generate_dataset(config)
    train_path, validation_path = write_dataset(args.output_dir, split)
    logger.info(
        "ml.dataset.generated train_rows=%d validation_rows=%d train_path=%s validation_path=%s",
        len(split.train),
        len(split.validation),
        train_path,
        validation_path,
    )


if __name__ == "__main__":
    main()
