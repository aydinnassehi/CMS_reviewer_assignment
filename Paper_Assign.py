import itertools
import pandas as pd
import pulp

# ======================================================
# 1. Load data
# ======================================================

PAPERS_FILE = "papers.xlsx"
REVIEWERS_FILE = "reviewers.xlsx"

papers = pd.read_excel(PAPERS_FILE)
reviewers = pd.read_excel(REVIEWERS_FILE)

# Required columns (matching your files)
PAPER_TITLE = "Paper Title"
PAPER_AUTHOR = "Name"
PAPER_TOPICS_COL = "Choose topic(s) that best match the topics covered by your paper (choose up to 3 topics)"
REVIEWER_NAME = "Name"
REVIEWER_TOPICS_COL = "Choose topic(s) that fits best to your research field"

papers = papers.reset_index(drop=True)
reviewers = reviewers.reset_index(drop=True)

paper_ids = list(papers.index)
reviewer_ids = list(reviewers.index)

# All reviewer pairs
reviewer_pairs = [(r1, r2) for r1, r2 in itertools.combinations(reviewer_ids, 2)]

print(f"Loaded {len(paper_ids)} papers and {len(reviewer_ids)} reviewers.")
print(f"Total reviewer pairs: {len(reviewer_pairs)}")


# ======================================================
# 2. Topic parsing (SOFT preference only)
# ======================================================

def split_topics(text):
    if pd.isna(text):
        return []
    return [t.strip() for t in str(text).split(",")]

paper_topics = {
    i: set(split_topics(papers.loc[i, PAPER_TOPICS_COL]))
    for i in paper_ids
}

reviewer_topics = {
    r: set(split_topics(reviewers.loc[r, REVIEWER_TOPICS_COL]))
    for r in reviewer_ids
}

# Topic overlap score for each paper × pair
topic_score = {}
for i in paper_ids:
    pt = paper_topics[i]
    for pair in reviewer_pairs:
        r1, r2 = pair
        R = reviewer_topics[r1] | reviewer_topics[r2]
        score = len(pt.intersection(R))
        topic_score[(i, pair)] = score


# ======================================================
# 3. Model definition
#    - FAIRNESS AS HARD CONSTRAINTS
#    - MAXIMISE TOPIC ALIGNMENT
# ======================================================

prob = pulp.LpProblem("Reviewer_Assignment", pulp.LpMaximize)

# Binary assignment: assign[i][(r1,r2)] = 1
assign = {
    i: {
        pair: pulp.LpVariable(f"assign_{i}_{pair[0]}_{pair[1]}",
                              lowBound=0, upBound=1, cat="Binary")
        for pair in reviewer_pairs
    }
    for i in paper_ids
}

# Whether a pair is used at least once
pair_used = {
    pair: pulp.LpVariable(f"pair_used_{pair[0]}_{pair[1]}",
                          lowBound=0, upBound=1, cat="Binary")
    for pair in reviewer_pairs
}

# Workload per reviewer
workload = {
    r: pulp.LpVariable(f"load_{r}", lowBound=0, cat="Integer")
    for r in reviewer_ids
}


# ======================================================
# 4. Constraints
# ======================================================

# Each paper gets exactly one pair
for i in paper_ids:
    prob += pulp.lpSum(assign[i][pair] for pair in reviewer_pairs) == 1

# Workload definition: count how many papers each reviewer sees
for r in reviewer_ids:
    prob += workload[r] == pulp.lpSum(
        assign[i][pair]
        for i in paper_ids
        for pair in reviewer_pairs
        if r in pair
    )

# Hard load constraints: fairness band

# ======================================================
# Automatic workload fairness based on paper count
# ======================================================

num_papers = len(paper_ids)
num_reviewers = len(reviewer_ids)

# Total reviewer-load required = 2 per paper
total_load = 2 * num_papers
average_load = total_load / num_reviewers

import math
L_min = math.floor(average_load)
L_max = math.ceil(average_load)

print(f"Automatic workload bounds: {L_min} to {L_max} per reviewer")

for r in reviewer_ids:
    prob += workload[r] >= L_min
    prob += workload[r] <= L_max


# Bind assign -> pair_used
for pair in reviewer_pairs:
    for i in paper_ids:
        prob += pair_used[pair] >= assign[i][pair]

