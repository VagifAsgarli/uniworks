"""Builds the PR1 summary on the lecturer's template (materials/pr1_assignment.pdf):

    Summary / First name, Last name / Date / Title of the Topic / Keywords. /
    five paragraphs as continuous text without subheadings / References (APA 7) / Note on AI tools

The summary itself is one A4 page; the reference list and the note follow it.
Text marked *like this* is set in italics (APA 7 titles and volumes).

    python build_pr1.py <out.docx>       # then convert to PDF with LibreOffice
"""
import re
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

NAME = "Vagif Asgarli"
DATE = "30 November 2026"
TITLE = "Application of BPMN 2.0 Diagrams in Modelling Cybersecurity Procedures"
KEYWORDS = "BPMN 2.0, cybersecurity procedures, incident response playbook, NIS2 Directive, conceptual modelling."

PARAGRAPHS = [
    # 1. Relevance of the topic: global, European, Latvian
    "Cyber incidents have become frequent and costly, so the procedures that an organisation follows when an "
    "incident occurs matter at every level. Globally, the average cost of a data breach reached a record "
    "USD 4.99 million in 2026, 12% more than a year earlier (IBM, 2026). In Europe, the European Union Agency for "
    "Cybersecurity (ENISA, 2026) analysed 8,257 incidents recorded in 2025, of which 72.9% affected essential "
    "entities, and the NIS2 Directive obliges such entities to have incident handling in place and to report a "
    "significant incident with an early warning within 24 hours, a notification within 72 hours and a final report "
    "within one month (Directive 2022/2555, 2022). In Latvia the same deadlines apply under the National "
    "Cybersecurity Law, in force since 1 September 2024 (Nacionālās kiberdrošības likums, 2024), while CERT.LV "
    "(2026) manually processed 2,982 incidents in 2025, 28% more than in 2024. Such deadlines can be met only "
    "with procedures that every participant understands alike.",
    # 2. Problem identification and existing solutions
    "The main problem is that incident-handling procedures (playbooks) are still written mostly as prose or as "
    "vendor-specific code, which makes them ambiguous and hard to verify, share and automate. In a study of 1,217 "
    "public playbooks and 147 practitioners, 76.7% of the practitioners’ playbooks were text-based and the public "
    "ones could not be used outright because of missing or obsolete information (Schlette et al., 2024); in another "
    "experiment experts judged 11 of 24 playbooks written with two standard frameworks as insufficiently detailed "
    "for real use (Stevens et al., 2022). Three existing solutions address the problem. First, NIST SP 800-61 "
    "Revision 3 gives textual recommendations and advises documenting procedures as playbooks (Nelson et al., "
    "2025); it is flexible, but it defines no notation, so the ambiguity of prose remains. "
    "Second, CACAO Security Playbooks 2.0, an OASIS Committee Specification of 27 November 2023, encodes a playbook "
    "in JSON as a workflow of eight step types (Jordan & Thomson, 2023); it is machine-readable and shareable, yet "
    "it has no native graphical notation and even a simple playbook takes hundreds of lines of code (Zych et al., "
    "2023). Third, BPMN 2.0, the graphical notation of the Object Management Group (OMG, 2011) built from flow "
    "objects, data, connecting objects, swimlanes and artifacts, is meant to be understood by managers and "
    "engineers alike, and its security extensions such as SecBPMN add security annotations and a query language "
    "that checked a process of 50 activities in 14.71 seconds (Salnitri et al., 2017). However, a review of 1,400 "
    "sources found only 12 security-aware BPMN extensions (Hornsteiner et al., 2022); they are not part of the "
    "standard, they annotate business processes with security requirements instead of describing response "
    "procedures, and keeping BPMN models synchronised with executable workflows is difficult (Akbari Gurabi et "
    "al., 2024).",
    # 3. Aim, tasks, and methods
    "The proposed approach is to describe incident-handling procedures with the standard BPMN 2.0 elements only: "
    "pools for the organisation and the computer security incident response team (CSIRT), swimlanes for roles, "
    "timer events for the legal deadlines, message flows for notifications and data objects for evidence and "
    "reports, so that the models can be drawn in free tools. The aim of the research is "
    "to develop and validate CyberFlow, a BPMN 2.0-based method and model repository for the incident-handling "
    "procedures of a medium-sized Latvian organisation subject to NIS2. The tasks are (1) to analyse the legal "
    "requirements and the existing playbook formats; (2) to define modelling rules that map roles, deadlines, "
    "notifications and documents to BPMN 2.0 elements; (3) to build the conceptual model of the goal system as a "
    "concept map and a causal loop diagram, and BPMN 2.0 models of three typical procedures (phishing, ransomware "
    "and denial of service); (4) to verify the models against the notation and the legal requirements; and (5) to "
    "validate them in a tabletop exercise against the prose versions. The methods are literature analysis, "
    "conceptual modelling (concept maps, causal loop diagrams and BPMN 2.0 diagrams in ARIS Express), expert "
    "review and a comparative experiment.",
    # 4. Expected results and target audience
    "The expected results are three validated procedure models in which every step has a responsible role and all "
    "three reporting deadlines appear as explicit events, a set of modelling rules, and measured evidence from the "
    "exercise, where the target is at least 20% fewer procedural errors and a shorter time to the first "
    "notification than with the prose procedures. The potential users are chief information security officers and "
    "security operations teams of essential and important entities, especially those without automation "
    "platforms, as well as auditors and the CSIRT. They gain a shared and unambiguous description of "
    "who does what and when, faster training of new staff, documented evidence of compliance and a starting point "
    "for automation, which matters because extensive use of AI and automation in security is associated with "
    "breach costs that are USD 1.93 million lower (IBM, 2026).",
    # 5. Further development
    "The proposed solution will not solve the problem completely. BPMN 2.0 leaves simulation, monitoring and "
    "organisational resource models outside its scope (OMG, 2011), so the models show the logic of a procedure but "
    "neither execute it nor predict response times; graphical models are also understood better only by trained "
    "readers (Ottensooser et al., 2012), and the mapping between BPMN and CACAO is not one-to-one (Zych et al., "
    "2023). Further research should therefore add an automatic transformation of the validated models into CACAO "
    "playbooks for execution, simulate response times with system dynamics and discrete-event models, extend the "
    "repository to further incident types and sectors, and repeat the evaluation in several organisations.",
]

