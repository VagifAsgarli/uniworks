// Builds the research-project presentation (RTU template style) with pptxgenjs.
// Usage: node build_deck.js <out.pptx> <logo_green.png> <logo_white.png> <apply_theme.js> <figures dir>
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const [OUT, LOGO_GREEN, LOGO_WHITE, APPLY_THEME, FIGDIR] = process.argv.slice(2);
if (!OUT || !APPLY_THEME || !FIGDIR) {
  console.error("usage: node build_deck.js <out.pptx> <logo_green.png> <logo_white.png> <apply_theme.js> <figures dir>");
  process.exit(1);
}
const { applyTheme } = require(APPLY_THEME);

const THEME = {
  name: "RTU research project",
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  colors: { dk1: "262626", lt1: "FFFFFF", dk2: "007A61", lt2: "EDF4F2", accent1: "007A61", accent2: "D0E4DE",
            accent3: "B2443B", accent4: "C98A00", accent5: "5A5A5A", accent6: "9BC8BB", hlink: "007A61", folHlink: "007A61" },
};
const HEX = THEME.colors;
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "Vagif Asgarli";
pres.title = "Log indicator matching on the GPU as the indicator list grows";
pres.subject = "DE0831 research project, topic 10";
const C = pres.SchemeColor;
const FOOTER = "DE0831 Cybersecurity Solutions in HPC Environments  ·  Research project, topic 10  ·  Vagif Asgarli, 251ADM047";

function motif(objects, color) {
  for (const l of [{ x: 10.9, y: 0.0, w: 2.43, h: 2.1, flipH: true }, { x: 11.9, y: 0.0, w: 1.43, h: 1.25, flipH: true },
                   { x: 10.9, y: 2.1, w: 2.43, h: 0.0 }, { x: 12.5, y: 0.0, w: 0.0, h: 2.9 }]) {
    objects.push({ line: { x: l.x, y: l.y, w: l.w, h: l.h, line: { color, width: 0.75 }, flipH: !!l.flipH } });
  }
}
{ const objects = []; motif(objects, "2E9077");
  if (LOGO_WHITE && fs.existsSync(LOGO_WHITE)) objects.push({ image: { path: LOGO_WHITE, x: 0.45, y: 0.4, w: 1.45, h: 0.62 } });
  objects.push({ placeholder: { options: { name: "title", type: "title", x: 0.45, y: 1.55, w: 11.5, h: 1.9, fontSize: 34, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } });
  objects.push({ placeholder: { options: { name: "body", type: "body", x: 0.45, y: 3.6, w: 11.5, h: 2.6, fontSize: 16, color: C.background1, valign: "top", align: "left", margin: 0 }, text: "" } });
  pres.defineSlideMaster({ title: "TITLE", background: { color: HEX.dk2 }, objects }); }
{ const objects = []; motif(objects, HEX.accent2);
  if (LOGO_GREEN && fs.existsSync(LOGO_GREEN)) objects.push({ image: { path: LOGO_GREEN, x: 0.45, y: 0.3, w: 1.25, h: 0.53 } });
  objects.push({ placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.9, w: 11.2, h: 0.6, fontSize: 24, bold: true, color: C.text2, valign: "middle", align: "left", margin: 0 }, text: "" } });
  objects.push({ rect: { x: 0.6, y: 1.52, w: 0.7, h: 0.035, fill: { color: HEX.dk2 }, line: { color: HEX.dk2, width: 0 } } });
  objects.push({ text: { text: FOOTER, options: { x: 0.6, y: 7.05, w: 10.5, h: 0.3, fontSize: 9, color: HEX.accent5, margin: 0, isTextBox: true } } });
  pres.defineSlideMaster({ title: "CONTENT", background: { color: HEX.lt1 }, objects, slideNumber: { x: 12.3, y: 7.05, w: 0.6, h: 0.3, fontSize: 9, color: HEX.accent5, align: "right" } }); }
{ const objects = []; motif(objects, "2E9077");
  if (LOGO_WHITE && fs.existsSync(LOGO_WHITE)) objects.push({ image: { path: LOGO_WHITE, x: 0.45, y: 0.4, w: 1.45, h: 0.62 } });
  objects.push({ placeholder: { options: { name: "title", type: "title", x: 0.45, y: 1.2, w: 12.0, h: 0.8, fontSize: 28, bold: true, color: C.background1, valign: "middle", align: "left", margin: 0 }, text: "" } });
  pres.defineSlideMaster({ title: "DARK", background: { color: HEX.dk2 }, objects }); }

