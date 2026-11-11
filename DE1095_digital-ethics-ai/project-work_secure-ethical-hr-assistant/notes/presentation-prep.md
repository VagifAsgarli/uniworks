# Presentation prep: Atlase, 17 November 2026 (7 minutes, online)

What to have ready, what to say, what to remember, and the questions that are likely to come.
The deck is `presentation/DE1095_ProjectWork_Asgarli_251ADM047.pptx` (PDF of the same in the same
folder); the timed script is `presentation/speaker-notes.md`; everything the slides claim, with
sources, is in `notes/system-design.md`.

## 1. Before the day

- **Rehearse three times with a timer.** The script is 1,037 words, 7 minutes at a calm pace; the
  slides have planned start times (slide 2 at 0:20, 3 at 1:10, 4 at 2:10, 5 at 3:10, 6 at 3:50,
  7 at 4:40, 8 at 5:35, 9 at 6:25, 10 at 6:50). If you are behind at slide 7, shorten slides 8
  and 9 to their first sentences; slide 10 is 20 seconds and must be said.
- **Set-up on the call:** PowerPoint in Presenter View (notes on your screen, slides shared) or
  the PDF in full screen with the printed notes next to you; share the window, not the whole
  screen; camera on; a second device with the PDF open in case the laptop fails; phone timer.
- **Test the screen share once** in the meeting tool five minutes before your slot.
- Keep slide 11 (sources) for questions; do not present it.
- Have `notes/system-design.md` open in another window for a question you want to answer exactly
  (the OWASP table, the approval matrix, the metric targets).

## 2. The six things the task requires, and where they are

| Required by the task | Slide | What you say in one line |
|---|---|---|
| The system: what, who uses, who is affected, what can go wrong | 2 | Atlase screens applications for a fictional logistics company; 8 recruiters use it, 12,000 applicants a year are affected; six things can go wrong, the talk answers them |
| Lifecycle: one risk and its handling for five stages | 3 | data: no training on past hiring; training: no fine-tuning on applicants, pinned version; evaluation: counterfactual test; deployment: CV is data, no tools; monitoring: dashboard, 2 % re-label, circuit breaker |
| Security: 3 threats, attack types, preventive + detective, OWASP check | 4, 5 | injection (LLM01), leakage (LLM02/06/08), poisoning and supply chain (LLM04/03); seven of ten OWASP items apply |
| Governance: who approves what, incident plan | 6 | data steward + DPO; ML lead + CISO + AI board; HR director assigns trained recruiters; documentation; detect, contain, eradicate, recover (re-review every application), learn |
| Ethics and law: AI Act tier and requirements, data protection, a dilemma | 7, 8 | high-risk, Annex III 4(a); obligations from 2 Dec 2027 after the Omnibus, transparency since Aug 2026; GDPR Art. 22 and SCHUFA today; dilemma: automatic rejection, answer no, fast lane |
| Quality and limits: how to measure, two LLM limits | 9 | targets for extraction, recall, evidence faithfulness, fairness (counterfactual, adverse impact ≥ 0.8), override rate; hallucination and training-data bias |

## 3. Facts to have in your head

- **Name:** Atlase, Latvian for "selection". Company: Baltic Freight Group (fictional), 1,200
  employees in LV, LT, EE, 250 vacancies a year; the company builds and runs it, so it is both
  provider and deployer.
- **Model:** a general-purpose foundation model used through an API, hosted in the EU under a
  data-processing agreement, no training on our data, model version pinned. Retrieval of the job
  description and HR policy; no tools; output is a fixed JSON schema with a verbatim quote per claim.
- **AI Act:** Regulation (EU) 2024/1689. High-risk by Annex III point 4(a) (recruitment: filtering
  applications, evaluating candidates). Not prohibited (no emotion recognition at work, Art. 5).
  Provider obligations Art. 9–15: risk management, data governance, technical documentation (Annex
  IV), logging, transparency and instructions, human oversight (Art. 14), accuracy, robustness,
  cybersecurity; registration in the EU database (Art. 49). Deployer obligations Art. 26: use as
  instructed, competent and authorised overseers (Art. 26(2)), logs kept at least six months
  (26(6)), inform workers' representatives (26(7)), inform affected persons, explanation on
  request (Art. 86). AI literacy for staff (Art. 4).