REFERENCES = [
    "Akbari Gurabi, M., Nitz, L., Bregar, A., Popanda, J., Siemers, C., Matzutt, R., & Mandal, A. (2024). "
    "Requirements for playbook-assisted cyber incident response, reporting and automation. *Digital Threats: "
    "Research and Practice, 5*(3), Article 34. https://doi.org/10.1145/3688810",
    "CERT.LV. (2026). *Latvijas kiberdrošības un CERT.LV tehnisko aktivitāšu 2025. gada pārskats* [Report on "
    "Latvian cybersecurity and CERT.LV technical activities in 2025]. "
    "https://cert.lv/lv/2026/09/latvijas-kiberdrosibas-un-cert-lv-tehnisko-aktivitasu-2025-gada-parskats",
    "Directive (EU) 2022/2555 of the European Parliament and of the Council of 14 December 2022 on measures for a "
    "high common level of cybersecurity across the Union (NIS 2 Directive). (2022). *Official Journal of the "
    "European Union, L 333*, 80–152. https://eur-lex.europa.eu/eli/dir/2022/2555/oj",
    "European Union Agency for Cybersecurity. (2026). *ENISA threat landscape 2026*. "
    "https://www.enisa.europa.eu/publications/enisa-threat-landscape-2026",
    "Hornsteiner, M., Stoiber, C., & Schönig, S. (2022). Towards security- and IIoT-aware BPMN: A systematic "
    "literature review. In *Proceedings of the 19th International Conference on Smart Business Technologies* "
    "(pp. 45–56). SciTePress. https://doi.org/10.5220/0011317700003280",
    "IBM. (2026). *Cost of a data breach report 2026*. https://www.ibm.com/reports/data-breach",
    "Jordan, B., & Thomson, A. (Eds.). (2023). *CACAO security playbooks version 2.0* (OASIS Committee "
    "Specification 01). OASIS Open. "
    "https://docs.oasis-open.org/cacao/security-playbooks/v2.0/cs01/security-playbooks-v2.0-cs01.html",
    "Nacionālās kiberdrošības likums [National Cybersecurity Law]. (2024). *Latvijas Vēstnesis*, 128A. "
    "https://likumi.lv/ta/id/353390",
    "Nelson, A., Rekhi, S., Souppaya, M., & Scarfone, K. (2025). *Incident response recommendations and "
    "considerations for cybersecurity risk management: A CSF 2.0 community profile* (NIST Special Publication "
    "800-61r3). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-61r3",
    "Object Management Group. (2011). *Business Process Model and Notation (BPMN), version 2.0* (OMG Document "
    "formal/2011-01-03). https://www.omg.org/spec/BPMN/2.0/PDF",
    "Ottensooser, A., Fekete, A., Reijers, H. A., Mendling, J., & Menictas, C. (2012). Making sense of business "
    "process descriptions: An experimental comparison of graphical and textual notations. *Journal of Systems and "
    "Software, 85*(3), 596–606. https://doi.org/10.1016/j.jss.2011.09.023",
    "Salnitri, M., Dalpiaz, F., & Giorgini, P. (2017). Designing secure business processes with SecBPMN. "
    "*Software & Systems Modeling, 16*(3), 737–757. https://doi.org/10.1007/s10270-015-0499-4",
    "Schlette, D., Empl, P., Caselli, M., Schreck, T., & Pernul, G. (2024). Do you play it by the books? A study "
    "on incident response playbooks and influencing factors. In *2024 IEEE Symposium on Security and Privacy (SP)* "
    "(pp. 3625–3643). IEEE. https://doi.org/10.1109/SP54263.2024.00060",
    "Stevens, R., Votipka, D., Dykstra, J., Tomlinson, F., Quartararo, E., Ahern, C., & Mazurek, M. L. (2022). How "
    "ready is your ready? Assessing the usability of incident response playbook frameworks. In *CHI Conference on "
    "Human Factors in Computing Systems* (pp. 1–18). ACM. https://doi.org/10.1145/3491102.3517559",
    "Zych, M., Mavroeidis, V., Fysarakis, K., & Athanatos, M. (2023). Reviewing BPMN as a modeling notation for "
    "CACAO security playbooks. In *2023 IEEE International Conference on Cyber Security and Resilience (CSR)* "
    "(pp. 490–495). IEEE. https://doi.org/10.1109/CSR57506.2023.10224922",
]

