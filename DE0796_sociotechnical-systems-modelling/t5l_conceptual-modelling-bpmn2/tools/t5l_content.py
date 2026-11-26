"""Text of the T5L protocol and presentation (one place, so that both say the same).

Markup used by the builders: **bold**, *italic*.
Numbers that describe the model are taken from build_bpmn.py, so the text cannot disagree with the diagram.
"""
import json
import os

import build_bpmn as model

HERE = os.path.dirname(os.path.abspath(__file__))

NAME = "Vagif Asgarli"
STUDENT_ID = "251ADM047"
DATE = "30. 11. 2026"                      # the template's format: DD. MM. 2026
GOAL_NAME = "CyberFlow"
PR1_TOPIC = "Application of BPMN 2.0 Diagrams in Modelling Cybersecurity Procedures"

# ----------------------------------------------------------------------------- numbers from the model
_kinds = {}
for _kind, *_rest in model.NODES.values():
    _kinds[_kind] = _kinds.get(_kind, 0) + 1
N_TASKS = _kinds["task"]
N_EVENTS = sum(_kinds[k] for k in ("start", "msgstart", "timer", "msgcatch", "end"))
N_GATEWAYS = sum(_kinds[k] for k in ("xor", "and", "or"))
N_SEQ, N_MSG, N_DATA_LINES = len(model.SEQ), len(model.MSG), len(model.ASSOC)
N_DATA_OBJECTS = sum(1 for v in model.DATA.values() if v[0] == "dataobject")
N_LANE_CROSSINGS = sum(1 for f in model.SEQ if model.NODES[f[1]][2] != model.NODES[f[3]][2])
LANES = [lane["name"] for lane in model.POOLS[0]["lanes"]]
POOL_ORG, POOL_CSIRT = model.POOLS[0]["name"], model.POOLS[1]["name"]

with open(os.path.join(HERE, "cyberflow_cld.json"), encoding="utf-8") as _f:
    _cld = json.load(_f)
N_CLD_VARIABLES, N_CLD_LINKS, N_CLD_LOOPS = len(_cld["nodes"]), len(_cld["links"]), len(_cld["loops"])

# ----------------------------------------------------------------------------- theoretical rationale
WHAT_IS_BPMN2 = [
    "BPMN2 is version 2.0 of the Business Process Model and Notation, the standard graphical notation for "
    "business processes of the Object Management Group (OMG, 2011). Version 2.0 was released in January 2011, "
    "and BPMN is also ratified as the ISO 19510 standard (Ginters, 2026b). Its primary goal is a notation that is "
    "readily understandable by all business users: the analysts who draft a process, the developers who implement "
    "it and the people who manage and monitor it (OMG, 2011). BPMN2 is not a methodology but a notation: it shows "
    "how a process is carried out, by whom and in which order.",
    "The elements belong to five basic categories: flow objects, data, connecting objects, swimlanes and "
    "artifacts (OMG, 2011). A process consists of Activities (tasks) that are started, delayed and finished by "
    "Events (start, intermediate and end events, for example Timer, Message or Error) and are connected by "
    "sequence flows. The work is parallelized in two ways: by feature, with Pools and their Swimlanes, which show "
    "who does the work, and by condition, with Gateways: XOR (exactly one path is taken), AND (all paths are taken "
    "in parallel) and OR (one or several paths are taken). Different Pools exchange information only through "
    "message flows, and Data objects show the information that the tasks read and write (Ginters, 2026b).",
]

DIFFERENCES = [
    "Both are conceptual models of the goal system, but they answer different questions. A Causal Loops Diagram "
    "(CLD) shows the cause and effect relationships between the variables of a system and its two basic feedback "
    "loops: reinforcing loops, which compound a change in one direction, and balancing loops, which keep the system "
    "in its current state (Kim, 1999, as cited in Ginters, 2026b). It explains why the system behaves as it does. "
    "A BPMN2 model describes the functionality of the system: which activities are performed, by whom, in which "
    "order and under which conditions. The main differences are summarised in Table 1. The weaknesses of a CLD "
    "listed there (conditional branching is not displayed, parallel processes are hard to represent, the start and "
    "the end of a process cannot be shown, the level of abstraction is high and the translation to an executable "
    "model is problematic) are the reasons why a functional notation such as BPMN2 is needed in addition to it "
    "(Ginters, 2026b).",
]

