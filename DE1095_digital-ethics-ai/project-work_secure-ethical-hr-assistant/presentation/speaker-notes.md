# Speaker notes: Atlase (7-minute online presentation)

Timing marks [m:ss] are the planned start of each slide; about 1,000 words in total, i.e. 7 minutes at a calm pace. The same notes are inside the PPTX (View > Notes Page).

## Slide 1: Atlase

[0:00] Good afternoon. My system is Atlase, Latvian for "selection": an AI assistant that helps the recruiters of a fictional logistics company screen job applications. I chose recruitment because the AI Act makes it high-risk, so security, governance, ethics and law all have real teeth. Seven minutes: the system, its lifecycle, three threats, governance, the law, one dilemma, and quality.

*(60 words)*

## Slide 2: Atlase: what it does, who uses it, who is affected

[0:20] Atlase reads an application, extracts a structured profile, checks the vacancy's must-have requirements and suggests a shortlist order, always with a verbatim quote from the document as evidence. Three choices define it. It never rejects anyone: a recruiter decides every case. It sees only plain text with hidden content removed and has no tools, so its output is a suggestion, never an action. And it never learns from past hiring decisions, which is how Amazon's engine learned to penalise the word "women's". Users: eight recruiters and the hiring managers. Affected: twelve thousand applicants a year, including groups a language model may treat worse. On the right, what can go wrong: unfair ranking, invented facts, manipulation through the CV, leakage, rubber-stamp decisions, unlawful automated rejection. The rest of the talk answers these.

*(132 words)*

## Slide 3: Lifecycle: one risk and one answer for each of the five stages

[1:10] Five lifecycle stages, one risk and one answer each. Data: historical bias baked in, so no training on who was hired before; only job descriptions and a small anonymised example set, identifiers stripped. Training: memorised personal data and silent provider updates, so no fine-tuning on real applicants, and a pinned model version; a new version is a new release. Evaluation: a model can pass every accuracy test and still be unfair, so the release gate includes a counterfactual test: the same application with a swapped name, gender or age must get the same result. Deployment: injection and over-trust, so the CV is data, the model has no tools, and the interface demands a reason to override. Monitoring: undetected drift, so a monthly dashboard, a re-labelled sample, and a circuit breaker that pauses the assistant, the Zillow lesson.

*(138 words)*

## Slide 4: Security: three threats, one preventive and one detective control each

[2:10] Three threats, with the two kinds of control from week four. T1: an applicant hides instructions in white text in the CV: indirect prompt injection, OWASP item one. Preventive: documents are normalised to plain text and hidden text dropped, the CV is passed as data with a fixed output format, and the model has no tools, so an injection can only change a suggestion a human reads. Detective: an injection detector flags the application and an evidence check rejects claims without a real quote. T2: candidate data out of scope: an insider asking about another vacancy, or data reaching the provider. Preventive: access filtered before retrieval, identifiers removed before the API call, an EU-hosted model under a data-processing agreement. Detective: every query logged, anomaly alerts, output filtering. T3: poisoning and supply chain: someone changes the examples, a document or the model. Preventive: governance sign-off for every change, even a small refresh. Detective: the whole test suite re-runs on every change as a canary.

*(164 words)*

## Slide 5: OWASP Top 10 for LLM Applications (2025): what applies to Atlase

[3:10] Against the OWASP Top 10 for LLM applications, used the way the lecture used it: does it apply, and what is our mitigation. Seven of ten apply directly; the three threats cover items one, two, three, four and eight. Improper output handling: the output is validated JSON that is only displayed, never executed or sent. Excessive agency: no tools, read-only scope, least privilege. Prompt leakage and unbounded consumption are low: no secrets in the prompt, and the system is internal and rate-limited.

*(83 words)*

## Slide 6: Governance: who approves what, and the incident response plan

[3:50] Governance follows the four controls from week five. Data changes: the data steward and the DPO. A model release: the ML lead and the CISO, and the AI governance board signs against written criteria, a fairness report and a red-team report. Human oversight: trained recruiters with the authority and the evidence to disagree, and the works council informed first. Documentation: the technical file, six months of logs, and a record of who approved what and why. The incident plan follows the lecture cycle: detect through alerts and complaints, contain with a kill switch while recruiters work manually, find the faulty version in the logs, and, most important, re-review every application that version touched, the Robodebt lesson. Then the post-mortem, the 72-hour GDPR notice, and the AI Act serious-incident report.

*(130 words)*

## Slide 7: Ethics and law: high-risk under the EU AI Act, and the GDPR today

[4:40] The law. Under the AI Act Atlase is high-risk: Annex III point four, systems that filter applications and evaluate candidates. Not prohibited, because it does no emotion recognition at work. High-risk means risk management, data governance with bias examined, documentation, logging, transparency, human oversight, accuracy and cybersecurity, and registration in the EU database. As deployer, the company assigns trained overseers, keeps logs, informs the works council and the applicants, and explains the system's role on request. One update to the week-two slides: in July 2026 the AI Omnibus postponed the Annex III obligations to the second of December 2027; transparency applies since August 2026. I would build to the high-risk rules now anyway, because the GDPR applies today: no solely automated decision, and after SCHUFA a score the recruiter relies on heavily is itself the decision, so the interface shows criteria and quotes, not one number. Plus a DPIA, information to applicants, six-month retention, and the Labour Law's ban on differential treatment.

*(163 words)*

## Slide 8: The dilemma: should Atlase reject applicants automatically?

[5:35] The dilemma. Twelve thousand applications, eight recruiters, a third of applicants clearly fail a hard requirement. Should the assistant reject them automatically? For: speed, an objective rule, and honestly, recruiters would rubber-stamp these anyway. Against: high confidence is not certainty, a licence in another language is exactly where extraction fails; a wrong automatic rejection is invisible and happens at scale, as in Robodebt; and in Kant's terms the applicant becomes a line to filter, not a person. The GDPR and Article 14 say the same in legal language. My choice: no automatic rejection, but a fast lane. The assistant groups these cases with the quote, a recruiter confirms each in seconds or asks the candidate, a sample is double-checked, and every letter names the requirement so the person can contest it. About a hundred recruiter hours a year, so that nobody is rejected by a mistake nobody saw.

*(149 words)*

## Slide 9: Quality and limits: measuring that it works, and two limits of LLMs

[6:25] How do we know it works? Written targets: extraction accuracy on a benchmark labelled by three recruiters, per language; recall on the must-have checks; evidence faithfulness, one hundred percent of claims with a quote that code can find; fairness as counterfactual consistency and an adverse-impact ratio of at least zero point eight; and in production the override rate, because a rate near zero means recruiters have stopped looking. Two limits shape the design. Hallucination: the model predicts plausible text, so every claim needs a quote and "unclear" is allowed. Bias in training data: the model learned the internet's associations, so identifiers are removed before the call, counterfactual tests run at every release, and weaker Latvian or Russian results block a release.

*(122 words)*

## Slide 10: Five decisions that make Atlase secure, ethical and legal

[6:50] Five decisions: a person decides every time, with evidence; the CV is data, not instructions; nothing is learned from applicants and nothing leaves its scope; written gates for accuracy, fairness and attacks; and built to the high-risk rules before December 2027, because the GDPR already demands most of it. Thank you, happy to take questions.

*(56 words)*

## Slide 11: Appendix: sources

Backup slide with the sources, for questions.

*(7 words)*

---
Total: 1204 words.