AI_NOTE = ("Note. Generative AI tools were used for information retrieval, drafting of the text and formatting the "
           "reference list: Claude (Anthropic).")

FONT = "Times New Roman"
BODY_PT = 10


def set_font(run, size=BODY_PT, bold=False, italic=False):
    run.font.name = FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic


def add(doc, text, *, size=BODY_PT, bold=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=3, hanging=None, lead_bold=None):
    """Adds a paragraph; *...* segments are italic; `lead_bold` is a bold lead-in such as 'Keywords.'"""
    p = doc.add_paragraph()
    p.alignment = align
    fmt = p.paragraph_format
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(after)
    fmt.line_spacing = 1.0
    if hanging is not None:
        fmt.left_indent = Cm(hanging)
        fmt.first_line_indent = Cm(-hanging)
    if lead_bold:
        set_font(p.add_run(lead_bold + " "), size, bold=True)
    for i, part in enumerate(re.split(r"\*(.+?)\*", text)):
        if part:
            set_font(p.add_run(part), size, bold=bold, italic=(i % 2 == 1))
    return p


def build(out):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)           # A4
    sec.left_margin = sec.right_margin = Cm(2.0)
    sec.top_margin = sec.bottom_margin = Cm(1.8)
    doc.styles["Normal"].font.name = FONT
    doc.styles["Normal"].font.size = Pt(BODY_PT)

    add(doc, "Summary", bold=True, size=12, align=WD_ALIGN_PARAGRAPH.LEFT, after=2)
    add(doc, NAME, align=WD_ALIGN_PARAGRAPH.LEFT, after=0)
    add(doc, DATE, align=WD_ALIGN_PARAGRAPH.LEFT, after=4)
    add(doc, TITLE, bold=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, after=4)
    add(doc, KEYWORDS, lead_bold="Keywords.", after=4)
    for text in PARAGRAPHS:
        add(doc, text, after=3)
    last = doc.paragraphs[-1]
    last.add_run().add_break(WD_BREAK.PAGE)                         # the summary is exactly one page
    add(doc, "References", bold=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, after=6)
    for ref in REFERENCES:                                          # APA 7: alphabetical, hanging indent
        add(doc, ref, align=WD_ALIGN_PARAGRAPH.LEFT, after=4, hanging=1.27)
    add(doc, "", after=4)
    add(doc, AI_NOTE, align=WD_ALIGN_PARAGRAPH.LEFT, after=0)
    doc.core_properties.author = doc.core_properties.last_modified_by = NAME
    doc.core_properties.title = TITLE
    doc.save(out)
    words = sum(len(t.split()) for t in PARAGRAPHS)
    print(f"written {out}: {words} words in the five paragraphs, {len(REFERENCES)} references")


if __name__ == "__main__":
    build(sys.argv[1])
