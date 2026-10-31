# Model Card: Synthetic Complaint Dataset

## Dataset generation

The current dataset is produced by `ml/src/generate_dataset.py`. It uses
deterministic, hand-authored synthetic complaint phrases and transformations;
it does not call an LLM or use external data.

### Generation brief

Write a short fictional municipal complaint for exactly one of the nine
department labels in the supplied language. Keep it synthetic and free of
personal data. Preserve enough department-specific meaning to support that
label. Create controlled variants with a typo, informal request, code-mixing,
missing location, or uncertainty. Do not treat generated text as reviewed
ground truth.

This brief documents the content constraints used to author the phrase bank;
the script itself applies repeatable transformations rather than prompting a
model.

### Reproduction settings

Run `make generate-dataset`, or invoke
`python -m ml.src.generate_dataset --help` for overrides. Defaults:

| Setting | Default |
|---|---:|
| Random seed | `20261031` |
| Validation fraction, stratified by language and department | `0.2` |
| Tier 1 samples per language and department | `50` |
| Tier 2 samples per language and department | `10` |

The nine department labels are read from the backend seed definitions, and the
eleven language codes and tiers come from `nlp/languages.py`. Each class and
language stratum is split independently. CSV outputs are written to
`ml/data/processed/train.csv` and `ml/data/processed/validation.csv` with
`text`, `label`, `language`, `tier`, `variation`, and `verified` columns.
At the defaults, generation produces 1,944 training and 486 validation rows.
Duplicate complaint text is kept out of the other split. Generated CSVs are
ignored by Git; do not commit generated datasets.

## Review status and limitations

- **Tier 1 (English, Hindi, Gujarati, Hinglish):** Generated phrase bank is
  synthetic and has not yet been manually reviewed. Before treating this
  dataset as ready for training, a human must review at least 50 generated rows
  per Tier 1 language and record the review outcome here.
- **Tier 2 (Marathi, Bengali, Tamil, Telugu, Kannada, Malayalam, Punjabi):**
  Experimental and unverified. The phrase bank and variation text have not
  been reviewed by native speakers. Tier 2 generated content is not verified.
- The `verified` column is `false` for every generated row. It is not a
  substitute for the independent, hand-written evaluation set, which must
  remain separate and must never be used for training.
- Typo, slang, code-mixed, missing-location, and ambiguous variants are
  controlled synthetic transformations, not a measure of real-world language
  distribution or user behavior.
- No model metrics are reported here; none have been measured by this generator.
