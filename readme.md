# CMS Reviewer Assignment Optimiser  
A fairness-driven reviewer assignment tool with institution-conflict handling, automatic workload balancing, soft topic preferences, and co-reviewer limits.

This repository provides a Python-based Mixed Integer Programming (MIP) model for assigning pairs of reviewers to conference papers. The model enforces balanced workloads based on the number of papers and reviewers, prevents institutional conflicts, limits reviewer partnerships, and incorporates topic similarity as a soft objective without affecting feasibility.

The optimiser is built using **PuLP** with the CBC solver.

---

## Features

### ✔ Reviewer Assignment  
Each paper receives **exactly one reviewer pair** (two reviewers).

### ✔ Automatic Fairness Constraints  
Reviewer workload bounds are calculated automatically from:
- number of papers  
- number of reviewers  
- requirement that each paper needs two reviewers  

The optimiser computes:
```
L_min = floor( 2 × num_papers / num_reviewers )
L_max = ceil( 2 × num_papers / num_reviewers )
```
These values ensure that fairness constraints are **always feasible**.

### ✔ Institution Conflict Constraint  
No reviewer may be assigned to a paper authored by someone from the **same institution**.  
Pairs including such reviewers are forbidden for that paper.

### ✔ Co-Reviewer Limits  
Each reviewer collaborates with **exactly two distinct co-reviewers**, unless modified.

### ✔ Soft Topic Matching  
Topics do not constrain feasibility.  
They contribute to the objective by rewarding reviewer pairs that share topics with the paper.

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
| **Institution** | Author’s institution |
| **Choose topic(s) that best match the topics covered by your paper (choose up to 3 topics)** | Topics selected by the author, separated by comma and space |

### `reviewers.xlsx`  
Required columns:
| Column | Description |
|--------|-------------|
| **Name** | Reviewer’s name |
| **Institution** | Reviewer’s institution |
| **Choose topic(s) that fits best to your research field** | List of reviewer topics, separated by comma and space |

### Notes on Topic Format  
- Topics must be separated with **comma + space**, for example:  
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
| Console output | Co-reviewer partnership summary |

---

## Objective Structure

The optimisation maximises:

```
total_topic_matches
```

subject to:

- Automatically determined reviewer workload bounds  
- Exactly one pair per paper  
- No reviewer may review a paper from their own institution  
- Exactly two co-reviewers per reviewer  
- Integer feasibility for all assignment variables  

Topics never reduce feasibility; they only guide pair selection when multiple feasible solutions exist.

---

## Co-Reviewer Limit Rationale

Limiting each reviewer to **two collaborators**:
- supports efficient bilateral discussions  
- prevents overloaded reviewer networks  
- maintains balanced reviewer relationships  

---

## License

MIT License (see LICENSE file).

---

## Contact

For questions, improvements, or feature requests, please open an issue or submit a pull request on GitHub.