# Each reviewer has exactly 2 distinct co-reviewers
for r in reviewer_ids:
    prob += pulp.lpSum(
        pair_used[pair]
        for pair in reviewer_pairs
        if r in pair
    ) == 2

# ======================================================
# 4b. Prevent authors from reviewing their own papers
# ======================================================

# Build a reverse lookup: reviewer name -> reviewer index
reviewer_name_to_id = {
    reviewers.loc[r, REVIEWER_NAME].strip(): r
    for r in reviewer_ids
}

for p in paper_ids:
    author_name = str(papers.loc[p, PAPER_AUTHOR]).strip()

    # If author's name does not appear among reviewers, skip
    if author_name not in reviewer_name_to_id:
        continue

    author_id = reviewer_name_to_id[author_name]

    # Prohibit any pair containing the author
    for pair in reviewer_pairs:
        if author_id in pair:
            prob += assign[p][pair] == 0


    prob += workload[r] <= L_max  # tighten upper bound to the known feasible L_max

# ======================================================
# 5. Objective: maximise topic alignment (SOFT)
# ======================================================

topic_term = pulp.lpSum(
    assign[i][pair] * topic_score[(i, pair)]
    for i in paper_ids
    for pair in reviewer_pairs
)

prob += topic_term   # maximise total topic overlap


# ======================================================
# 6. Solve with an optional 180-second limit
# ======================================================

solver = pulp.PULP_CBC_CMD(
    msg=1,
    options=["sec=180"]  # hard time cap
)

prob.solve(solver)

print("\nSolver status:", pulp.LpStatus[prob.status])

# If no integer solution found, say so explicitly and stop cleanly
if pulp.LpStatus[prob.status] not in ("Optimal", "Integer Feasible"):
    print("No integer-feasible solution found within the time limit.")
else:
    print("Objective (total topic matches):", pulp.value(topic_term))


# ======================================================
# 7. Extract assignments (only if feasible)
# ======================================================

assignments = []

for i in paper_ids:
    chosen = None
    for pair in reviewer_pairs:
        val = pulp.value(assign[i][pair])
        if val is not None and abs(val - 1) < 1e-5:
            chosen = pair
            break

    if chosen is None:
        print(f"WARNING: paper {i} has no chosen pair.")
        continue

    r1, r2 = chosen

    # topic reporting for this assignment
    pt = paper_topics[i]
    rt = reviewer_topics[r1] | reviewer_topics[r2]
    shared = pt.intersection(rt)
    shared_topics = ", ".join(sorted(shared)) if shared else ""

    assignments.append({
        "Paper ID": i,
        "Paper Title": papers.loc[i, PAPER_TITLE],
        "Author": papers.loc[i, PAPER_AUTHOR],
        "Reviewer 1": reviewers.loc[r1, REVIEWER_NAME],
        "Reviewer 2": reviewers.loc[r2, REVIEWER_NAME],
        "Topic matches (count)": len(shared),
        "Shared Topics": shared_topics
    })

df_assign = pd.DataFrame(assignments)
df_assign.to_excel("assignment_output.xlsx", index=False)
print("Saved assignment_output.xlsx")


# ======================================================
# 8. Workload summary
# ======================================================

df_load = pd.DataFrame([
    {
        "Reviewer ID": r,
        "Reviewer Name": reviewers.loc[r, REVIEWER_NAME],
        "Workload": float(pulp.value(workload[r])) if pulp.value(workload[r]) is not None else None
    }
    for r in reviewer_ids
])

df_load.to_excel("reviewer_workloads.xlsx", index=False)
print("Saved reviewer_workloads.xlsx")


# ======================================================
# 9. Co-reviewer relationships
# ======================================================

print("\nCo-reviewer relationships:")
for r in reviewer_ids:
    partners = []
    for pair in reviewer_pairs:
        if pulp.value(pair_used[pair]) is not None and abs(pulp.value(pair_used[pair]) - 1) < 1e-5 and r in pair:
            partners.append(pair[0] if pair[1] == r else pair[1])
    names = [reviewers.loc[x, REVIEWER_NAME] for x in partners]
    print(f"{reviewers.loc[r, REVIEWER_NAME]} -> {names}")
