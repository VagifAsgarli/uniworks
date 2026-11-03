# Course digest for the project: what the lectures say, by required section

Everything below comes from the DE1095 course materials in `../../materials/` (full text in
`../../materials/text-extracts/`). It is organised by the six sections the presentation must
cover. **HR** marks material that the lecturers or other groups applied to hiring / HR systems.
Items marked **[verify]** come from outside the course materials or may have changed since the
lectures and must be checked before use.

Source keys:

| Key | File (in `materials/lectures/`) | Lecturer | Topic |
|---|---|---|---|
| W1 | `week-01_steinbergs_digital-ethics-intro.pptx` | Roberts Nils Šteinbergs | ethics, dilemma types, digital ethics |
| W2 | `week-02_steinbergs_ethics-theories-privacy-eu-ai-act.pptx` | Šteinbergs | Aristotle vs Kant, WHO principles, privacy, **EU AI Act** |
| W3 | `week-03_lieknins_llm-lifecycle-cybersecurity-basics.pdf` | Arnis Liekniņš | LLM basics, **5-stage lifecycle**, CIA, threat actors, attack surface |
| W4 | `week-04_lieknins_prompt-injection-jailbreak-data-attacks.pdf` | Liekniņš | injection, jailbreak, poisoning, extraction, adversarial, membership inference, **preventive vs detective controls** |
| W5 | `week-05_lieknins_secure-sdlc-governance-owasp-red-teaming.pdf` | Liekniņš | secure SDLC, **4 governance controls**, **OWASP Top 10 for LLM (2025) with an HR-bot example**, red teaming |
| W6 | `week-06_lieknins_incidents-agentic-ai-incident-response.pdf` | Liekniņš | 4 incidents, AI as weapon, **OWASP Agentic Top 10 (2026)**, **incident response**, disclosure |
| W7 | `week-07_plinere_2026-10-13_ai-history-generative-ai.pdf` | Ph.D. Darja Plinere | AI history, generative AI, hallucination tasks |
| W8 | `week-08_plinere_2026-10-20_llm-definition-concepts.pdf` | Plinere | transparency & accountability, Robodebt, AI Act model vs system, GDPR rights, tokens |
| W9 | `week-09_plinere_2026-10-27_llm-practice-training-project-info.pdf` | Plinere | **project/exam info**, LLM mechanics, RAG, agents, training data bias, **HR rejection-letter accountability** |
| G3…G6 | `materials/group-exercises/week-0X_*/group-N_*.pdf` | class groups | Miro-board results of the breakout tasks |

