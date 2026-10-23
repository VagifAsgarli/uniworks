# uniworks

Coursework of **Vagif Asgarli**, student ID **251ADM047**, Riga Technical University (RTU),
academic year 2026/27.

## Courses and assignments

| Course | Assignment | Due | Status |
|---|---|---|---|
| [DE0831 Cybersecurity Solutions in High-Performance Computing Environments](DE0831_cybersecurity-hpc/) | [Project 1: GPU Programming Fundamentals in Julia](DE0831_cybersecurity-hpc/project-1_gpu-fundamentals-julia/) | 23.10.2026 | measured, archive ready |

## Repository layout

Every course has its own folder, and every assignment its own folder inside it:

```
uniworks/
├── README.md                          student information and this index
└── <COURSECODE>_<short-name>/          one folder per course, e.g. DE0831_cybersecurity-hpc
    ├── README.md                      course name, lecturers, description, list of assignments
    └── <assignment>_<short-name>/      e.g. project-1_gpu-fundamentals-julia
        ├── README.md                  task, deadline, status, results summary, layout
        ├── materials/                 what the course provides: brief, guides, data
        ├── <code>/                    the work itself (named as the brief requires, e.g. DE0831_P1)
        ├── tools/                     helper scripts and notebooks that are not handed in
        └── outputs/                   everything a run produced: logs, raw results, and
            └── submission/            the exact file(s) handed in
```

Conventions:

- Folder names: lower case, words joined by `-`, parts joined by `_`; course folders start with
  the course code.
- Each assignment README starts with a table of issue date, due date, weight, defence and
  submission method, then a status checklist.
- Runs that produce data get their own folder under `outputs/`, named `<where>_<YYYY-MM-DD>`
  (e.g. `colab-t4_2026-10-23`), so earlier results are never overwritten.
- When a course or assignment is added, add a row to the table above and to the course README.
