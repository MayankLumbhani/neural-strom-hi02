# Model Card: Synthetic Complaint Dataset

## Dataset generation

`ml/src/generate_dataset.py` drafts multilingual municipal complaints with the
official Google Gen AI Python SDK. All examples are LLM-drafted and synthetic;
no citizen records or other real personal data are used. No generation run has
been performed for this change, and no dataset/model metrics are reported here.

### Generation prompt

Each request asks for 15 distinct complaints in strict JSON for one department
and one language. The language code, tier, and script are read from
`nlp/languages.py`; Hindi and Gujarati use their native scripts, Hinglish uses
romanized Hindi in Latin letters, and Tier 2 languages use their native
scripts. Prompts ask for varied polite, angry, brief, and detailed tones; varied
length and spoken style; occasional realistic typos; fictional concrete details
and duration; and about 25% of examples without a location. Locations may only
be fictional ward numbers, areas, invented streets, or invented landmarks.
Prompts forbid real people, real places, phone numbers, full street addresses,
unrelated code-mixing, and repeated or closely paraphrased phrasings within a
batch.

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
| `LLM_TIMEOUT_SECONDS` | `10` | API request timeout |

Set the required Gemini settings in `.env`, then run
`python -m ml.src.generate_dataset --check` to make one small request without
writing data. Use `make generate-dataset` for a full run, or
`python -m ml.src.generate_dataset --limit N` to process at most N batches.
Each run logs the configured model name and kept/dropped counts by language
and department. The API key is not logged.

API responses must be JSON arrays of strings. The generator strips whitespace,
enforces a 12-to-500 character length, checks that letters match the registry
script, rejects repeated adjacent words and phone-number-like digit runs, and
drops normalized exact and near duplicates. It retries rate-limit and server
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