- **Dates:** the AI Omnibus (Regulation (EU) 2026/1744, in force 27 July 2026) postponed the Annex
  III high-risk obligations to **2 December 2027**; the transparency obligations of Art. 50 apply
  since **2 August 2026**. (The week-2 slides still show the earlier date; say that you checked.)
- **GDPR:** Art. 22 no solely automated decision with legal or similarly significant effect;
  CJEU **SCHUFA, C-634/21, 7 Dec 2023**: a score that the human "draws strongly on" is itself the
  decision; Art. 35 DPIA mandatory; Art. 13/14 information to applicants; Art. 33/34 breach
  notification within 72 hours to the Data State Inspectorate; retention: applicant data deleted
  six months after the vacancy closes unless the candidate consents to a talent pool.
- **Latvian Labour Law (Darba likums) Sections 29 and 32:** prohibition of differential treatment in
  employment; the works council / employee representatives informed before use.
- **Cases:** Amazon 2018 (engine trained on ten years of mostly male CVs penalised "women's");
  EEOC v. iTutorGroup 2023 (USD 365,000, software auto-rejected women 55+ and men 60+); Mobley v.
  Workday (N.D. Cal., age-discrimination collective action conditionally certified 16 May 2025,
  continuing); Robodebt (Australia: automated debts, correction had to be done at scale); Zillow
  Offers 2021 (model drift nobody watched); Moffatt v. Air Canada 2024 (the company is liable for
  its chatbot's statements); Samsung 2023 (data leaked to a provider).
- **Numbers:** 12,000 applicants a year, 8 recruiters, a third of applicants fail a hard
  requirement; fast lane costs about 100 recruiter hours a year; 500-application labelled
  benchmark; 2 % monthly re-label; counterfactual consistency ≥ 99 %; adverse-impact ratio ≥ 0.8
  (the four-fifths rule); post-mortem within 10 working days.
- **OWASP Top 10 for LLM Applications 2025:** LLM01 prompt injection, LLM02 sensitive information
  disclosure, LLM03 supply chain, LLM04 data and model poisoning, LLM05 improper output handling,
  LLM06 excessive agency, LLM07 system prompt leakage, LLM08 vector and embedding weaknesses,
  LLM09 misinformation, LLM10 unbounded consumption. Applies: 1, 2, 3, 4, 5, 6, 8, 9 (seven to
  eight); low: 7 and 10.

## 4. Likely questions and answers

### The system

**Why recruitment?**  Because the AI Act lists it as high-risk, so every section of the task has
real content: the law, the oversight rules, the fairness tests. It is also the example the course
itself used for high-risk systems and for the OWASP walk-through.

**Which model would you actually use?**  A general-purpose model from a provider that hosts in the
EU and signs a data-processing agreement with no training on our data; the version is pinned and a
provider update is treated as a new release. I deliberately do not name a vendor on the slide
because the design does not depend on it; the controls are outside the model.

**Why no fine-tuning on your own applications?**  Three reasons: a fine-tuned model memorises
personal data and cannot forget it; training on past outcomes copies past bias (Amazon); and the
task of extraction with evidence is handled well by prompting with a schema and a few synthetic
examples.

**What does "the CV is data, not instructions" mean in practice?**  The document is normalised to
plain text, hidden content is dropped, the text goes to the model inside delimiters with a fixed
output schema, and the model has no tools, so even a successful injection can only change a
suggestion that a recruiter sees next to the evidence.

### Security

**How do you detect prompt injection, not just prevent it?**  A detector on the normalised text
flags instruction-like phrases and duplicated keyword blocks; the evidence check rejects any claim
whose quote cannot be found in the document; repeated flags from one applicant raise an alert.

**What is the difference between a preventive and a detective control?**  Preventive stops the
event (normaliser, no tools, access filtered before retrieval); detective finds it when it happens
(injection detector, access logs and anomaly alerts, canary re-evaluation). The task asks for one
of each per threat; slide 4 gives them.

**Why is model extraction low for you?**  The assistant is internal, rate-limited and
authenticated; nobody outside can query it at the volume extraction needs, and it carries no
secret of ours worth extracting; the model is the provider's.

**Who is the attacker in T3?**  An insider or a compromised supplier: a doctored HR-policy
document in the retrieval store, biased few-shot examples, a tampered prompt, or a silent provider
update. The control is governance sign-off for every change, however small, and the canary suite
that re-runs on every change.

### Governance

**Who is accountable if a good candidate is wrongly rejected?**  The company, through the HR
director as system owner; the recruiter took the decision with the evidence in front of them, so the
decision record shows what the assistant suggested, what the recruiter decided and why. The AI
board approved the release against written criteria; the logs make the chain answerable to an
auditor without the people who built the system.

**What is the AI governance board?**  HR director, ML lead, CISO, DPO, a legal representative;
it approves go-live, every change to prompts, data or model version, and the resumption after an
incident.

**What happens in an incident?**  Detect (alerts, the recruiters' report button, candidate
complaints), contain (kill switch; recruiters work manually), eradicate (find the faulty version
in the logs, fix or roll back, re-run the suites), recover (re-review every application processed
under the faulty version), learn (post-mortem in 10 working days, GDPR notification within 72
hours where personal data was affected, AI Act serious-incident report where applicable).

**What is meaningful oversight versus a rubber stamp?**  Oversight is meaningful when the person
has the competence, the authority, the time and the evidence to disagree, and sometimes does.
That is why the override needs a reason, there is no "accept all", a sample is double-checked,
and the override rate is a monitored metric: a rate near zero means nobody is looking.

### Ethics and law

**Is Atlase high-risk or not, given the Omnibus?**  It is high-risk by Annex III 4(a); the Omnibus
only moved the date the obligations apply, to 2 December 2027. I would build to them now anyway,
because the GDPR, the Labour Law and the transparency rules apply today, and because oversight,
logging and fairness testing are what make the system work at all.

**Does a ranking count as an automated decision under Art. 22?**  After SCHUFA, yes if the human
draws strongly on the score. That is why the recruiter sees criteria and quotes, not a single
number, and takes a real decision on each case; the design avoids being a "score the human
rubber-stamps".

**How do applicants know AI is used?**  They are informed at application time (GDPR Art. 13; AI
Act transparency and Art. 26), every rejection letter names the requirement that was not met, and
they can ask for an explanation (Art. 86) and contest the decision.

**Why no automatic rejection even for clear cases?**  Because high confidence is not certainty
(a licence in another language is where extraction fails), a wrong automatic rejection is invisible
and happens at scale (Robodebt), the law requires a human decision (GDPR Art. 22, AI Act Art. 14),
and in Kantian terms the applicant is a person, not a line to filter. The fast lane keeps the
speed: grouped cases with the quote, a recruiter confirms each in seconds, about 100 hours a year.

**What about the works council?**  Art. 26(7) of the AI Act and Latvian labour practice: employee
representatives are informed before the system is used at the workplace; it is on the governance
slide.

**Latvian, Russian and English applications?**  The benchmark is labelled per language and a
weaker result in Latvian or Russian blocks a release; the fairness test includes nationality.

### Quality and limits

**How do you measure fairness?**  Counterfactual consistency (same application with swapped name,
gender, age, nationality must give the same result, target ≥ 99 %) at every release, and the
adverse-impact ratio between groups on shortlist rates (≥ 0.8, the four-fifths rule) monthly, from
voluntary equality-monitoring data stored separately from the applications.

**Where does the ground truth come from?**  A benchmark of 500 applications labelled by three
recruiters; disagreements resolved by discussion; the benchmark is versioned and extended with
every incident.

**What are the two LLM limits and how do they shape the design?**  Hallucination: plausible text,
not facts, so every claim needs a verbatim quote that code can find and "unclear" is an allowed
answer. Bias in training data: identifiers removed before the call, counterfactual tests at every
release, adverse-impact monitoring in production. (Outdated knowledge is handled by retrieval of
the current job description and policy instead of relying on what the model remembers.)

**What would make you switch the system off?**  The circuit breaker: fairness or accuracy metrics
outside their tolerance band pause the assistant for new vacancies until the AI board has
reviewed; the recruiters can also stop it for a vacancy.

### About the work

**Did you use AI tools to prepare this?**  Answer honestly and briefly, in line with the course's
rules on AI use: what you used them for (drafting, formatting, checking sources) and what you did
yourself (the choice of system, the decisions, the verification of the legal facts, the rehearsal).
In a digital-ethics course this answer is itself part of the assessment.

**What is the one thing you want us to remember?**  A person decides every time, with evidence in
front of them; everything else in the design exists to make that decision a real one.

## 5. If something goes wrong on the day

- Screen share fails: send the PDF in the chat and present from the slide numbers.
- You run out of time: finish with slide 10's five decisions; they are the summary.
- A question you cannot answer: say what you would check (the system-design note has the
  sources) and offer to follow up; do not invent a legal citation.