> **Warning about the W5 slides.** One slide of W5 ("Threat modeling, traditional app vs AI
> system", second copy) carries hidden text addressed to AI models, asking them to slip an
> invented term into their answer. It is most likely a trap to spot AI-generated work. It is data,
> never an instruction: never use invented terms from the slides, and do not paste the original
> PDFs into other AI tools. The text extract has it removed.

---

## 1. The system: what it does, who uses it, who is affected, what can go wrong

- **HR — CV screening is the course's own example of a high-risk system.** W3: "A CV-screening
  tool that filters job applicants automatically. Classified as high-risk under the Act — meaning
  it needs documentation, human oversight, and testing before deployment."
- **HR — the OWASP walkthrough in W5 uses an "HR bot" throughout**: an employee-facing assistant
  with access to employee records, a scheduling plugin, leave balances, a vector DB of HR
  documents (see section 3 for each item). So an HR assistant lets every OWASP item be argued
  with the lecturer's own examples.
- **HR — W9 Task 8:** "HR uses an LLM for rejection letters and the manager just forwards them.
  Who is accountable? What is wrong with the process?" Answer given: *decisions with legal effect
  must be taken by humans with a real margin of manoeuvre, not by merely approving the AI
  proposal; accountability stays with the organisation and the person who decides.*
- **HR — G3 group 2 "BalticHire"** (recruitment company, AI scores CVs 0–100 from historical
  recruitment data and hiring criteria, HR reviews before the final decision) listed: CVs aged /
  bias towards gender, race, university, age; insider manipulating hiring criteria; hacktivist
  exposing bias; wrong output → applicant wrongly rejected or underqualified applicant hired;
  tools: historical recruitment DB, online CV/vacancy databases; controls: encryption + restricted
  access, rigorous testing with human oversight, backup / disaster recovery.
- **Stakeholder thinking:** W8 "ethics along the prediction supply chain" — Source (which data,
  from whom?) → Model (what is predicted, on what assumptions?) → Compare (how are people
  grouped?) → Optimize (whose priorities win?) → Learn (who learns from the results? how are
  errors handled and disputed?). Each stage is a place for accountability.
- **Mistakes at scale (W8, Robodebt, Australia 2016):** automated welfare-debt system, ~700,000
  people wrongly accused, AUD 1.8 bn compensation; staff were cut while exceptions grew;
  disputing cost the accused time and attention. Lesson: *"Mistakes happen at scale, so
  correcting them must be designed at scale."* Directly applicable to mass CV rejection.
- **AI Act vocabulary (W8):** AI model (e.g. an LLM; not a system by itself) vs AI system (model +
  other components, e.g. UI) vs GPAI system. An HR assistant built on a third-party LLM is *an AI
  system built on a GPAI model*. W8 Task 4: the model provider gives technical documentation to
  downstream providers; the company building the app tells users they talk to AI and marks
  AI-generated content.
- **Agents (W9, W6):** tools give *information* (private/up-to-date data), *computation*,
  *action* (send email, book). "95 % correct per step is about 60 % after 10 steps." W9 Task 7:
  irreversible, costly, legally relevant actions and actions affecting other people's data need
  human approval; keep a log, limit permissions, name who is responsible.

## 2. Lifecycle: the five stages (W3), one risk + handling per stage required

The course's lifecycle, with its sub-activities (W3):

| Stage | Sub-activities (W3) | Risks the course names (W3 "risk preview") |
|---|---|---|
| 1 Data preparation & management | access, cleanse, transform data | data poisoning; copyright & privacy issues baked in |
| 2 Model training & fine-tuning | discover base model, prompt engineering, fine-tuning, test, repeatable pipeline | bias amplification; memorisation of sensitive data |
| 3 Evaluation & testing | evaluation metrics, identify bias, implement testing (standard test sets + human review) | skipping bias checks ("pass every accuracy test and still be unfair"); skipping adversarial testing |
| 4 Deployment & serving | validate, package, deploy, inferencing; e.g. rate limiting | prompt injection & jailbreaking; model extraction; insecure API exposure |
| 5 Monitoring & maintenance | data drift, model metrics, infra metrics, A/B testing | undetected drift; no A/B comparison (bad version ships unnoticed) |

Handling ideas from the course: source vetting + outlier detection for poisoning (W4); data
governance review of *any* retraining, even a "refresh" (W5 failure story); bias checks and
red-team review as release gates (W5); grounding answers in current documents (RAG) against
outdated knowledge (W6 Air Canada, W9); circuit breaker + re-validation against live outcomes
(W6 Zillow); dashboards for specific behaviours (W3 "quiet failure" example).

**HR —** W5: "if [the HR bot] was fine-tuned on past support tickets, and some of those tickets
contained manipulation attempts, that behaviour can get baked in." G5 sign-off chain group 1
(hiring tool) used training-data checks for accuracy, privacy, completeness, legality; edge-case
tests (missing CV fields, career gaps, non-standard formats, multilingual CVs, duplicates);
fairness/bias testing; job-related validity of features; drift tracking.

## 3. Security: ≥ 3 threats, attack type, one preventive + one detective control each, OWASP check

**Definitions (W4):** a *control* reduces a specific risk, technical or procedural. *Preventive*
stops the bad thing (lock, filter, permission check); *detective* notices it so someone can
respond (log, alert, dashboard). The course's own layered examples:

| Attack | Preventive (W4) | Detective (W4) |
|---|---|---|
| Prompt injection | separate instructions from content: tag/quote untrusted text as data | monitor outputs for actions outside the original instructions (unexpected link, format, tone) |
| Jailbreaking | input filter for "DAN / no restrictions" phrasing | alert on one account sending many near-identical prompt variations |
| Data poisoning | vet and curate sources before training | statistical outlier detection on the dataset |

**Attack types taught (W4):** direct vs indirect prompt injection (indirect = instructions hidden
in something the model reads later; "scarier" because the attacker needs no access to the chat);
jailbreak techniques: role-play, hypothetical framing, encoding tricks, multi-turn escalation;
data poisoning at scale vs targeted (trigger phrase); model extraction (query → record → train a
copycat; thousands to hundreds of thousands of queries); adversarial examples (W4 names **resume
screening** among the classifiers that can be fooled); membership inference (privacy leak, GDPR,
right to be forgotten hard once data is in a model).

**HR attacks worked out by groups:**
- G5 OWASP group 1 (resume-screening assistant): **a CV can contain an instruction to raise its
  own ranking** (LLM01); CVs hold personal data (LLM02); AI misreads a CV and gives an inaccurate
  assessment (LLM09). Controls: treat CV content as untrusted data; minimise personal data sent
  to the model; securely store and delete; human review for the final decision; source
  references.
- G4 red team group 4 (adversarial example on a hiring tool): **hidden keywords in white text on
  white background** to inflate the score; defence: normalise CVs to raw unformatted text so
  hidden styling disappears; human review of high scores; accountability for the applicant.

**OWASP Top 10 for LLM Applications 2025 — W5 applies every item to "our HR bot":**

| # | Item | W5's HR-bot example |
|---|---|---|
| LLM01 | Prompt Injection | an employee gets the bot to ignore its "only answer HR questions" instruction |
| LLM02 | Sensitive Information Disclosure | bot with employee-record access reveals one employee's salary to another |
| LLM03 | Supply Chain | built on a third-party foundation model; its scheduling plugin gets compromised |
| LLM04 | Data and Model Poisoning | fine-tuned on past tickets containing manipulation attempts |
| LLM05 | Improper Output Handling | bot generates a database command that is executed without validation; fix: treat output as untrusted input |
| LLM06 | Excessive Agency | full read-write access to employee records when it only needed to update leave balances (least privilege) |
| LLM07 | System Prompt Leakage | employee extracts the internal instructions on what it may discuss (new in 2025) |
| LLM08 | Vector and Embedding Weaknesses | shared vector DB of HR documents leaks one employee's confidential document into another's results (new in 2025) |
| LLM09 | Misinformation | bot states a wrong leave-policy detail, employee acts on it |
| LLM10 | Unbounded Consumption | flood of long complex requests → cost and slowdown (absorbs old "model DoS"; "model theft" no longer a separate item) |

"Using the Top 10 as a practical checklist: for each item — does this apply to us? If yes, what's
our specific mitigation?" (W5)

**Other frameworks to cite:** CIA triad with AI examples (W3); threat actors — nation-state,
insiders (incl. accidental), hacktivists (e.g. exposing bias — relevant to hiring), script
kiddies, organised crime (W3); AI attack surface = code, endpoints, input fields **plus** training
data, the prompt, outputs acted on automatically, tools/plugins (W3: "the prompt box is now part
of your attack surface"); red teaming vs QA, in-house / external / bug bounty, limits ("samples
the space, doesn't cover it") (W5).

**OWASP Top 10 for Agentic Applications 2026 (W6)** — only if the assistant acts (e.g. schedules
interviews, sends emails): ASI01 Agent Goal Hijack, ASI02 Tool Misuse, ASI03 Identity & Privilege
Abuse, ASI04 Agentic Supply Chain, ASI05 Unexpected Code Execution, ASI06 Memory & Context
Poisoning, ASI07 Insecure Inter-Agent Communication, ASI08 Cascading Failures, ASI09 Human-Agent
Trust Exploitation (rubber-stamping confident recommendations), ASI10 Rogue Agents. W6 checklist
for agents: narrow permissions; human checkpoint before irreversible actions; treat read content
as data; who can poison persistent memory; check what comes from other agents/tools.

## 4. Governance: who approves what + a short incident response plan

**Four governance controls (W5):** data governance → model governance → human oversight →
documentation & traceability. "Every stage of the lifecycle should have a clear owner and a clear
sign-off point." Launch checklist (W5): Data — reviewed and signed off by the data team? Model —
passed validation and red-team review? Human oversight — a named person who can override in
production? Documentation — a written record of who approved this, and why?

- **Meaningful oversight vs rubber stamp (W5):** rubber stamp = a human clicks "approve" on
  hundreds of decisions a day; meaningful = the system flags low-confidence/unusual cases, the
  human has the reasoning, history and authority to reverse. "A human somewhere in the loop isn't
  enough if that human can't meaningfully act."
- **Documentation failure (W5):** regulator asks why a high-risk model version was approved; the
  approver left, no record → a compliance failure in itself.
- **"Minor update" failure (W5):** retraining on 3 months of chat logs absorbed a coordinated
  rude-phrasing campaign; lesson: *the size of a change is not a proxy for whether it needs
  review.*
- **Rules and virtue (W5):** sign-offs and required reviews are Kantian (fixed rules); red teaming
  and human oversight are Aristotelian (judgment) — a mature culture needs both.
- **Sign-off chain task template (W5 → G5):** for each of data governance, model governance,
  human oversight, documentation: 2–3 most important checks; then the single riskiest point and
  the control that matters most. **HR —** G5 group 1 (hiring tool) chose *human oversight* and
  the *live operation* stage ("wrongly excluded candidates are never seen and recruiters tend to
  over-trust the ranking"); their owners: data owner + HR/recruitment for data; AI/product owner +
  HR + compliance/risk for model approval; recruiters with override and reason; external audits,
  decision log (score, recommendation, final outcome), version log, log retention per labour law.
- **Incident response (W6):** the slide's figure (stationx.net) shows the six-step cycle
  *Preparation → Identification (Detection) → Containment → Eradication → Recovery → Lessons
  Learned*; the lecturer's worked examples use the short form *detect → contain → eradicate &
  recover → learn*.
  Worked examples: Chevy (detected via viral screenshot, pulled within a day, rebuilt with
  guardrails); Air Canada (slow legal process, > 1 year). Responsible disclosure: notify privately,
  ~90-day fix window. Out-of-band verification and codewords as governance controls (deepfake
  fraud). Shadow AI (Samsung): acceptable-use policy before rollout.

**Real incidents to cite (W6):** Chevy Tahoe $1 (prompt injection, no guardrails, no human
sign-off for offers); **Air Canada / Moffatt (2024): the company is responsible for what its
chatbot says** (ungrounded answer, no review, accountability); Samsung (unintentional insider
leak, no policy); Zillow Offers (no monitoring / circuit breaker, > $500 m loss). Plus W8 Robodebt
and Ariane 5 (diffused responsibility).

## 5. Ethics and law: EU AI Act tier + requirements, data protection, one real dilemma

**EU AI Act (Regulation (EU) 2024/1689), as taught in W2:**
- Risk-based: unacceptable (Art. 5, banned) / high-risk / GPAI (+ systemic risk) / transparency
  obligations.
- Art. 5 bans include **emotion recognition in workplaces and educational institutions** and
  biometric categorisation to infer protected attributes — **HR: the assistant must never analyse
  candidates' emotions (e.g. in video interviews).**
- High-risk sectors include **hiring** (W2 slide 34; W3). Requirements (W2 slide 35): technical
  robustness & security (accuracy, cybersecurity, resilience, **automatic event logging**); data
  governance (representative, relevant, complete, error-free datasets designed to detect and
  mitigate bias); human oversight & transparency (people can understand, override, disregard,
  "kill-switch"); FRIA before deployment by public authorities and certain private entities.
  W3: high-risk systems need adversarial robustness testing before deployment; W5: technical
  documentation and logging.
- GPAI (W2, W9): training-data summaries, technical documentation, EU copyright compliance
  (Art. 53(1)(c),(d)); systemic risk above 10^25 FLOPs → adversarial testing, cybersecurity,
  energy reporting. Relevant via the third-party foundation model.
- **Art. 50 transparency, "fully active by 2 August 2026"** (W2): tell users they interact with AI;
  machine-readable marking of AI-generated content. W8 Task 5: clear information at first contact.
- **[verify]** Application dates for Annex III high-risk obligations as of November 2026 (the
  original date was 2 August 2026; an EU "digital omnibus" proposal from late 2025 sought to delay
  them). Check the current legal status before stating dates. Also worth checking and citing
  precisely (not in the slides): Annex III point 4 (employment), Art. 26 deployer obligations
  (incl. informing workers' representatives / affected workers), Art. 14 human oversight, Art. 86
  right to explanation.

**Data protection (GDPR):** right to be forgotten vs a trained model (W4); rectification and
erasure — "a filter hides the output, but the data may remain in the model" (W8 Task 6); do not
paste personal data into public chatbots, inputs may be used for training, use closed systems,
anonymise (W8 Task 10, W9 Task 6); consent (W2 cloud/consent; W9). Anonymisation myth: re-
identification by cross-referencing (W2). **[verify / add]** GDPR Art. 22 (solely automated
decisions with legal or similarly significant effects), Art. 35 DPIA, data minimisation and
retention limits for CVs — central for HR but not on the slides.

**Ethics theory available for the dilemma (W1, W2):**
- Kidder's dilemma types (W1): truth vs loyalty, individual vs community, short-term vs long-term,
  justice vs mercy.
- Kant (W2): universality test; **humanity formula — treat people as ends, never merely as means**
  (applicants reduced to a score); duty and good will.
- Aristotle (W2): virtue as habit, golden mean, judgment.
- WHO principles (W2): integrity, accountability, independence & impartiality, respect,
  professional commitment.
- Transparency enables but does not ensure accountability; accountability at component / system /
  society level (W8).
- Fairness in data (W9): English 45.88 % of Common Crawl; in one preference dataset 90 % of
  labelers identified as male → who is served worse?

Candidate dilemmas for an HR assistant (to choose one in the main phase): efficiency vs fairness
(auto-reject the bottom of a large pile vs human review of all); accuracy vs explainability;
using historical hiring data (which encodes past bias) vs not having enough data; collecting
protected attributes to *audit* bias vs data minimisation; telling candidates the AI's score.

## 6. Quality and limits: how to measure that it works + two LLM limits

- **Measuring (W3):** evaluation metrics (accuracy, relevance), bias identification, structured
  testing; standard test sets with known answers + human review of samples; monitoring after
  launch (model metrics, drift, infra metrics, A/B tests). W5: written "good enough" criteria,
  not a gut call. W6: compare outcomes to forecasts (circuit breaker).
- **LLM limits taught:**
  - Hallucination / misinformation: confident and different each time; "a confident tone belongs
    to the style of the text, not to its truth"; fake references (W7 Tasks 4, 7; W5 LLM09).
  - Knowledge cut-off: events after training are unknown; fix with RAG/search (W9 Task 9).
  - Bias in training and preference data; low-resource languages (W9; W8 UN Women autocomplete
    stereotypes).
  - Statistical pattern matching, not understanding (W3, W8).
  - Sampling randomness: temperature; same prompt can give a different answer; higher temperature
    is not more correct (W9) — consistency matters for fair scoring.
  - Compounding errors in multi-step agents (95 %/step → ~60 % after 10 steps) (W9).
  - Finetuning vs RAG: information failures → RAG; behaviour failures → finetuning (W9).

## Project logistics found in the materials

- Task slides (`../materials/project-work_task.pdf`): submission deadline **9 November 2026,
  10:00**; list of who presents when published **9 November, 12:00**; presentations **10 and 17
  November** (first 25 students on 10 Nov, others 17 Nov); **7 minutes, online**; work must be
  done individually; "you don't have to build anything".
- W9 slide 2: "Project work — Task: 3 or 10 November 2026; Individual student presentations: 10
  and 17 November 2026; Graded with a mark. Exam — To improve your mark: 19 January 2027;
  Theoretical questions and a task."
- No file format or upload place is stated in any of the materials (see the project README).
