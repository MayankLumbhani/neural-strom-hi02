# Decisions

Short log of technology and design choices. Newest at the bottom. Format: context, decision, alternatives, consequences.

---

## D-01 Classifier: fine-tuned MuRIL

- **Context:** Complaints arrive in several Indian languages, including romanized Hindi. We need a measurable classifier that is cheap at inference.
- **Decision:** Fine-tune `google/muril-base-cased` for 9 department classes, behind a `Classifier` interface.
- **Alternatives:** zero-shot LLM only, IndicBERT.
- **Consequences:** Gives real accuracy and F1 numbers and runs on CPU. Needs training data and a Colab or Kaggle GPU run. The baseline (TF-IDF plus Logistic Regression) is kept for comparison.

## D-02 Fixed replies come from templates

- **Context:** Confirmations, status messages and errors must be reliable and reviewable.
- **Decision:** All fixed user-facing messages come from per-language template files. An LLM is never used to write them.
- **Alternatives:** LLM-generated replies.
- **Consequences:** Deterministic, free and safe. Every new language needs a template file.

## D-03 Background work: APScheduler in the API process

- **Context:** Tickets must escalate automatically, and we want minimal infrastructure.
- **Decision:** Run the escalation job with APScheduler inside the API process, written as an idempotent update.
- **Alternatives:** Celery plus Redis.
- **Consequences:** Far less infrastructure. Safe with several replicas because the update is idempotent.

## D-04 Database: PostgreSQL (Neon)

- **Context:** Free hosts wipe local disks, and escalation needs safe concurrent updates.
- **Decision:** PostgreSQL on Neon, with conversation state stored in the database so the API stays stateless.
- **Alternatives:** SQLite.
- **Consequences:** Persistent and concurrent. Needs a connection string secret.

## D-05 Hosting

- **Context:** The model needs more RAM than small free instances give.
- **Decision:** Backend and model on Hugging Face Spaces (Docker), frontend on Vercel.
- **Alternatives:** Render free tier.
- **Consequences:** More RAM. The Space sleeps when idle, so wake it before judging and show a waking-up message in the UI.

## D-06 No orchestration framework

- **Decision:** Plain services instead of Rasa or LangChain.
- **Consequences:** Simpler, easier for AI IDEs to keep clean, easier to test.

## D-07 Tiered language support behind one registry

- **Context:** Language is the core problem, so supporting only English, Hindi and Gujarati is too narrow. But the project is solo, and the author can only verify some languages, so claiming equal quality everywhere would be dishonest.
- **Decision:** Support languages in two tiers, defined in one registry (`nlp/languages.py`).
  - Tier 1, verified: English, Hindi, Gujarati, Hinglish. Full dataset, hand-written evaluation set, real metrics.
  - Tier 2, experimental: Marathi, Bengali, Tamil, Telugu, Kannada, Malayalam, Punjabi. Machine-translated templates, smaller LLM-drafted data, small evaluation sets not checked by native speakers.
  - Not supported now: Urdu and other right-to-left scripts, Odia, Assamese, romanized text in any language except Hindi.
- **Alternatives:** only three or four languages; all languages claimed as equal.
- **Consequences:**
  - Results are reported per language with the tier shown, and Tier 2 is always labelled unverified.
  - Adding a language is a registry entry, a template file, tests and docs, with no business logic changes.
  - Tier 2 can be disabled in the registry if time runs short.
  - UI strings are translated for Tier 1 only. The chat works in every registry language.
  - Before enabling a Tier 2 language, confirm that the base model covers it.

## D-08 Hindi vs Marathi detection

- **Context:** Both use Devanagari, so the Unicode block alone cannot tell them apart.
- **Decision:** Count whole-word markers from the central language registry. Hindi markers include `है`, `हैं`, `नहीं`, `मुझे`, `मेरे`, `रहा` and `रही`; Marathi markers include `आहे`, `नाही`, `मला`, `माझा`, `माझ्या`, `मध्ये` and `करा`. Fall back to Hindi on a tie or no signal. For Latin text, choose Hinglish when its registry markers (such as `nahi`, `paani`, `mere`, `hai` and `raha`) outscore English; otherwise choose English.
- **Alternatives:** a language-ID library from the start.
- **Consequences:** No extra dependency. Unsupported or ambiguous scripts return English and Hindi fallback reply languages. Detection affects only reply language, not department classification; results must be measured on the evaluation set before making quality claims.

