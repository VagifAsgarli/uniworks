# uniworks

Coursework of **Vagif Asgarli**, student ID **251ADM047**, Riga Technical University (RTU),
academic year 2026/27.

## Courses and assignments

| Course | Assignment | Due | Status |
|---|---|---|---|
| [DE0831 Cybersecurity Solutions in High-Performance Computing Environments](DE0831_cybersecurity-hpc/) | [Project 1: GPU Programming Fundamentals in Julia](DE0831_cybersecurity-hpc/project-1_gpu-fundamentals-julia/) | 23.10.2026 | **graded 9.75/10**, defence passed |
| [DE0831 Cybersecurity Solutions in High-Performance Computing Environments](DE0831_cybersecurity-hpc/) | [Project 2: Applied Security on GPUs](DE0831_cybersecurity-hpc/project-2_applied-security-gpus/) | 27.11.2026 | track E implemented and validated; T4 run pending |
| [DE0831 Cybersecurity Solutions in High-Performance Computing Environments](DE0831_cybersecurity-hpc/) | [Research Project: GPU-Accelerated Cybersecurity](DE0831_cybersecurity-hpc/research-project_gpu-accelerated-cybersecurity/) | report 11.12.2026, defence 14.12.2026 | topic to choose |
| [DE1095 Digital Ethics and Artificial Intelligence Interaction](DE1095_digital-ethics-ai/) | [Project work: secure and ethical AI system — HR assistant "Atlase"](DE1095_digital-ethics-ai/project-work_secure-ethical-hr-assistant/) | 9.11.2026, 10:00 | deck and notes ready; to upload |

## Repository layout

Every course has its own folder, and every assignment its own folder inside it:

```
uniworks/
├── README.md                          student information and this index
└── <COURSECODE>_<short-name>/          one folder per course, e.g. DE0831_cybersecurity-hpc
    ├── README.md                      course name, lecturers, description, list of assignments
    ├── materials/                     course-wide material shared by all assignments:
    │                                  lectures/, group-exercises/, text-extracts/ (plain text of each file)
    └── <assignment>_<short-name>/      e.g. project-1_gpu-fundamentals-julia
        ├── README.md                  task, deadline, status, results summary, layout
        ├── materials/                 what the course provides for this assignment: brief, guides, data
        ├── notes/                     research and digests prepared for the work
        ├── <code>/                    the work itself (named as the brief requires, e.g. DE0831_P1)
        ├── tools/                     helper scripts and notebooks that are not handed in
        └── outputs/                   everything a run produced: logs, raw results, and
            └── submission/            the exact file(s) handed in
```

Conventions:

- Folder names: lower case, words joined by `-`, parts joined by `_`; course folders start with
  the course code.  Lecture files are named `week-NN_<lecturer>_<topic>`, group exercises
  `group-N_<system>` inside a `week-NN_<task>` folder.
- Raw uploads go to a temporary folder (e.g. `temp_loc_data/`) and are moved into this structure
  with `git mv`, so no file is lost and history is kept.
- Each assignment README starts with a table of issue date, due date, weight, defence and
  submission method, then a status checklist.
- Runs that produce data get their own folder under `outputs/`, named `<where>_<YYYY-MM-DD>`
  (e.g. `colab-t4_2026-10-23`), so earlier results are never overwritten.
- When a course or assignment is added, add a row to the table above and to the course README.
