# Model Card: Synthetic Complaint Dataset

## Dataset generation

`ml/src/generate_dataset.py` drafts multilingual municipal complaints with the
official Google Gen AI Python SDK. All examples are LLM-drafted and synthetic;
no citizen records or other real personal data are used. No real generation run
was performed for this change, and no dataset/model metrics are reported here.

### Generation prompt

Each request asks for 15 distinct complaints in strict JSON for one department
and one language. The language code, tier, and script are read from
`nlp/languages.py`; Hindi and Gujarati use their native scripts, Hinglish uses
romanized Hindi in Latin letters, and Tier 2 languages use their native
scripts. Prompts ask for varied polite, angry, brief, and detailed tones; varied
length and spoken style; occasional realistic typos; fictional concrete details
and duration; and about 25% of examples without a location. About 30% should
start directly with the issue, without a greeting or formula; no one named
opener such as “Hey”, “Excuse me”, or “Urgent:” should exceed 10% of a batch.
About 15% should be informal (lowercase, missing punctuation, spelling errors,
or short fragments), and some should be multi-sentence stories.

Locations must be fictional and Indian-style: invented names ending in nagar,
society, chowk, colony, vas, or road; fictional ward numbers; or places near a
mandir, school, bus stop, or market. Prompts forbid Western-style street names,
real city, person, or organization names, phone numbers, full street addresses,
unrelated code-mixing, and repeated or closely paraphrased phrasings within a
batch.

Every non-TAX prompt confines complaints to that department's physical or
service issue and explicitly prohibits billing, payment, overcharge, and
meter-reading-bill complaints. Those issues, including water and electricity
bills, belong only to TAX. TAX prompts cover property-tax and billing issues.

For `OTHER`, prompts require varied vague or ambiguous complaints, general
municipal questions, and issues that fit none of the other departments; one
fixed generic sentence is not sufficient.

### Settings and commands

| Environment setting | Default | Purpose |
|---|---:|---|
| `GEMINI_API_KEY` | unset | Required Google API credential; never logged |
| `GEMINI_MODEL` | unset | Required model name; generation fails clearly if missing |
| `DATASET_SEED` | `20261031` | Seed for reproducible stratified splits |
| `DATASET_TIER1_SAMPLES_PER_CLASS_LANGUAGE` | `100` | Target examples per department and Tier 1 language |
| `DATASET_TIER2_SAMPLES_PER_CLASS_LANGUAGE` | `30` | Target examples per department and Tier 2 language |
| `DATASET_MINIMUM_STRATUM_FRACTION` | `0.9` | Minimum target fraction accepted after the configured batch budget |
| `LLM_TIMEOUT_SECONDS` | `10` | API request timeout |

Prompt and validation limits: 15 complaints per request; 25% without a
location; 30% without a greeting/formula; 15% informal; no named opener above
10% of a batch; and at least 80% native-script letters for non-Latin
languages. The native-script percentage is computed over alphabetic
characters only; digits, spaces, and punctuation do not affect the share.
Non-Latin rows may include Latin loanwords only while at least 80% of their
letters remain in the registry script. English rows must not contain registry
Hinglish marker words, while Hinglish rows must contain at least one.

Repeated-word validation tokenizes Unicode letters and numbers while keeping
combining marks attached to their word. Cached `hi/WATER` responses showed that
the prior `\w+` tokenization split Devanagari vowel marks and falsely flagged
ordinary words as repeated; the Unicode-aware tokenizer fixes that without
weakening genuine adjacent-word rejection. Native-script validation still
requires at least 80% of alphabetic characters to match the registry script;
digits, punctuation, and combining marks are excluded from that letter-share
calculation.

`DATASET_MINIMUM_STRATUM_FRACTION` defaults to `0.9`. A stratum with at least
90% of its target is retained with a warning and included in a final shortfall
summary; a stratum below the configured fraction fails the run. Drop reasons
are included in each language/department stratum log entry. Cached files store
raw JSON responses and are validated again on every run, so updated validation
rules take effect without another model request.

Set the required Gemini settings in `.env`, then run
`python -m ml.src.generate_dataset --check` to make one small request without
writing data. Use `make generate-dataset` for a full run, or
`python -m ml.src.generate_dataset --limit N` to process at most N batches.
Each run logs the configured model name and kept/dropped counts by language
and department. The API key is not logged.

API responses must be JSON arrays of strings. The generator strips whitespace,
enforces a 12-to-500 character length, checks registry-script proportions,
rejects English rows containing registry Hinglish markers, and rejects
Hinglish rows without one. It also rejects non-TAX billing terms, Western-style
place-name suffixes, repeated adjacent words, phone-number-like digit runs,
and excess repeated named openers. Normalized exact and near duplicates are
dropped. These checks do not guarantee that all real place, person, or
organization names are recognized. The generator retries rate-limit and server
errors with exponential backoff and spaces API calls. Raw response batches are
saved to the Git-ignored `ml/data/raw/llm_batches/` directory and reused on a
rerun for the same model, language, and department.

The generated train and validation files remain at
`ml/data/processed/train.csv` and `ml/data/processed/validation.csv`. Rows
include `text`, `label`, `language`, `tier`, `variation`, `verified`, and
`source`; generated rows use `variation=llm_generated`, `verified=false`, and
`source=llm`. The split is stratified by language and department using the
configured seed, with no normalized complaint text shared between splits.
Generated CSVs and raw batches are ignored by Git.

### Preparing a manual-review sample

After generating the training data, run `make review-sample` to select 50
random training rows per enabled Tier 1 language using seed `20261031`. The
script writes `ml/data/review/review_sample.csv` with columns
`text,label,language,verdict,notes`; the last two columns are blank for the
reviewer. The review directory is ignored by Git. Creating the sample does not
count as completing the review: record the human review outcome below.

## Review status and limitations

- **Tier 1 (English, Hindi, Gujarati, Hinglish):** Generated examples are
  synthetic and LLM-drafted, not manually reviewed, and not quality-verified.
  A human must review at least 50 generated rows per Tier 1 language and record
  the outcome here before treating this dataset as reviewed.
- **Tier 2 (Marathi, Bengali, Tamil, Telugu, Kannada, Malayalam, Punjabi):**
  Experimental, LLM-drafted, synthetic, and unverified by native speakers.
- The `verified` column is `false` for every generated row. It is not a
  substitute for the independent, hand-written evaluation set, which must
  remain separate and must never be used for training.
- Prompt constraints and automated validation reduce common defects but do
  not establish factuality, native-speaker quality, or label correctness.
- No model metrics are reported here; none have been measured by this generator.