const B = 12;
function card(s, x, y, w, h, o = {}) { s.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.06, fill: { color: o.fill || C.background2 }, line: { color: o.line || HEX.accent2, width: 0.75 }, objectName: o.name || "card" }); }
function heading(s, t, x, y, w, o = {}) { s.addText(t, { x, y, w, h: o.h || 0.3, fontSize: o.size || 13, bold: true, color: o.color || C.text2, margin: 0, isTextBox: true, valign: "middle", objectName: "heading" }); }
function bullets(s, items, x, y, w, h, o = {}) {
  const runs = items.map((t, i) => ({ text: typeof t === "string" ? t : t.text, options: Object.assign({ bullet: { indent: 10 }, breakLine: i < items.length - 1, paraSpaceAfter: o.space == null ? 3 : o.space }, typeof t === "string" ? {} : t.options || {}) }));
  s.addText(runs, { x, y, w, h, fontSize: o.size || B, color: o.color || C.text1, margin: 0, isTextBox: true, valign: "top", objectName: "bullets" });
}
function para(s, runs, x, y, w, h, o = {}) { s.addText(runs, { x, y, w, h, fontSize: o.size || B, color: o.color || C.text1, margin: 0, isTextBox: true, valign: o.valign || "top", align: o.align || "left", bold: !!o.bold, objectName: o.name || "text" }); }
function big(s, value, label, x, y, w, o = {}) {
  card(s, x, y, w, 1.15, o);
  s.addText(value, { x: x + 0.15, y: y + 0.08, w: w - 0.3, h: 0.55, fontSize: o.size || 24, bold: true, color: o.color || C.text2, margin: 0, isTextBox: true, valign: "middle", objectName: "big value" });
  s.addText(label, { x: x + 0.15, y: y + 0.62, w: w - 0.3, h: 0.48, fontSize: 10.5, color: HEX.accent5, margin: 0, isTextBox: true, valign: "top", objectName: "big label" });
}
function fig(s, file, x, y, w, h) { s.addImage({ path: path.join(FIGDIR, file), x, y, w, h, objectName: "figure " + file }); }
function newSlide(master, section, title) { const s = pres.addSlide({ masterName: master, sectionTitle: section }); if (title) s.addText(title, { placeholder: "title" }); return s; }

