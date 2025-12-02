# CMS Reviewer Assignment Optimiser  
A fairness‑driven reviewer assignment tool with soft topic preferences and co‑reviewer limits.

This repository provides a Python‑based Mixed Integer Programming (MIP) model for assigning pairs of reviewers to conference papers. The model enforces balanced workloads, limits reviewer partnerships, and incorporates topic similarity as a *soft* objective without affecting feasibility.

The optimiser is built using **PuLP** with the CBC solver.

---

## Features

### ✔ Reviewer Assignment  
Each paper receives **exactly one reviewer pair** (two reviewers).

### ✔ Fairness Constraints  
Each reviewer is assigned between **6 and 9 papers**, based on known feasibility.

### ✔ Co‑Reviewer Limits  
Each reviewer collaborates with **no more than 2 distinct co‑reviewers**.

### ✔ Soft Topic Matching  
Topics **do not constrain** feasibility. Instead, they improve solution quality by giving a score bonus when paper–reviewer topics overlap.

### ✔ Flexible Objective  
The optimisation problem **maximises total topic matches** while respecting all fairness and structural constraints.

---

## Input File Format

The tool expects two Excel files placed in the working directory:

### `papers.xlsx`  
Required columns:
| Column | Description |
|--------|-------------|
| **Paper Title** | Title of the manuscript |
| **Name** | Author name |
| **Choose topic(s) that best match the topics covered by your paper (choose up to 3 topics)** | Topics selected by the author, separated by comma and space |

### `reviewers.xlsx`  
Required columns:
| Column | Description |
|--------|-------------|
| **Name** | Reviewer's name |
| **Choose topic(s) that fits best to your research field** | List of reviewer topics, separated by comma and space |

### Notes on Topic Format  
- Topics **must** be separated with **comma + space**, for example:  
  ```
  Digital Twin functionalities and strategies in manufacturing, Industry 4.0
  ```
- Compound topics containing internal commas are supported.

---

## How to Run

### 1. Install Dependencies
```bash
pip install pandas pulp
```

CBC is bundled with PuLP on many platforms.  
If unavailable, install from:  
https://coin-or.github.io/pulp/installation.html

### 2. Place Required Files  
Ensure the working directory contains:
```
papers.xlsx
reviewers.xlsx
Paper_Assign.py
```

### 3. Run the Optimiser
```bash
python Paper_Assign.py
```

### 4. Outputs Generated

| Output File | Contents |
|-------------|----------|
| `assignment_output.xlsx` | Reviewer pair assigned to each paper, including topic match information |
| `reviewer_workloads.xlsx` | Number of papers assigned to each reviewer |
| Console output | Co‑reviewer partnership summary |

The tool prints any warnings about unassigned papers or structural issues.

---

## Objective Structure

The optimisation maximises:

```
total_topic_matches
```

subject to:

- Reviewer workload: 6–9 papers  
- Exactly one pair per paper  
- Max 2 co‑reviewers per reviewer  
- Integer feasibility for all assignment variables  

Topics never reduce feasibility; they only guide pair selection when multiple feasible solutions exist.

---

## Co‑Reviewer Limit Rationale

Limiting each reviewer to **no more than two** collaborators:

- supports efficient bilateral discussions,  
- prevents overloaded reviewer networks,  
- ensures partner diversity without fragmentation.

---

## License

MIT License (see LICENSE file).

---

## Contact

For questions, improvements, or feature requests, please open an issue or submit a pull request on GitHub.
