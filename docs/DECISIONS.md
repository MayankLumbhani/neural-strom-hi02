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
- **Decision:** Start with marker-word counts for each language (for example words that are common in one and rare in the other), falling back to Hindi on a tie or no signal. A detector library is added only if the marker words prove too weak, and then it needs its own entry here.
- **Alternatives:** a language-ID library from the start.
- **Consequences:** No extra dependency at first. Accuracy of this step is measured on the evaluation set and reported. It affects only the reply language, not the department classification.