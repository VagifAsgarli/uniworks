# Tools used for the project

Scripts used to check and extract the course materials (`../../materials/`). Python 3 with
`pdfplumber`, `pypdf` and `python-pptx`; `pdftotext` (poppler) for the text extracts.

| Script | Purpose |
|---|---|
| `scan_pdf_hidden.py <pdf…>` | flags text a reader would not see: font < 5 pt, white/near-white fill, text outside the page, plus annotations and unusual metadata; prints each flagged group with its text |
| `scan_pptx_hidden.py <pptx…>` | flags hidden slides, speaker notes, tiny or white runs, shapes outside the slide, text in masters/layouts |
| `pptx2txt_to.py <pptx> <txt>` | text extract of a PPTX (slide text and tables) |

Result of the scan on 3 November 2026 (all lectures, group boards and the task slides): the only
hidden text is on page 10 of the week-5 lecture (2 pt, white, Calibri; 289 characters addressed
to language models). Everything else flagged was visible: white headings on green backgrounds,
a 3 pt image-source URL in week 6, and the small sticky-note text of the Miro board exports.
Text render modes other than fill were not used anywhere (no invisible `3 Tr` text).
