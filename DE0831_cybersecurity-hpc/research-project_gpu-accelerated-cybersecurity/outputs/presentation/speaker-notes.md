# Speaker notes: research project presentation (10 minutes + 5 minutes of questions)

Timings in brackets are cumulative. Start the live-run cell on Colab when slide 5 is up; show its output at slide 10. About 1,350 words: 10 minutes at a calm pace.


## Slide 1: Title slide

[0:00] Good afternoon. My project is topic 10, log indicator matching: how many log lines per second one GPU can match against a threat-intelligence list, and what happens when that list grows from ten entries to ten thousand. I worked alone, by agreement. Ten minutes, then questions; the live run is already started on Colab and I will show its output at the end.


## Slide 2: The question: what does the list cost?

[0:30] The question is about the cost of the list. A SOC gets a feed of thousands of indicators and must check every one against every log line; nearly all of them are cold. There are two families of matchers: those whose cost is per indicator and per line, and those that pay once per token whatever the list. My objective is a measurable one: lines per second on one GPU as the list grows from ten to ten thousand, against a tuned multithreaded CPU with the same algorithm, with the hits checked against the ground truth every time. The secondary questions are the data rate where the CPU stops keeping up, with the copy counted, and how many cores one T4 replaces.


## Slide 3: Data: the course corpus and lists that grow without changing the hits

[1:30] The data is the course corpus from the handout generator with my ID: a million lines, 119 megabytes, with twenty planted indicators that hit 894 lines, which is the truth file. The lists are built from the same seed: up to twenty they are subsets of the planted ones; above twenty I add cold indicators in the same two forms, addresses from the RFC 2544 benchmarking range and DGA-style .invalid hostnames, which cannot occur in the corpus. So the truth of every list is known exactly and only the list size changes; every method has to report the same 894 hits: that is a real feed, and a fair comparison. The rule is whole tokens, so 192.0.2.24 never matches inside 192.0.2.248.


## Slide 4: Methods: one list-independent GPU pipeline, three baselines

[2:30] The method is a token hash set. The corpus is one flat byte vector on the device; thread i owns byte i, so every warp reads 32 consecutive bytes. The lecture-7 pattern, flag per byte, inclusive scan, scatter, gives first the line table and then the token starts. Then one thread per token walks its bytes, computing the FNV-1a hash as it reads, and probes an open-addressing table of the indicators with linear probing; on a hash hit it compares the bytes. The cost is one pass whatever the list; the list only sets the table size, half a kilobyte at ten entries, half a megabyte at ten thousand. Three baselines: the same match without compaction, one thread per byte, to measure what the scan costs; the Project 2 kernel, one launch per 32 indicators, whose cost grows with the list; and the same hash-set algorithm on the CPU, tuned, one task per chunk, plus occursin per indicator.


## Slide 5: Validation first, then the lecture-7 timing

[4:00] Before any timing the run validates everything on the million-line corpus: the CPU matcher against the generator's truth, the library route, the GPU line table, and every GPU variant against the CPU matcher, for every list size; plus eleven hand-made cases for the edges. Only then it times, the way lecture 7 says: a warm-up, synchronize, then one CUDA elapsed per launch over a hundred launches, every step on its own, the pipeline as one timing, the copy as another; nothing is a difference of two timings, and nothing accumulates or garbage-collects inside a timed interval. The script also writes its own evidence. The live run on the screen starts now.


## Slide 6: Result 1: the hash-set pipeline is flat; everything per-indicator is linear

[4:45] The first result, on a million lines. The hash-set pipeline is flat: 33 milliseconds from ten to ten thousand indicators, thirty million lines per second; the match kernel alone is two to three milliseconds with two probes per token, so even the kernel that touches the table does not see the list. Without the token scan the pipeline is 20 milliseconds, fifty million lines per second, also flat. The per-indicator kernel is the straight line going down: 5.9 milliseconds per group of 32, so 5.6 milliseconds at ten indicators, 561 milliseconds at three thousand, and 1.9 seconds predicted at ten thousand, 56 times the hash set. With the line table it needs, the hash-set pipeline overtakes it between 30 and 100 indicators. The CPU hash set is flat too; occursin is the other straight line, 33 seconds at 300 indicators, 14 minutes per million lines at ten thousand.


## Slide 7: Result 2: the limiter is the scan traffic, not the hash table

[6:00] Where does the time go? At a thousand indicators the line table is 40 percent, the token scan 47, the hash match 8, the extraction 7. The two scans read and write a four-byte flag per corpus byte, eight bytes moved for every byte of log, while the hash kernel reads each byte once. The hash kernel runs at the equivalent of 45 gigabytes per second of corpus against a copy rate of 241: it is bound by the serial walk and the probe of every thread, not by bandwidth; shared-memory keys change nothing, the probes come from L1 and L2 anyway. So the limiter is the scan traffic, which does not depend on the list, and that is exactly why the pipeline is flat. The variant without compaction confirms it: drop the 16-millisecond scan, add an 8-millisecond kernel, and the pipeline goes from 33 to 20 milliseconds.


## Slide 8: Result 3: the data rate, the copy, and the CPU

[7:00] The third result is the data rate, with a list of a thousand. On the device the pipeline runs at 3.3 gigabytes per second and the variant without compaction at 5.8. The pageable copy runs at 4.6 gigabytes per second and costs 0.7 times the pipeline, so with the copy the GPU keeps up with about 1.9 gigabytes per second, 165 terabytes a day. The tuned CPU reaches 1.1 gigabytes per second on four cores, 94 terabytes a day, 290 megabytes per second on one core, scaling almost linearly with tasks. So, honestly: with the copy counted the GPU is 1.75 times the four-core CPU and 6.7 times one core; on the device 3 and 11.6 times. One T4 replaces about seven cores of this class once the transfer is counted, about twenty if the logs are already there.


## Slide 9: What a defender should take from it

[8:00] What should a defender take from this? First, the method before the hardware: anything whose cost grows with the list is unusable for a real feed; a list-independent method makes the feed size free. The algorithm changes the capacity by three to four orders of magnitude, CPU against GPU by two to seven times. Second, the sizing rule: one core handles about 290 megabytes per second, 25 terabytes a day; four cores about a gigabyte per second; one T4 with the copy about two gigabytes per second, 165 terabytes a day, and 5.8 on the device. A two-terabyte-a-day site is far below one core; the GPU is needed above what the cores cover, and it pays when the logs are on the device anyway. The limits are on the slide: synthetic logs, whole tokens, one 2018 GPU. And the ethical side: only self-generated data here; in production addresses and hostnames identify people, so retention and access rules apply to logs and matches alike.


## Slide 10: Live run and conclusions

[9:00] This is the live run I started at slide 5, the same script on 125 thousand lines with lists of ten, a thousand and ten thousand: first the validation prints Correct, then the sweep. What to look at: the GPU pipeline times stay the same from ten to ten thousand, the per-indicator time grows with the groups, and the CPU times do not move either. To conclude: matching with a token hash set is flat in the list size, thirty million lines per second with the compaction, forty-nine without, while per-indicator methods are linear; the limiter of the pipeline is the scan traffic, not the table; a tuned CPU reaches a gigabyte per second on four cores and the T4 gives two with the copy and six on the device, so one GPU is about seven cores once the transfer is counted; and for a SOC the order is algorithm first, hardware only above what the cores cover. Everything is reproducible from one script and one notebook, with Correct printed before every number. Thank you; I am happy to take questions.


## Slide 11: Backup: evidence and numbers to point at

Backup slide for questions: the evidence the script produced.