## D-09 Gemini SDK for synthetic dataset drafting

- **Context:** The phrase-bank generator produces repetitive, uneven multilingual training examples, while generated data must remain synthetic and reproducible enough to resume interrupted runs.
- **Decision:** Use the official Google Gen AI Python SDK for offline dataset drafting. Read the API key and required model name from pydantic-settings; do not provide a model default. Cache raw responses by model, language, department, and batch so interrupted runs can resume.
- **Alternatives:** Continue maintaining hand-authored phrase banks or use another model provider.
- **Consequences:** Generation requires configured Gemini credentials and incurs API usage. LLM output is untrusted, so strict JSON, script, length, repetition, phone-number, and duplicate checks run before output; generated text is synthetic and unreviewed until human review.

## D-10 Deterministic drainage-label normalization

- **Context:** Generated complaints containing drainage issues were sometimes assigned to HEALTH or SANITATION, overlapping the DRAINAGE class and reducing classifier recall.
- **Decision:** In the processed training and validation splits, relabel a row to DRAINAGE only when its original label is HEALTH or SANITATION, its text contains a drainage keyword, and its text contains no disease keyword. Latin keywords match case-insensitively as whole words; Hindi and Gujarati keywords match as case-insensitive substrings. No other original label changes.
  - Latin drainage: `drain`, `drains`, `drainage`, `sewer`, `sewers`, `sewage`, `manhole`, `manholes`, `gutter`, `gutters`, `nala`, `naala`, `nalla`, `naale`, `naali`, `nali`, `nalli`.
  - Hindi drainage: `नाला`, `नाले`, `नाली`, `सीवर`, `ड्रेनेज`, `मैनहोल`, `गटर`.
  - Gujarati drainage: `ગટર`, `નાળું`, `નાળા`, `ગરનાળ`, `ડ્રેનેજ`, `મેનહોલ`.
  - Latin disease: `mosquito`, `mosquitoes`, `malaria`, `dengue`, `disease`, `diseases`, `infection`, `infectious`, `sick`, `ill`, `illness`, `bimar`, `bimari`, `machhar`, `fogging`, `epidemic`.
  - Hindi disease: `मच्छर`, `मलेरिया`, `डेंगू`, `बीमार`, `बीमारी`, `संक्रामक`, `संक्रमण`.
  - Gujarati disease: `મચ્છર`, `મેલેરિયા`, `ડેંગ્યુ`, `બીમાર`, `બીમારી`, `રોગ`, `રોગચાળો`.
- **Alternatives:** Manually relabel rows, retrain without correcting labels, or use a probabilistic classifier.
- **Consequences:** `ml/src/relabel_drainage.py` applies the rule deterministically and idempotently, preserves timestamped pre-change backups, and writes a local audit CSV. The rule only normalizes existing synthetic training/validation labels; it does not alter evaluation rows or predict labels for other departments.

## D-11 Demo account hashing and seed data

- **Context:** The database needs repeatable synthetic departments and demo officer/admin accounts for local development.
- **Decision:** Seed the nine departments with initial synthetic SLA hours, require demo usernames and passwords from environment variables, and hash passwords with bcrypt (12 rounds; 12 to 72 UTF-8 bytes). Re-running the seed updates seeded department/account fields while retaining hashes when passwords are unchanged.
- **Alternatives:** Store passwords directly, choose default demo passwords, or use Argon2.
- **Consequences:** Demo credentials must be configured before seeding, and bcrypt is an explicit backend dependency. The seeded SLA values are illustrative and are not legal or service guarantees.

## D-12 Localized template format

- **Context:** All supported languages need the same fixed-message keys, with Tier 2 files visibly labelled as machine-translated.
- **Decision:** Store template data in TOML files, load it with Python 3.11's built-in `tomllib`, and validate it with a typed Pydantic schema.
- **Alternatives:** JSON (no standard comment syntax for the Tier 2 warning) or YAML (would add a dependency).
- **Consequences:** No extra parsing dependency; all files are validated consistently, and Tier 2 warning comments remain alongside their translations.

