# Model Card: Synthetic Complaint Dataset

## Dataset generation

`ml/src/generate_dataset.py` drafts multilingual municipal complaints with the
official Google Gen AI Python SDK. All examples are LLM-drafted and synthetic;
no citizen records or other real personal data are used. The dataset was
generated in a prior run; no new generation is performed by the baseline
evaluation command.

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
| `LLM_TIMEOUT_SECONDS` | `60` | Per-request timeout in seconds |

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
organization names are recognized. The generator retries rate-limit, server,
timeout, and transport errors with exponential backoff. `LLM_TIMEOUT_SECONDS`
configures the per-request timeout and defaults to 60 seconds. Request spacing
applies only to actual API calls; cached raw batches replay without delay. Raw
responses are saved to the Git-ignored `ml/data/raw/llm_batches/` directory
and reused on a rerun for the same model, language, and department. If retries
are exhausted, the generator exits with a short message; completed batches
remain cached, and rerunning the same command resumes from them.

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
`text,label,language,verdict,notes`; the last two columns are initially blank
and filled during review. The review directory is ignored by Git. Creating a
sample does not count as completing the review: record the review outcome
below.

### Tier 1 review log

- Reviewed sample: 200 rows (50 each for en, hi, gu, hinglish), randomly sampled with a fixed seed.
- Method: an AI pre-flagged suspicious rows, and the developer spot-checked the flags. The full 200 rows were not independently read line by line by a human.
- Rows judged bad: en 7/50, hi 1/50, gu 9/50, hinglish 8/50 (25/200 total).
- Bad rows were removed from the training data. The remaining rows of the dataset are unreviewed.
- Tier 2 data remains unverified by native speakers.

## Evaluation set

Tier 1 evaluation set: 100 rows (25 per language), written by Claude (an AI), independent of the Gemini-generated training data. It is NOT human-written. Rows are short and parallel across languages, so accuracy measured on it is an optimistic estimate.

Tier 2 evaluation set: 70 rows (10 per language for mr, bn, ta, te, kn, ml, pa), written by Claude (an AI), NOT verified by native speakers, verified=false. This is below the ~20 per language target in the task plan. Tier 2 metrics are experimental and must always be reported separately from Tier 1.

## Baseline evaluation

`python -m ml.src.evaluate` (or `make eval-baseline`) fits a character
2-to-5-gram TF-IDF vectorizer and Logistic Regression using only
`ml/data/processed/train.csv`. It evaluates against
`ml/data/eval_handwritten/eval.csv`, rejects exact complaint-text overlap
between the files, and writes the generated report to
`ml/reports/baseline_metrics.json`. The JSON report contains overall accuracy,
per-class precision/recall/F1 and support, macro-F1, a confusion matrix,
per-language metrics, and separate Tier 1 and Tier 2 metrics. Tier 1 results
are optimistic estimates because its AI-authored rows are short and parallel;
Tier 2 results are experimental and unverified by native speakers. No
evaluation rows are used for fitting.

The generated report used 4,367 training rows and 170 evaluation rows:

| Evaluation group | Accuracy | Macro-F1 |
|---|---:|---:|
| Overall | 0.894 | 0.892 |
| Tier 1 | 0.880 | 0.877 |
| Tier 2 (unverified) | 0.914 | 0.918 |

| Tier 1 language | Accuracy | Macro-F1 |
|---|---:|---:|
| English (`en`) | 0.840 | 0.814 |
| Gujarati (`gu`) | 0.840 | 0.825 |
| Hindi (`hi`) | 1.000 | 1.000 |
| Hinglish (`hinglish`) | 0.840 | 0.848 |

| Tier 2 language (unverified) | Accuracy | Macro-F1 |
|---|---:|---:|
| Bengali (`bn`) | 0.700 | 0.574 |
| Kannada (`kn`) | 0.900 | 0.867 |
| Malayalam (`ml`) | 1.000 | 1.000 |
| Marathi (`mr`) | 0.900 | 0.926 |
| Punjabi (`pa`) | 1.000 | 1.000 |
| Tamil (`ta`) | 1.000 | 1.000 |
| Telugu (`te`) | 0.900 | 0.926 |

These are real baseline results from the generated JSON report, not independent
human-verified performance estimates. The full per-class and confusion-matrix
results are in the report.

## MuRIL fine-tuning

The training implementation is `ml/src/train_muril.py`; the ordered Colab
workflow is in `ml/notebooks/train_colab.ipynb`. It fine-tunes
`google/muril-base-cased` for the nine department labels from the repository's
department seed list. Training reads `ml/data/processed/train.csv`, selects
the best checkpoint by validation macro-F1 on
`ml/data/processed/validation.csv`, and evaluates that checkpoint on the
separate `ml/data/eval_handwritten/eval.csv`. The evaluation set is never used
for training or checkpoint selection.

Defaults are `max_length=128`, `epochs=4`, `learning_rate=3e-5`,
`batch_size=32`, and `seed=42`; all are command-line options. Install training
dependencies with `python -m pip install -e ".[training]"`, then run
`python -m ml.src.train_muril`. The script saves model/tokenizer files and
`label_mapping.json` under `ml/artifacts/muril_model/`, and writes the
baseline-compatible report to `ml/artifacts/muril_metrics.json`. The mapping
is derived from the canonical department seed data and is saved alongside the
model for inference.

To publish the model and tokenizer, pass both `--push_to_hub` and
`--hub_model_id OWNER/REPOSITORY`; the script reads `HF_TOKEN` from the
environment and never logs it. The notebook reads the token from Colab or
Kaggle secrets. Training has not been run, no MuRIL metrics are available, and
no trained weights or model identifier are committed.

## Review status and limitations

- **Tier 1 (English, Hindi, Gujarati, Hinglish):** Generated examples are
  synthetic and LLM-drafted. The review log above records the AI pre-flagging
  and developer spot-check; the full sample was not independently read line by
  line by a human, and the remaining rows are unreviewed.
- **Tier 2 (Marathi, Bengali, Tamil, Telugu, Kannada, Malayalam, Punjabi):**
  Experimental, LLM-drafted, synthetic, and unverified by native speakers.
- The `verified` column is `false` for every generated row. It is not a
  substitute for the independent evaluation set described above, which must
  remain separate and must never be used for training.
- Prompt constraints and automated validation reduce common defects but do
  not establish factuality, native-speaker quality, or label correctness.
- The baseline metrics report is generated from the local training split and
  evaluation set; metrics are not reported by the dataset generator.