TABLE1_CAPTION = "Table 1. Differences between a CLD and a BPMN2 model (compiled from Ginters, 2026a, 2026b, and OMG, 2011)"
TABLE1 = [
    ("Aspect", "Causal Loops Diagram (CLD)", "BPMN2 model"),
    ("What it shows", "Why the system behaves as it does: causes, effects and feedbacks",
     "How the system operates: activities, their order and their performers"),
    ("Elements", "Variables, links with a polarity (+ or −), delays, loops R and B",
     "Events, Activities, Gateways, sequence and message flows, Pools and Swimlanes, Data objects"),
    ("Meaning of an arrow", "Influence: a change of one variable changes another",
     "Order of execution (sequence flow) or communication (message flow)"),
    ("Start and end", "None: the diagram has no beginning and no end",
     "Every process runs from a start event to an end event"),
    ("Branching and parallel work", "Not displayed", "Gateways XOR, AND and OR; Pools and Swimlanes"),
    ("Feedback", "The central element: reinforced and balanced loops",
     "Not shown as such; only as a flow that returns or as a repeated run of the process"),
    ("Level of detail", "High abstraction, few elements", "Detailed; a drawing quickly becomes large"),
    ("Next step", "Stocks and flows model for simulation (system dynamics)",
     "Specification for the implementation and automation of the process"),
]

# ----------------------------------------------------------------------------- 1. goal system and CLD
DESCRIPTION = [
    f"{GOAL_NAME} is the goal system of the PR1 topic “{PR1_TOPIC}”: a BPMN 2.0-based method and model repository "
    "for the incident-handling procedures of a medium-sized Latvian organisation that is subject to the NIS2 "
    "Directive. It is a sociotechnical system. Its social part consists of the people who handle an incident (the "
    "employee who notices it, the analysts of the security operations centre (SOC), the cybersecurity manager and "
    "IT operations) and of the national computer security incident response team (CSIRT), CERT.LV. Its technical "
    "part consists of the procedure models drawn in BPMN 2.0, the repository in which they are kept and the "
    "modelling rules that map roles, time limits, notifications and documents to BPMN 2.0 elements.",
    "The system is needed because incident-handling procedures are still mostly written as text: in a study with "
    "147 practitioners, 76.7% of their playbooks were text-based (Schlette et al., 2024), while the law leaves "
    "little time. An essential or important entity must send to the CSIRT an early warning within 24 hours of "
    "becoming aware of a significant incident, an incident notification within 72 hours and a final report not "
    "later than one month after the notification (Directive 2022/2555, 2022). The Latvian National Cybersecurity "
    "Law sets the same time limits (Nacionālās kiberdrošības likums, 2024), and CERT.LV (2026) manually processed "
    f"2,982 incidents in 2025. The purpose of {GOAL_NAME} is that every participant understands a procedure in the "
    "same way, so that fewer procedural errors are made and the time limits are met.",
]

FIG1_CAPTION = (f"Figure 1. Causal Loops Diagram of the goal system {GOAL_NAME}. Blue arrow with “+”: the two "
                "variables change in the same direction; red arrow with “−”: they change in opposite directions; "
                "two strokes across an arrow: delay; R: reinforced loop; B: balanced loop; italics: outside influence.")

CLD_INTRO = (f"The CLD in Figure 1 has {N_CLD_VARIABLES} variables, {N_CLD_LINKS} links and five feedback loops: "
             "two balanced (B) and three reinforced (R).")
LOOPS = [
    ("B1", "loss-driven improvement (balanced)",
     "Incident losses raise management support. With it more procedures are modelled and kept up to date, the "
     "staff understand their roles and steps better, make fewer procedural errors and respond faster, and a "
     "shorter response time reduces the losses. The loop has one negative link, so it counteracts the change: "
     "the organisation reacts to its losses, but with a delay."),
    ("B2", "maintenance limit (balanced)",
     "More models and more detailed models mean more maintenance workload, and when this workload grows, the "
     "models are no longer kept up to date. The loop limits the growth of the repository."),
    ("R1", "learning (reinforced)",
     "Models that are complete and up to date are used in real incidents, every use ends with a review, and the "
     "lessons learned improve the models (Nelson et al., 2025). The loop works in both directions: models that "
     "are not used are not improved either."),
    ("R2", "workload spiral (reinforced)",
     "Procedural errors cause rework and raise the analyst workload, and overloaded analysts make more errors."),
    ("R3", "cooperation with the CSIRT (reinforced)",
     "A short response time makes a timely notification possible. After the early warning the CSIRT gives "
     "feedback and, on request, guidance (Directive 2022/2555, 2022, Article 23(5)), which shortens the response "
     "time further. A late notification has the opposite effect."),
]
CLD_OUTRO = (
    "Two outside influences act on the loops: cyber threats increase the incident losses, and the requirements of "
    "NIS2 and of the national law increase management support. Reinforcing loops must be balanced, otherwise the "
    f"system is unstable (Ginters, 2026a). In {GOAL_NAME} the growth of R1 is limited by B2, and when R2 or R3 run "
    "in the harmful direction, the response time and the losses grow, which activates B1. The polarity of every "
    "loop was checked by counting its negative links: an even number gives a reinforced loop, an odd number a "
    "balanced one.")

