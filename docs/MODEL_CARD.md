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

## Training-label normalization

The processed `train.csv` and `validation.csv` labels were normalized with the
deterministic D-10 rule in `docs/DECISIONS.md`: HEALTH or SANITATION rows with
a drainage keyword and no disease keyword are relabelled DRAINAGE. Latin
keywords use case-insensitive word boundaries; Hindi and Gujarati keywords
use substring matching. The local run changed 113 training rows and 23
validation rows; the hand-authored evaluation CSV was not changed. The
committed baseline report predates this normalization and has not been
recomputed on the updated local split.

## MuRIL fine-tuned classifier

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
Kaggle secrets. The trained model is published as the optional MuRIL backend
`MayankLumbhani/hi02-muril-grievance`; set `CLASSIFIER_BACKEND=muril` and
`MODEL_NAME_OR_PATH` to select it. The default backend is the TF-IDF baseline.
The run report is tracked at
`ml/artifacts/muril_metrics.json`; it records the base model name used for
fine-tuning.

### Tier 1 results

| Language | Accuracy | Macro-F1 |
|---|---:|---:|
| Overall (Tier 1) | 0.89 | 0.8305583305583305 |
| English (`en`) | 0.84 | 0.7873015873015873 |
| Hindi (`hi`) | 0.92 | 0.8571428571428572 |
| Gujarati (`gu`) | 0.92 | 0.8571428571428572 |
| Hinglish (`hinglish`) | 0.88 | 0.8190476190476191 |
### Tier 2 results (unverified, experimental)
### Tier 2 results (unverified, experimental)

| Language | Accuracy | Macro-F1 |
|---|---:|---:|
| Overall (Tier 2, unverified) | 0.8857142857142857 | 0.8575835957414905 |
| Marathi (`mr`) | 0.8 | 0.7777777777777778 |
| Bengali (`bn`) | 0.9 | 0.8518518518518517 |
| Tamil (`ta`) | 0.9 | 0.8518518518518517 |
| Telugu (`te`) | 0.9 | 0.8518518518518517 |
| Kannada (`kn`) | 0.9 | 0.9259259259259258 |
| Malayalam (`ml`) | 0.9 | 0.8518518518518517 |
| Punjabi (`pa`) | 0.9 | 0.8518518518518517 |

### Tier 1 baseline comparison

The baseline values below are from the committed T-09 report, generated
before the D-10 training-label normalization; the MuRIL values are from its
second run on the normalized training data. Both reports use the same
evaluation set.

| Tier 1 metric | Baseline | MuRIL |
|---|---:|---:|
| Overall accuracy | 0.88 | 0.89 |
| Macro-F1 | 0.8767333793420751 | 0.8305583305583305 |

| Department | Baseline F1 | MuRIL F1 |
|---|---:|---:|
| WATER | 0.8695652173913043 | 1.0 |
| ROADS | 1.0 | 1.0 |
| SANITATION | 0.7826086956521738 | 0.7857142857142857 |
| ELECTRICITY | 0.9565217391304348 | 0.9090909090909091 |
| STREETLIGHT | 0.9600000000000001 | 0.923076923076923 |
| DRAINAGE | 0.8571428571428571 | 0.8571428571428571 |
| HEALTH | 0.5714285714285714 | 0.0 |
| TAX | 0.9600000000000001 | 1.0 |
| OTHER | 0.9333333333333333 | 1.0 |

### Training history

The first MuRIL run on unrelabelled data scored Tier 1 accuracy `0.83` and
DRAINAGE recall `0.053` on the full evaluation set because the training labels
for DRAINAGE, HEALTH, and SANITATION overlapped. D-10's rule-based relabelling
fixed this training-label overlap. The published model is the second run,
trained on the relabelled data.

### Known limitations

- HEALTH recall is `0.0` on the Tier 1 evaluation set (8 rows): 5 were
  predicted as SANITATION and 3 as DRAINAGE, so HEALTH complaints are likely
  to be misrouted.
- The Tier 1 evaluation set has only 100 AI-authored rows. Its rows are short
  and parallel, making accuracy an optimistic estimate; the approximately
  `0.01` accuracy gap between MuRIL (`0.89`) and the baseline (`0.88`) is not
  meaningful.
- Tier 2 results are experimental and rest on only 10 unverified rows per
  language.
- The baseline report predates D-10 label normalization, so the baseline and
  MuRIL training data are not directly equivalent.
- Generated examples are synthetic and LLM-drafted. The review log above
  records AI pre-flagging and developer spot-checks; the full sample was not
  independently read line by line by a human, and remaining rows are
  unreviewed.
- The `verified` column is `false` for every generated row. It is not a
  substitute for the independent evaluation set, which must remain separate
  and must never be used for training.
- Prompt constraints and automated validation reduce common defects but do
  not establish factuality, native-speaker quality, or label correctness.
- The baseline metrics report is generated from the local training split and
  evaluation set; metrics are not reported by the dataset generator.