## D-13 Synthetic training corpus generation

- **Context:** The baseline and MuRIL pipelines need multilingual, labelled training examples, but no real citizen data may be used.
- **Decision:** Draft examples with Gemini according to department and registry-language metadata. Use a configured seed for stratified train/validation splits, record `source=llm`, and keep generated CSVs and raw response caches out of Git.
- **Alternatives:** External citizen data or deterministic phrase banks.
- **Consequences:** The corpus is LLM-drafted, synthetic, unreviewed, and not a quality claim. Human review of at least 50 Tier 1 examples per language remains required; Tier 2 remains unverified.

## D-14 Default classifier backend

- **Context:** Tier 1 overall accuracy is comparable for MuRIL (0.89) and the baseline (0.880); a gap of this size is not meaningful on 100 AI-authored rows. The baseline has substantially better HEALTH F1 (0.57 versus 0.0) and is faster and lighter for the free hosting tier.
- **Decision:** Use the TF-IDF baseline as the default classifier backend. Keep the fine-tuned MuRIL model (`MayankLumbhani/hi02-muril-grievance`) as an optional backend selected through the existing `CLASSIFIER_BACKEND` environment variable.
- **Alternatives:** Make the published MuRIL model the default, or select a backend without configuration.
- **Consequences:** `CLASSIFIER_BACKEND` defaults to `baseline`; `muril` is the optional model runtime, while `fake` is test-only. ONNX inference remains future work. A later MuRIL retrain may prompt a review of this decision.

## D-15 Process-local public rate limits

- **Context:** Public chat and ticket-status endpoints need configurable per-IP request limits, while the hackathon deployment targets a single lightweight API instance.
- **Decision:** Enforce sliding-window limits in process memory using `RATE_LIMIT_CHAT` and `RATE_LIMIT_STATUS`; identify callers by the direct ASGI client address and do not trust unconfigured forwarded-IP headers.
- **Alternatives:** Shared database counters or a distributed cache, which require persistent/shared rate-limit infrastructure.
- **Consequences:** Each worker or replica maintains an independent quota, so aggregate enforcement is not distributed. Move to a shared store before relying on these limits across multiple replicas. Stale per-IP windows are periodically removed; no raw request content or address is logged.

## D-16 Train the baseline during the image build and load the artifact

- **Context:** The default baseline classifier originally fitted TF-IDF plus Logistic Regression at startup from `ml/data/processed/train.csv`. The processed CSV pattern was Git-ignored and the whole `ml` tree was Docker-ignored, so production images could not find the file and logged `classifier.initialization.failed backend=baseline reason=Baseline training CSV not found`. Fitting on every start also adds startup CPU and latency on a 512 MB free-tier instance.
- **Decision:** Commit only the synthetic `ml/data/processed/train.csv` (about 1 MB) and copy it into the image. During `docker build`, `python -m grievance.nlp.export_baseline` fits the pipeline once and writes `ml/artifacts/baseline.joblib` inside the image. At runtime `BaselineClassifier` loads that artifact; it fits from the CSV only when the artifact is absent, which covers local development and tests. The generated artifact is Git-ignored and never committed, and `.dockerignore` excludes any host copy so the image uses only the build-time output. Uvicorn runs a single worker.
- **Alternatives:** Fit at every startup (previous behavior, higher startup CPU and latency), commit a serialized joblib artifact (adds a binary to Git that can drift from the CSV), or download a model at runtime (adds a network dependency).
- **Consequences:** Production images start with `classifier.baseline.loaded source=artifact` and do not import PyTorch, Transformers or SentencePiece on the baseline path. Under a 512 MB container limit the API peaked at 284,132 kB VmHWM after English, Hindi and Gujarati chat flows (223.4 MiB in `docker stats`) and was not OOM-killed. Training data and hyperparameters are unchanged, so the committed baseline metrics still apply; a unit test asserts the loaded artifact predicts exactly like a freshly fitted model. Regenerating the dataset requires rebuilding the image so the artifact matches the committed CSV.