# ----------------------------------------------------------------------------- 2. BPMN2 model
TRANSFORM = [
    "The CLD cannot be redrawn in BPMN2 element by element, because its variables are states of the system and "
    "not activities. The transformation was done in three steps. First, the operation that produces the behaviour "
    "shown in the CLD was chosen: the handling of one significant cyber incident, because all five loops pass "
    "through it. Second, every variable was traced to the place of the process in which it appears (Table 2). "
    "Third, the information that a CLD does not contain was added from the legal requirements: the roles, the "
    "order of the activities, the conditions and the three time limits (Directive 2022/2555, 2022; Nacionālās "
    "kiberdrošības likums, 2024).",
]
TABLE2_CAPTION = "Table 2. Transformation of the CLD variables (Figure 1) into BPMN2 elements (Figure 2)"
TABLE2 = [
    ("CLD variable", "BPMN2 element"),
    ("Staff understanding of roles and steps",
     f"Pool “{POOL_ORG}” with four Swimlanes: every task has one responsible role"),
    ("Procedure models in BPMN 2.0; Use of the models in real incidents",
     "Data store “Procedure models”, read by the task “Activate the incident procedure”"),
    ("Lessons learned; Maintenance workload",
     "Task “Review and update the procedure model”, which writes to the data store “Procedure models”"),
    ("Response time; NIS2 and national law",
     "Timer intermediate events with the time limits of 24 hours, 72 hours and one month"),
    ("Timely notification of the CSIRT",
     "Tasks “Send the early warning”, “Send the incident notification” and “Prepare and send the final report” "
     f"with Message flows to the Pool “{POOL_CSIRT}”"),
    ("CSIRT guidance and support",
     f"Task “Send feedback and guidance” in the Pool “{POOL_CSIRT}”, its Message flow and the Message intermediate "
     "event “Feedback and guidance received”"),
    ("Cyber threats", "Start event “Suspicious activity noticed”"),
    ("Incident losses",
     "Gateway XOR “Significant incident?” and the tasks that limit the damage after the Gateway OR “Which "
     "measures are needed?”"),
    ("Procedural errors; Analyst workload; Management support",
     "No BPMN2 element: they describe how well the process is performed and are not steps of it"),
]
N_MAPPED, N_UNMAPPED = 11, 3