async function build() {
  // 1 title
  pres.addSection({ title: "Introduction" });
  { const s = newSlide("TITLE", "Introduction", null);
    s.addText([{ text: "Log indicator matching on the GPU", options: { breakLine: true, fontSize: 34 } },
               { text: "as the indicator list grows from 10 to 10,000", options: { fontSize: 24, bold: false } }], { placeholder: "title" });
    s.addText([{ text: "Research project, topic 10: a measurable performance study", options: { breakLine: true, bold: true, fontSize: 16 } },
               { text: "DE0831 Cybersecurity Solutions in High-Performance Computing Environments", options: { breakLine: true, fontSize: 14 } },
               { text: " ", options: { breakLine: true, fontSize: 8 } },
               { text: "Vagif Asgarli, student ID 251ADM047", options: { breakLine: true, fontSize: 14 } },
               { text: "Riga Technical University, Institute of Information Technology", options: { breakLine: true, fontSize: 11 } },
               { text: "14 December 2026", options: { fontSize: 11 } }], { placeholder: "body" });
    s.addNotes("[0:00] Good afternoon. My project is topic 10, log indicator matching: how many log lines per second one GPU can match against a threat-intelligence list, and what happens when that list grows from ten entries to ten thousand. I worked alone, by agreement. Ten minutes, then questions; the live run is already started on Colab and I will show its output at the end."); }

  // 2 the question
  pres.addSection({ title: "Question" });
  { const s = newSlide("CONTENT", "Question", "The question: what does the list cost?");
    card(s, 0.6, 1.75, 6.0, 2.35); heading(s, "The security context", 0.8, 1.85, 5.6);
    bullets(s, ["A SOC matches its logs against threat-intelligence indicators: addresses and hostnames known to be malicious",
                "Real feeds are long (hundreds to tens of thousands) and cold: almost no indicator ever appears, yet every one must be checked against every line",
                "Two kinds of matcher: cost per indicator per line, or cost per token whatever the list"], 0.8, 2.2, 5.6, 1.85, { size: 11.5 });
    card(s, 6.8, 1.75, 5.95, 2.35, { fill: "F3F8F6" }); heading(s, "Measurable objective", 7.0, 1.85, 5.5);
    bullets(s, ["Lines per second on one GPU as the list grows from 10 to 10,000, against a tuned multithreaded CPU with the same algorithm and the naive library route",
                "Hit set verified against the ground truth for every list size: no method is fast because it is wrong",
                "Secondary: the data rate at which the CPU stops keeping up and the GPU is needed, with the host-to-device copy counted; cores replaced"], 7.0, 2.2, 5.5, 1.85, { size: 11.5 });
    big(s, "lines / s at N", "the metric, for N = 10 … 10,000 indicators", 0.6, 4.35, 2.9);
    big(s, "MB/s, GB/day", "the same number in the units a SOC plans with", 3.65, 4.35, 2.9);
    big(s, "894 hits", "the ground truth every method must reproduce, for every list", 6.7, 4.35, 2.9);
    big(s, "1 GPU vs cores", "how many CPU cores one Tesla T4 replaces", 9.75, 4.35, 2.8);
    para(s, "Brief: “determine the data rate at which GPU log mining exceeds a tuned multicore CPU baseline and identify the factors that limit throughput as the input grows.” Here the input that grows is the indicator list.", 0.6, 5.75, 12.0, 0.8, { size: 11, color: HEX.accent5 });
    s.addNotes("[0:30] The question is about the cost of the list. A SOC gets a feed of thousands of indicators and must check every one against every log line; nearly all of them are cold. There are two families of matchers: those whose cost is per indicator and per line, and those that pay once per token whatever the list. My objective is a measurable one: lines per second on one GPU as the list grows from ten to ten thousand, against a tuned multithreaded CPU with the same algorithm, with the hits checked against the ground truth every time. The secondary questions are the data rate where the CPU stops keeping up, with the copy counted, and how many cores one T4 replaces."); }

  // 3 data and semantics
  pres.addSection({ title: "Data" });
  { const s = newSlide("CONTENT", "Data", "Data: the course corpus and lists that grow without changing the hits");
    card(s, 0.6, 1.75, 4.0, 4.9); heading(s, "The corpus", 0.8, 1.85, 3.6);
    bullets(s, ["Handout generator, seed from my student ID: 1,000,000 lines, 119.2 MB (125k to 4M for the size sweep)",
                "sshd and nginx events; RFC 5737 addresses, .invalid hostnames",
                "20 planted indicators (12 addresses, 8 DGA domains) in 894 lines: the truth file",
                "20.6 million tokens of 5.8 bytes on average"], 0.8, 2.2, 3.6, 3.0, { size: 11.5 });
    card(s, 4.8, 1.75, 4.0, 4.9, { fill: "F3F8F6" }); heading(s, "The lists: 10 … 10,000", 5.0, 1.85, 3.6);
    bullets(s, ["Up to 20: subsets of the planted indicators",
                "Above 20: the 20 plus synthetic cold indicators in the same forms: 198.18.x.y (RFC 2544 benchmarking range) and 12–20-letter .invalid hostnames",
                "They cannot occur in the corpus, so the truth of every list is the generator’s truth restricted to it",
                "Only the list size changes between runs; every method must report the same 894 hits"], 5.0, 2.2, 3.6, 3.6, { size: 11.5 });
    card(s, 9.0, 1.75, 3.75, 4.9); heading(s, "Matching rule", 9.2, 1.85, 3.4);
    bullets(s, ["An indicator matches a line when it occurs as a whole token: the bytes around it are not word characters [A-Za-z0-9.-]",
                "192.0.2.24 never matches inside 192.0.2.248",
                "The same rule on the CPU and in every kernel; occursin (substring) gives the same hits here",
                "Nothing from any real system (course policy)"], 9.2, 2.2, 3.4, 3.6, { size: 11.5 });
    s.addNotes("[1:30] The data is the course corpus from the handout generator with my ID: a million lines, 119 megabytes, with twenty planted indicators that hit 894 lines, which is the truth file. The lists are built from the same seed: up to twenty they are subsets of the planted ones; above twenty I add cold indicators in the same two forms, addresses from the RFC 2544 benchmarking range and DGA-style .invalid hostnames, which cannot occur in the corpus. So the truth of every list is known exactly and only the list size changes; every method has to report the same 894 hits: that is a real feed, and a fair comparison. The rule is whole tokens, so 192.0.2.24 never matches inside 192.0.2.248."); }

  // 4 methods
  pres.addSection({ title: "Methods" });
  { const s = newSlide("CONTENT", "Methods", "Methods: one list-independent GPU pipeline, three baselines");
    const steps = [["Line table", "newline flags → scan → scatter"], ["Token starts", "word-start flags → scan → scatter"],
                   ["Hash match", "one thread per token: FNV-1a as it reads, probe an open-addressing table (16 B per slot, load ≤ 0.5), compare bytes on a hash hit"],
                   ["Extraction", "hit tokens compacted; line by binary search; pairs to the host"]];
    const sx = 0.6, sy = 1.72, sw = 2.9, sh = 1.25, gap = 0.15;
    for (let i = 0; i < steps.length; i++) {
      const x = sx + i * (sw + gap); card(s, x, sy, sw, sh, { fill: "F3F8F6", name: "flow " + i });
      heading(s, steps[i][0], x + 0.12, sy + 0.08, sw - 0.24, { size: 12 });
      para(s, steps[i][1], x + 0.12, sy + 0.4, sw - 0.24, 0.8, { size: 10.5 });
      if (i < steps.length - 1) s.addShape(pres.ShapeType.rightArrow, { x: x + sw - 0.02, y: sy + 0.5, w: gap + 0.04, h: 0.22, fill: { color: C.accent1 }, line: { color: C.accent1, width: 0 }, objectName: "arrow" });
    }
    para(s, "G2, the method: one flat byte vector, thread i owns byte i (coalesced), the lecture-7 scan and compaction twice, then one hash per token. Cost: one pass over the corpus, independent of the list; the list enters only through the table’s footprint (0.5 KB at 10, 512 KB at 10,000) against the caches.", 0.6, 3.05, 12.1, 0.6, { size: 11 });
    card(s, 0.6, 3.8, 3.95, 2.85); heading(s, "G3: the same match, no compaction", 0.8, 3.9, 3.6);
    bullets(s, ["One thread per byte; a thread whose byte starts a token walks, hashes and probes it", "Hits appended with one atomic counter (0.09 % of lines)", "Measures what the scan costs against warp divergence"], 0.8, 4.25, 3.6, 2.3, { size: 11 });
    card(s, 4.7, 3.8, 3.95, 2.85); heading(s, "G1: per-indicator (unoptimised GPU baseline)", 4.9, 3.9, 3.6);
    bullets(s, ["The Project 2 kernel: 4 KB shared-memory tile, three-byte prefix filter, atomic OR into the line mask", "One launch per group of 32 indicators: cost ∝ ⌈N/32⌉", "Measured to 3,000 (94 launches), predicted at 10,000"], 4.9, 4.25, 3.6, 2.3, { size: 11 });
    card(s, 8.8, 3.8, 3.95, 2.85, { fill: "F3F8F6" }); heading(s, "C1, C2: the CPU baselines", 9.0, 3.9, 3.6);
    bullets(s, ["C1 tuned: the same hash-set algorithm in Julia, hand-written table, no allocation per token, one task per newline-aligned chunk (1, 2, 4 tasks on a 4-core Xeon; 1, 2 on the Colab host)", "C2 library: occursin per indicator over the lines, up to 300"], 9.0, 4.25, 3.6, 2.3, { size: 11 });
    s.addNotes("[2:30] The method is a token hash set. The corpus is one flat byte vector on the device; thread i owns byte i, so every warp reads 32 consecutive bytes. The lecture-7 pattern, flag per byte, inclusive scan, scatter, gives first the line table and then the token starts. Then one thread per token walks its bytes, computing the FNV-1a hash as it reads, and probes an open-addressing table of the indicators with linear probing; on a hash hit it compares the bytes. The cost is one pass whatever the list; the list only sets the table size, half a kilobyte at ten entries, half a megabyte at ten thousand. Three baselines: the same match without compaction, one thread per byte, to measure what the scan costs; the Project 2 kernel, one launch per 32 indicators, whose cost grows with the list; and the same hash-set algorithm on the CPU, tuned, one task per chunk, plus occursin per indicator."); }

  // 5 validation and measurement
  pres.addSection({ title: "Methodology" });
  { const s = newSlide("CONTENT", "Methodology", "Validation first, then the lecture-7 timing");
    card(s, 0.6, 1.75, 6.0, 4.9); heading(s, "Validated before any timing (the run prints Correct!)", 0.8, 1.85, 5.6);
    bullets(s, ["CPU matcher with 1 and more tasks = the generator’s truth for its 20 indicators; occursin = truth",
                "GPU line table = CPU line table",
                "GPU hash set (global table, shared keys), the no-compaction variant and the per-indicator kernel = the CPU matcher",
                "For every list size: all methods = the truth restricted to the list (894 pairs)",
                "11 hand-made cases: empty corpus, no final newline, prefixes of longer tokens, several hits in a line, chunk boundaries, 64-byte limit",
                "test/runtests.jl repeats it"], 0.8, 2.2, 5.6, 4.3, { size: 11.5 });
    card(s, 6.8, 1.75, 5.95, 4.9, { fill: "F3F8F6" }); heading(s, "Measured as lecture 7 says", 7.0, 1.85, 5.5);
    bullets(s, ["One warm-up launch (compiles), CUDA.synchronize(), then one CUDA.@elapsed per launch, 100 launches: mean, min, max",
                "Every step timed on its own; the pipeline one timing of its own; the copy a separate timing: no figure is a difference",
                "Accumulating kernels reset outside the timed region; every launch’s outputs freed, so no GC inside a timing",
                "CPU: wall-clock @elapsed, best of 3 after a warm-up, tasks stated",
                "Evidence from the script itself: probes per token, table bytes vs caches, registers, occupancy, PTX, copy rate"], 7.0, 2.2, 5.5, 4.3, { size: 11.5 });
    s.addNotes("[4:00] Before any timing the run validates everything on the million-line corpus: the CPU matcher against the generator's truth, the library route, the GPU line table, and every GPU variant against the CPU matcher, for every list size; plus eleven hand-made cases for the edges. Only then it times, the way lecture 7 says: a warm-up, synchronize, then one CUDA elapsed per launch over a hundred launches, every step on its own, the pipeline as one timing, the copy as another; nothing is a difference of two timings, and nothing accumulates or garbage-collects inside a timed interval. The script also writes its own evidence. The live run on the screen starts now."); }

  // 6 result 1
  pres.addSection({ title: "Results" });
  { const s = newSlide("CONTENT", "Results", "Result 1: the hash-set pipeline is flat; everything per-indicator is linear");
    fig(s, "rate_vs_list.png", 0.6, 1.7, 8.2, 4.1);
    big(s, "30 M lines/s", "GPU hash-set pipeline, 10 to 10,000 indicators: 32.9–33.3 ms, a 1 % spread", 9.0, 1.7, 3.75);
    big(s, "49 M lines/s", "the same match without the token scan: 19.8–24.8 ms", 9.0, 2.95, 3.75);
    big(s, "5.9 ms per 32", "per-indicator kernel: 5.6 ms at 10, 561 ms at 3,000, 1.86 s predicted at 10,000 (56×)", 9.0, 4.2, 3.75, { color: HEX.accent3 });
    para(s, "Tesla T4, 1,000,000 lines. CPU lines are the Colab host (one core, two hardware threads); occursin is 1.1 s at 10 and 33 s at 300 indicators there. The hash-match kernel alone: 1.9–2.7 ms with 1.4–2.4 probes per token, so even the kernel that touches the table does not see the list.", 0.6, 5.9, 12.1, 0.75, { size: 11, color: HEX.accent5 });
    s.addNotes("[4:45] The first result, on a million lines. The hash-set pipeline is flat: 33 milliseconds from ten to ten thousand indicators, thirty million lines per second; the match kernel alone is two to three milliseconds with two probes per token, so even the kernel that touches the table does not see the list. Without the token scan the pipeline is 20 milliseconds, fifty million lines per second, also flat. The per-indicator kernel is the straight line going down: 5.9 milliseconds per group of 32, so 5.6 milliseconds at ten indicators, 561 milliseconds at three thousand, and 1.9 seconds predicted at ten thousand, 56 times the hash set. With the line table it needs, the hash-set pipeline overtakes it between 30 and 100 indicators. The CPU hash set is flat too; occursin is the other straight line, 33 seconds at 300 indicators, 14 minutes per million lines at ten thousand."); }

  // 7 result 2
  { const s = newSlide("CONTENT", "Results", "Result 2: the limiter is the scan traffic, not the hash table");
    fig(s, "breakdown_vs_list.png", 0.6, 1.7, 6.6, 3.7);
    card(s, 7.4, 1.7, 5.35, 3.7, { fill: "F3F8F6" }); heading(s, "At 1,000,000 lines and 1,000 indicators", 7.6, 1.8, 5.0);
    bullets(s, ["Line table 13.3 ms (40 %), token scan 15.7 ms (47 %), hash match 2.7 ms (8 %), extraction 2.3 ms (7 %)",
                "The two scans move about 8 bytes per corpus byte (UInt32 flags, scan, scatter); the hash kernel reads 1",
                "Hash kernel: 45 GB/s of corpus against a 241 GB/s copy rate: bound by the serial byte walk and the probe per thread, not by bandwidth (28 registers, occupancy 100 %, 15 branches, no atomics)",
                "Keys in shared memory do not help (2.2–3.1 vs 1.9–2.7 ms): the probes come from L1/L2; even the 512 KB table is 12 % of L2"], 7.6, 2.15, 5.0, 3.2, { size: 10.5 });
    big(s, "33 → 20 ms", "dropping the token scan (15.7 ms) and adding the direct kernel (7.3–8.2 ms): the compaction costs more than it saves at one token start per five bytes", 0.6, 5.55, 6.6, 1.1, { size: 20 });
    big(s, "flat because", "the limiter does not depend on the list; the table is cache-resident at every size", 7.4, 5.55, 5.35, 1.1, { size: 20 });
    s.addNotes("[6:00] Where does the time go? At a thousand indicators the line table is 40 percent, the token scan 47, the hash match 8, the extraction 7. The two scans read and write a four-byte flag per corpus byte, eight bytes moved for every byte of log, while the hash kernel reads each byte once. The hash kernel runs at the equivalent of 45 gigabytes per second of corpus against a copy rate of 241: it is bound by the serial walk and the probe of every thread, not by bandwidth; shared-memory keys change nothing, the probes come from L1 and L2 anyway. So the limiter is the scan traffic, which does not depend on the list, and that is exactly why the pipeline is flat. The variant without compaction confirms it: drop the 16-millisecond scan, add an 8-millisecond kernel, and the pipeline goes from 33 to 20 milliseconds."); }

  // 8 result 3
  { const s = newSlide("CONTENT", "Results", "Result 3: the data rate, the copy, and the CPU");
    fig(s, "rate_vs_size.png", 0.6, 1.7, 6.6, 3.3);
    const rows = [["", "MB/s at 4M lines", "GB per day"],
                  ["GPU, no compaction, on the device", "5,760", "498"], ["GPU hash-set pipeline, on the device", "3,288", "284"],
                  ["GPU pipeline + pageable copy (4.6 GB/s)", "1,909", "165"], ["CPU, 4 tasks (4-core Xeon 2.1 GHz)", "1,089", "94"],
                  ["CPU, 2 tasks (Colab host, 1 core)", "316", "27"], ["CPU, 1 task", "283", "24"]];
    s.addTable(rows.map((r, i) => r.map((c, j) => ({ text: c, options: { bold: i === 0, align: j === 0 ? "left" : "right", fontSize: 10.5, color: i === 0 ? "FFFFFF" : HEX.dk1, fill: { color: i === 0 ? HEX.dk2 : (i % 2 ? "F3F8F6" : "FFFFFF") } } }))),
               { x: 7.4, y: 1.7, w: 5.35, colW: [3.05, 1.2, 1.1], rowH: 0.36, border: { type: "solid", color: HEX.accent2, pt: 0.5 }, fontFace: "Arial", margin: 0.04, objectName: "rate table" });
    big(s, "1.75× / 6.7×", "GPU with the copy against the 4-core CPU with four tasks / one task; 3.0× and 11.6× on the device", 0.6, 5.2, 4.0, { size: 20 });
    big(s, "1.92×, 3.63×", "CPU matcher with 2 and 4 tasks over 1: close to linear (1,000 indicators)", 4.75, 5.2, 3.85, { size: 20 });
    big(s, "≈ 7 cores", "what one T4 replaces once the transfer is counted; about 20 if the logs are already on the device", 8.75, 5.2, 4.0, { size: 20 });
    para(s, "The copy costs 0.7× the pipeline at 4M lines (11.3 GB/s pinned): not yet the wall, but the next one.", 0.6, 6.45, 12.1, 0.35, { size: 10.5, color: HEX.accent5 });
    s.addNotes("[7:00] The third result is the data rate, with a list of a thousand. On the device the pipeline runs at 3.3 gigabytes per second and the variant without compaction at 5.8. The pageable copy runs at 4.6 gigabytes per second and costs 0.7 times the pipeline, so with the copy the GPU keeps up with about 1.9 gigabytes per second, 165 terabytes a day. The tuned CPU reaches 1.1 gigabytes per second on four cores, 94 terabytes a day, 290 megabytes per second on one core, scaling almost linearly with tasks. So, honestly: with the copy counted the GPU is 1.75 times the four-core CPU and 6.7 times one core; on the device 3 and 11.6 times. One T4 replaces about seven cores of this class once the transfer is counted, about twenty if the logs are already there."); }

  // 9 security conclusion
  pres.addSection({ title: "Conclusion" });
  { const s = newSlide("CONTENT", "Conclusion", "What a defender should take from it");
    card(s, 0.6, 1.75, 6.0, 2.55); heading(s, "1. The algorithm first, the hardware second", 0.8, 1.85, 5.6);
    bullets(s, ["Any method whose cost grows with the list is unusable for a real feed: per-indicator GPU 1.9 s per million lines at 10,000; occursin on a core about 14 minutes (10 GB/day per core)",
                "A list-independent method makes the feed size free: 10,000 indicators at the rate of 10, on GPU and CPU",
                "The algorithm changes the capacity by 3–4 orders of magnitude; CPU vs GPU by 2–7×"], 0.8, 2.2, 5.6, 2.05, { size: 11.5 });
    card(s, 6.8, 1.75, 5.95, 2.55, { fill: "F3F8F6" }); heading(s, "2. The sizing rule", 7.0, 1.85, 5.5);
    bullets(s, ["One core: 290 MB/s, 25 TB/day. Four cores: 1.1 GB/s, 94 TB/day. One T4 with the copy: 1.9 GB/s, 165 TB/day; on the device 5.8 GB/s, 500 TB/day",
                "A 2 TB/day site (23 MB/s) is far below one core",
                "The GPU is needed above what the cores cover (~1 GB/s here) and keeps up to ~2 GB/s if the logs arrive that fast; otherwise storage or the network is the limit",
                "It pays when the logs are on the device anyway (Project 2’s entropy pass shares the corpus copy)"], 7.0, 2.2, 5.5, 2.05, { size: 11 });
    card(s, 0.6, 4.5, 6.0, 2.15); heading(s, "Limits", 0.8, 4.6, 5.6, { color: HEX.accent4 });
    bullets(s, ["Synthetic logs; whole tokens only (no substrings, no regular expressions)", "Cold indicators never hit: the cost of the list, not of the hits", "Julia on a shared 4-core host; a vectorised C++ matcher would narrow the GPU’s margin", "One Colab session on a 2018 T4; the line-table scan could still go (13 ms)"], 0.8, 4.95, 5.6, 1.65, { size: 11 });
    card(s, 6.8, 4.5, 5.95, 2.15); heading(s, "Ethical and legal notes", 7.0, 4.6, 5.5, { color: HEX.accent4 });
    bullets(s, ["Only self-generated data: RFC 5737 / 2544 ranges, .invalid names; nothing probed or collected", "In production, addresses and hostnames identify people: retention, purpose limitation, access control apply to logs and to match results", "Threat feeds carry sharing restrictions (TLP); a faster matcher changes none of this"], 7.0, 4.95, 5.5, 1.65, { size: 11 });
    s.addNotes("[8:00] What should a defender take from this? First, the method before the hardware: anything whose cost grows with the list is unusable for a real feed; a list-independent method makes the feed size free. The algorithm changes the capacity by three to four orders of magnitude, CPU against GPU by two to seven times. Second, the sizing rule: one core handles about 290 megabytes per second, 25 terabytes a day; four cores about a gigabyte per second; one T4 with the copy about two gigabytes per second, 165 terabytes a day, and 5.8 on the device. A two-terabyte-a-day site is far below one core; the GPU is needed above what the cores cover, and it pays when the logs are on the device anyway. The limits are on the slide: synthetic logs, whole tokens, one 2018 GPU. And the ethical side: only self-generated data here; in production addresses and hostnames identify people, so retention and access rules apply to logs and matches alike."); }

  // 10 demo and close
  { const s = newSlide("CONTENT", "Conclusion", "Live run and conclusions");
    card(s, 0.6, 1.75, 5.6, 4.9, { fill: "F3F8F6" }); heading(s, "The live run (Colab, Tesla T4)", 0.8, 1.85, 5.2);
    bullets(s, ["Started at slide 5: 125,000 lines, lists of 10, 1,000 and 10,000",
                "Validation of every method against the truth → Correct!",
                "Then the list-size sweep: GPU hash set, GPU without compaction, per-indicator kernel (to 1,000), CPU hash set, occursin (at 10)",
                "What to look at: the GPU pipeline times do not move from 10 to 10,000; the per-indicator time grows with the groups; the CPU times do not move either",
                "Same script, same checks, fewer repetitions (RP_REPS=20); the full runs are in results/"], 0.8, 2.2, 5.2, 4.3, { size: 11.5 });
    card(s, 6.4, 1.75, 6.35, 4.9); heading(s, "Conclusions", 6.6, 1.85, 6.0);
    bullets(s, ["Indicator matching with a token hash set is flat in the list size on the GPU: 30 M lines/s with the lecture-7 compaction, 49 M without, from 10 to 10,000 indicators; per-indicator methods are linear",
                "The limiter of the GPU pipeline is the scan traffic of the compaction, not the hash table: removing the token scan gives 1.6×",
                "A tuned CPU with the same algorithm reaches 1.1 GB/s on four cores; the T4 gives 1.9 GB/s with the copy, 5.8 GB/s on the device: one GPU ≈ seven cores once the transfer is counted",
                "Order of decisions for a SOC: a list-independent algorithm first; hardware only above the rate the cores cover, about 1 GB/s for four cores of this class",
                "Reproducible: Project.toml, Manifest.toml, one script, one notebook, Correct! before every number"], 6.6, 2.2, 6.0, 4.3, { size: 11.5 });
    s.addNotes("[9:00] This is the live run I started at slide 5, the same script on 125 thousand lines with lists of ten, a thousand and ten thousand: first the validation prints Correct, then the sweep. What to look at: the GPU pipeline times stay the same from ten to ten thousand, the per-indicator time grows with the groups, and the CPU times do not move either. To conclude: matching with a token hash set is flat in the list size, thirty million lines per second with the compaction, forty-nine without, while per-indicator methods are linear; the limiter of the pipeline is the scan traffic, not the table; a tuned CPU reaches a gigabyte per second on four cores and the T4 gives two with the copy and six on the device, so one GPU is about seven cores once the transfer is counted; and for a SOC the order is algorithm first, hardware only above what the cores cover. Everything is reproducible from one script and one notebook, with Correct printed before every number. Thank you; I am happy to take questions."); }

  // 11 backup
  pres.addSection({ title: "Backup" });
  { const s = newSlide("CONTENT", "Backup", "Backup: evidence and numbers to point at");
    const rows = [["Quantity", "Value"],
                  ["hash_match! kernel", "28 registers, 0 B shared, occupancy 100 %, 4 blocks/SM; PTX 111 instructions, 12 global loads, 0 atomics, 15 branches"],
                  ["probes per token", "1.41–2.37 (linear probing, load ≤ 0.5); shared keys 2.2–3.1 ms vs global 1.9–2.7 ms"],
                  ["table footprint", "16 B per slot: 0.5 KB at 10, 49 KB at 1,000, 512 KB at 10,000 (12 % of the 4 MB L2)"],
                  ["per-indicator kernel", "5.6 / 7.7 / 23.7 / 58.6 / 186.6 / 561.4 ms at 10 / 30 / 100 / 300 / 1,000 / 3,000; 5.94 ms per group"],
                  ["copies", "device-to-device 240.7 GB/s (read + write); host-to-device 4.6 GB/s pageable, 11.3 GB/s pinned; theoretical DRAM 320 GB/s"],
                  ["CPU 4-core Xeon, 1M lines", "1 task 0.31–0.41 s, 2 tasks 0.17–0.21 s, 4 tasks 0.086–0.113 s, flat from 10 to 10,000; occursin 0.80 / 2.5 / 8.0 / 24.8 s at 10 / 30 / 100 / 300"],
                  ["validation", "894 (line, indicator) pairs for every list and every method; 11 hand-made cases; test suite"],
                  ["device", "Tesla T4, 40 SMs, 14.56 GiB, CC 7.5, driver 580.82 / CUDA 13.3, CUDA.jl 6.5.1, Julia 1.12.7"]];
    s.addTable(rows.map((r, i) => r.map((c, j) => ({ text: c, options: { bold: i === 0 || j === 0, align: "left", fontSize: 10.5, color: i === 0 ? "FFFFFF" : HEX.dk1, fill: { color: i === 0 ? HEX.dk2 : (i % 2 ? "F3F8F6" : "FFFFFF") } } }))),
               { x: 0.6, y: 1.75, w: 12.15, colW: [2.6, 9.55], rowH: 0.5, border: { type: "solid", color: HEX.accent2, pt: 0.5 }, fontFace: "Arial", margin: 0.05, objectName: "evidence table" });
    s.addNotes("Backup slide for questions: the evidence the script produced."); }

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("written", OUT);
}
build().catch(e => { console.error(e); process.exit(1); });
