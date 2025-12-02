# CMS Reviewer Assignment Optimiser  
A fair, topic-aware reviewer assignment tool with co-reviewer limits.

This repository contains a Python-based optimisation model for assigning two reviewers to each paper submitted to the CIRP-CMS conference (or any similar academic event). The model aims to balance reviewer workload, encourage topic alignment, and restrict the number of co-reviewer partnerships per reviewer to facilitate efficient bilateral discussions.

The core solver is implemented using Mixed Integer Linear Programming (MILP) via **pulp** and the CBC solver.

---

## Overview

The script performs the following tasks:

1. **Reads metadata** from two Excel files:
   - `papers.xlsx`
   - `reviewers.xlsx`

2. **Parses topics** from authors and reviewers using a safe comma-and-space split  
   (`", "`), ensuring compound topics such as  
   *Industry 4.0, Industry 5.0 and beyond* remain a **single topic**.

3. **Assigns exactly two reviewers per paper** by selecting reviewer pairs.

4. **Enforces constraints**:
   - Each reviewer may review **at most 10 papers**.
   - Each reviewer may collaborate with **no more than 2 distinct co-reviewers**.
   - Topic matching is **desirable** (rewarded), but **not required**.
   - **Fairness** is the primary objective: minimise the maximum workload (`L_max`).
   - **Topic alignment** is a secondary objective.

5. **Generates output files**:
   - `assignment_output.xlsx` – final reviewer assignments  
   - `reviewer_workloads.xlsx` – workload summary  
   - `topic_reviewer_utilisation.xlsx` – topic utilisation across reviewers  
   - `reviewer_workloads.png` – workload visualisation  
   - `topic_coverage_heatmap.png` – topic heatmap  
   - Plus co-reviewer summaries printed to console

---

## Input File Format

### `papers.xlsx`

Must contain the following columns:

| Column Name | Description |
|-------------|-------------|
| **Paper Title** | Title of the submitted paper |
| **Name** | Corresponding author |
| **Choose topic(s) that best match the topics covered by your paper (choose up to 3 topics)** | Topics selected by the author |

**Topic format:**  
Topics must be separated only by **comma + space**, for example:

```
Digital Twin functionalities and strategies in manufacturing, Industry 4.0, Industry 5.0 and beyond
```

Notes:
- The parser preserves compound topics containing internal commas.
- Do **not** change separators to semicolons or other formats.

---

### `reviewers.xlsx`

Must contain the following columns:

| Column Name | Description |
|-------------|-------------|
| **Name** | Reviewer’s full name |
| **Choose topic(s) that fits best to your research field** | Reviewer-selected topics, in the same comma+space-separated format |

**Example:**  
```
Artificial Intelligence (AI) and Machine Learning (ML), Digital Twin functionalities and strategies in manufacturing, Sustainable and circular manufacturing
```

---

## How to Run

### 1. Install dependencies

```bash
pip install pandas pulp matplotlib
```

CBC is bundled with `pulp` on many systems.  
If not, see installation instructions here:  
https://coin-or.github.io/pulp/installation.html

### 2. Place `papers.xlsx` and `reviewers.xlsx` in the same directory as the solver script.

### 3. Run the optimiser

```bash
python assign_with_coreviewer_limits.py
```

### 4. Outputs generated automatically

- `assignment_output.xlsx`  
- `reviewer_workloads.xlsx`  
- `reviewer_workloads.png`  
- `topic_reviewer_utilisation.xlsx`  
- `topic_coverage_heatmap.png`

Console messages also report:
- solver status  
- reviewer workloads  
- co-reviewer pairings  

---

## Objective Structure

The solver uses lexicographic optimisation:

### **Primary objective:**  
Minimise  
L_max = max_r workload[r]

to achieve reviewer fairness.

### **Secondary objective:**  
Maximise topic alignment across assignments.

Implemented as:

```
minimise   10000 * L_max  -  topic_score
```

The weighting ensures fairness takes precedence over topic matching.

---

## Co-Reviewer Limit Rationale

To support consistent bilateral discussions, each reviewer is restricted to pairing with **no more than two** distinct co-reviewers across all assigned papers.  
This ensures the reviewer collaboration network remains manageable, forming simple paths or small cycles rather than large, complex graphs.


---

## Contact

For questions, comments, or improvements, please open an issue or pull request on GitHub.