OPERATION = [
    "The process starts when an employee notices suspicious activity (Start event) and reports it. The SOC analyst "
    "registers and classifies the event and creates the Data object “Incident ticket”. The cybersecurity manager "
    "assesses the significance of the incident; an incident is significant if it causes or can cause severe "
    "operational disruption or financial loss, or considerable damage to other persons (Directive 2022/2555, "
    "2022, Article 23(3)). The Gateway XOR “Significant incident?” has exactly one outcome: an event that is not "
    "significant is handled as a routine event and the process ends; for a significant incident the cybersecurity "
    "manager activates the incident procedure, which is read from the data store “Procedure models”.",
    "A Gateway AND then starts three parallel branches. IT operations limit the damage: after the Gateway OR "
    "“Which measures are needed?” one, two or all three measures are carried out (isolate the affected systems, "
    "block accounts and addresses, switch to backup systems), and a second Gateway OR merges them. The SOC analyst "
    "collects and preserves the evidence (Data object “Evidence package”). The cybersecurity manager sends the "
    "early warning within the 24-hour time limit and receives the feedback and guidance of the CSIRT (Message "
    "intermediate event). A second Gateway AND waits until all three branches are finished.",
    "After that the SOC analyst prepares the initial assessment (Data object), the cybersecurity manager sends "
    "the incident notification within the 72-hour time limit, IT operations remove the cause and restore the "
    "services, and the cybersecurity manager reviews the incident and updates the procedure model in the data "
    "store. The final report is prepared and sent within one month after the notification, and the process ends "
    f"with the End event “Incident closed”. The process of the Pool “{POOL_CSIRT}” starts with the Message start "
    "event “Early warning received”, answers every message of the organisation and ends with the End event "
    "“Case closed”.",
    "The three legal time limits are drawn as Timer intermediate events in front of the sending tasks. In this "
    "conceptual model such a timer marks the time limit within which the next message must be sent; it is not a "
    "waiting time.",
]
TABLE3_CAPTION = "Table 3. Mandatory notational elements in the BPMN2 model (Figure 2)"
TABLE3 = [
    ("Mandatory element", "In the model"),
    ("At least 2 Pools where at least one of the Pools has multiple Swimlanes",
     f"2 Pools: “{POOL_ORG}” with 4 Swimlanes ({', '.join(LANES)}) and “{POOL_CSIRT}”"),
    ("At least 4 different Events and/or Intermediate events",
     f"5 different kinds, {N_EVENTS} events in total: Start event ({_kinds['start']}), Message start event "
     f"({_kinds['msgstart']}), Timer intermediate event ({_kinds['timer']}), Message intermediate event "
     f"({_kinds['msgcatch']}), End event ({_kinds['end']})"),
    ("All recommended Gateways (OR, AND and XOR)",
     "XOR “Significant incident?” (1); AND: split into three parallel branches and their join (2); OR: split "
     "“Which measures are needed?” and its join (2)"),
    ("Message and Data lines",
     f"{N_MSG} Message flows between the two Pools (Early warning, Feedback and guidance, Incident notification, "
     f"Final report); {N_DATA_LINES} Data lines (data associations) between tasks and Data objects or the data store"),
    ("Several Data objects",
     f"{N_DATA_OBJECTS} Data objects (Incident ticket, Evidence package, Initial assessment, Final report) and the "
     "data store “Procedure models”, which is drawn twice: where it is read and where it is updated"),
]
MODEL_SIZE = (f"In total the model has {N_TASKS} tasks, {N_EVENTS} events, {N_GATEWAYS} gateways, {N_SEQ} sequence "
              f"flows, {N_MSG} message flows and {N_DATA_LINES} data lines.")

INTERACTION = [
    f"Interaction between the Swimlanes: {N_LANE_CROSSINGS} of the {N_SEQ} sequence flows pass from one Swimlane to "
    "another. The employee hands the event over to the SOC analyst and the SOC analyst to the cybersecurity "
    "manager, who starts the parallel work of IT operations and the SOC analyst and later needs the initial "
    "assessment of the SOC analyst for the incident notification.",
    f"Interaction between the Pools: the organisation and the CSIRT are connected only by the {N_MSG} Message "
    "flows, three to the CSIRT (early warning, incident notification, final report) and one back (feedback and "
    "guidance). Every Message flow ends in a Message event of the receiving Pool.",
]
FIGURE_INTRO = ("The model was drawn in the ArisExpress environment and saved in the ADF and PDF formats. Figure 2 "
                "shows the whole diagram; Figures 3 and 4 show its left and right parts enlarged.")
FIGURE_INTRO_DRAFT = ("DRAFT: the figures below are the reference drawing of the model. In the final protocol they "
                      "are replaced by the figure exported from ArisExpress.")
FIG2_CAPTION = (f"Figure 2. BPMN2 model of the operation of the goal system {GOAL_NAME}: handling of a significant "
                "cyber incident (drawn in ArisExpress)")
FIG3_CAPTION = "Figure 3. Left part of the BPMN2 model enlarged: from the detection of the event to the parallel handling"
FIG4_CAPTION = "Figure 4. Right part of the BPMN2 model enlarged: from the parallel handling to the final report"
VERIFICATION = ("Before the drawing the logic of the model was verified: sequence flows stay inside their Pool, "
                "Message flows connect different Pools, every element lies on a path from a start event to an end "
                "event, the AND and OR splits are closed by joins of the same type, and no lines cross.")

# ----------------------------------------------------------------------------- 3. conclusions
CONCLUSIONS = [
    f"A CLD cannot be transformed into a BPMN2 model mechanically. The CLD shows variables and their influences, "
    f"BPMN2 shows activities and their order. Of the {N_CLD_VARIABLES} variables of the CLD, {N_MAPPED} could be "
    f"traced to an element of the process, and {N_UNMAPPED} (procedural errors, analyst workload, management "
    "support) have no BPMN2 element, because they describe how well the process is performed.",
    "The feedback loops, which are the main content of the CLD, are not visible in the BPMN2 model. One run of the "
    "process goes from the start event to the end event, while a loop such as R1 (learning) closes only over many "
    "incidents. It could be shown only indirectly: the task “Review and update the procedure model” writes to "
    "the data store that the next incident reads.",
    "The convenient part was that the CLD had already fixed the border of the system and its participants. The "
    "CSIRT, a variable of loop R3, became the second Pool, the links of R3 became Message flows, and the variable "
    "“Response time” pointed to the Timer events.",
    "The main problem was missing information. A CLD contains no roles, no order of activities, no conditions and "
    "no documents, so the Swimlanes, the Gateways, the time limits and the Data objects had to be taken from the "
    "legal requirements and from incident response guidance (Directive 2022/2555, 2022; Nacionālās kiberdrošības "
    "likums, 2024; Nelson et al., 2025).",
    "Time limits were difficult to express. BPMN lacks support for tasks with uncertainty in time (Ginters, "
    "2026b): “not later than 24 hours” is not a waiting time, so the Timer intermediate events of the model only "
    "mark the limits.",
    f"The level of abstraction had to be chosen carefully, because a detailed BPMN2 drawing has a large size "
    f"(Ginters, 2026b). The model already has {N_TASKS} tasks, {N_EVENTS} events and {N_GATEWAYS} gateways, "
    "although the technical measures are reduced to three tasks. The CLD stays small and readable, but it does not "
    "say who does what.",
    "The two models complement each other. The CLD explains why the procedure models matter and where the system "
    "can become unstable; the BPMN2 model gives a procedure that the staff can follow and that can be compared "
    "with the legal requirements step by step.",
]

# ----------------------------------------------------------------------------- 4. references (APA 7, alphabetical)
AI_NOTE = ("Note. Generative AI tools were used for information retrieval, for designing and checking the models, "
           "for drafting the text and for formatting the reference list: Claude (Anthropic).")

REFERENCES = [
    "CERT.LV. (2026). *Latvijas kiberdrošības un CERT.LV tehnisko aktivitāšu 2025. gada pārskats* [Report on "
    "Latvian cybersecurity and CERT.LV technical activities in 2025]. "
    "https://cert.lv/lv/2026/09/latvijas-kiberdrosibas-un-cert-lv-tehnisko-aktivitasu-2025-gada-parskats",
    "Directive (EU) 2022/2555 of the European Parliament and of the Council of 14 December 2022 on measures for a "
    "high common level of cybersecurity across the Union (NIS 2 Directive). (2022). *Official Journal of the "
    "European Union, L 333*, 80–152. https://eur-lex.europa.eu/eli/dir/2022/2555/oj",
    "Ginters, E. (2026a). *T4. Systems thinking and dynamics simulation* [Lecture slides]. Riga Technical "
    "University, ORTUS. https://ortus.rtu.lv",
    "Ginters, E. (2026b). *T5. Parallelization of work and data flows in a conceptual model* [Lecture slides]. "
    "Riga Technical University, ORTUS. https://ortus.rtu.lv",
    "Nacionālās kiberdrošības likums [National Cybersecurity Law]. (2024). *Latvijas Vēstnesis*, 128A. "
    "https://likumi.lv/ta/id/353390",
    "Nelson, A., Rekhi, S., Souppaya, M., & Scarfone, K. (2025). *Incident response recommendations and "
    "considerations for cybersecurity risk management: A CSF 2.0 community profile* (NIST Special Publication "
    "800-61r3). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-61r3",
    "Object Management Group. (2011). *Business Process Model and Notation (BPMN), version 2.0* (OMG Document "
    "formal/2011-01-03). https://www.omg.org/spec/BPMN/2.0/PDF",
    "Schlette, D., Empl, P., Caselli, M., Schreck, T., & Pernul, G. (2024). Do you play it by the books? A study "
    "on incident response playbooks and influencing factors. In *2024 IEEE Symposium on Security and Privacy (SP)* "
    "(pp. 3625–3643). IEEE. https://doi.org/10.1109/SP54263.2024.00060",
]

# ----------------------------------------------------------------------------- 5. presentation
PRESENTATION_NOTE = ("The presentation was prepared in MS PowerPoint on the T5L template from ORTUS "
                     "(file vagif.asgarli-T5L-presentation.pptx).")
