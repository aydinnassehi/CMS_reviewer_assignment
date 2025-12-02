"""
Reviewer assignment with:
 - Exactly two reviewers per paper (via pairs)
 - Reviewer workload <= 10
 - Reviewer may have at most 2 co-reviewers overall
 - Soft topic matching (rewarded but not required)
 - Fairness first (minimise maximum workload)
 - Topic alignment second (maximise topic reward)
"""

import pandas as pd
from itertools import combinations
from collections import Counter, defaultdict
import pulp
import matplotlib.pyplot as plt


# =========================================================
# 1. Load data
# =========================================================
papers = pd.read_excel("papers.xlsx")
reviewers = pd.read_excel("reviewers.xlsx")

# Column names
paper_title_col = "Paper Title"
paper_author_col = "Name"
paper_topic_col = "Choose topic(s) that best match the topics covered by your paper (choose up to 3 topics)"

reviewer_name_col = "Name"
reviewer_topic_col = "Choose topic(s) that fits best to your research field"


# =========================================================
# 2. Parse topics correctly
# =========================================================
def extract_topics(x):
    if pd.isna(x):
        return []
    return [t.strip() for t in str(x).split(", ") if t.strip()]

paper_ids = list(papers.index)
reviewer_ids = list(reviewers.index)

paper_topics = {i: extract_topics(papers.loc[i, paper_topic_col]) for i in paper_ids}
reviewer_topics = {j: extract_topics(reviewers.loc[j, reviewer_topic_col]) for j in reviewer_ids}

topic_match = {
    (i, j): len(set(paper_topics[i]) & set(reviewer_topics[j])) > 0
    for i in paper_ids for j in reviewer_ids
}

reviewer_pairs = list(combinations(reviewer_ids, 2))


# =========================================================
# 3. Model
# =========================================================
prob = pulp.LpProblem("ReviewerAssignment_SoftTopics", pulp.LpMinimize)

# assign[i][pair] = 1 if paper i is reviewed by the pair (r1,r2)
assign = pulp.LpVariable.dicts(
    "assign", (paper_ids, reviewer_pairs), 0, 1, cat="Binary"
)

# pair_used[pair] = 1 if that pair is used for at least one paper
pair_used = pulp.LpVariable.dicts(
    "pair_used", reviewer_pairs, 0, 1, cat="Binary"
)

# workload[r] = number of papers reviewer r is assigned
workload = {
    r: pulp.LpVariable(f"load_{r}", lowBound=0, cat="Integer")
    for r in reviewer_ids
}

# max workload (fairness)
L_max = pulp.LpVariable("L_max", lowBound=0, cat="Integer")


# =========================================================
# 4. Constraints
# =========================================================

# 4.1 Assign => pair_used
for pair in reviewer_pairs:
    for i in paper_ids:
        prob += assign[i][pair] <= pair_used[pair]

# 4.2 Each paper gets exactly one pair
for i in paper_ids:
    prob += pulp.lpSum(assign[i][pair] for pair in reviewer_pairs) == 1

# 4.3 Workload definition
for r in reviewer_ids:
    prob += workload[r] == pulp.lpSum(
        assign[i][pair]
        for i in paper_ids
        for pair in reviewer_pairs
        if r in pair
    )

# 4.4 Workload upper bound
for r in reviewer_ids:
    prob += workload[r] <= 10

# 4.5 Fairness: link all workloads to L_max
for r in reviewer_ids:
    prob += workload[r] <= L_max

# 4.6 Co-reviewer limit: each reviewer may collaborate with <= 2 other reviewers
for r in reviewer_ids:
    prob += pulp.lpSum(
        pair_used[pair] for pair in reviewer_pairs if r in pair
    ) <= 2


# =========================================================
# 5. Soft topic reward
# =========================================================
topic_score = {}
for i in paper_ids:
    for (r1, r2) in reviewer_pairs:
        topic_score[(i, (r1, r2))] = (
            int(topic_match[(i, r1)]) + int(topic_match[(i, r2)])
        )

topic_term = pulp.lpSum(
    assign[i][pair] * topic_score[(i, pair)]
    for i in paper_ids
    for pair in reviewer_pairs
)

# Lexicographic objective:
#   Minimise L_max * BIG - topic_term
BIG = 10000

prob += L_max * BIG - topic_term


# =========================================================
# 6. Solve
# =========================================================
solver = pulp.PULP_CBC_CMD(msg=1)
prob.solve(solver)

print("\nSolver status:", pulp.LpStatus[prob.status], "\n")


# =========================================================
# 7. Extract assignment
# =========================================================
assigned_pair_for_paper = {}
rows = []

for i in paper_ids:
    chosen = [pair for pair in reviewer_pairs if pulp.value(assign[i][pair]) == 1]
    if len(chosen) != 1:
        print(f"WARNING: Paper {i} has {len(chosen)} chosen pairs (expected 1)")
        continue
    pair = chosen[0]
    r1, r2 = pair
    assigned_pair_for_paper[i] = pair

    shared = set(paper_topics[i]) & set(reviewer_topics[r1]) & set(reviewer_topics[r2])

    rows.append({
        "Paper Title": papers.loc[i, paper_title_col],
        "Author": papers.loc[i, paper_author_col],
        "Reviewer 1": reviewers.loc[r1, reviewer_name_col],
        "Reviewer 2": reviewers.loc[r2, reviewer_name_col],
        "Shared Topics (if any)": ", ".join(sorted(shared)),
    })

assignment_df = pd.DataFrame(rows)
assignment_df.to_excel("assignment_output.xlsx", index=False)
print("Saved assignment_output.xlsx")


# =========================================================
# 8. Workload summary
# =========================================================
computed_workload = Counter()
for i,pair in assigned_pair_for_paper.items():
    (r1,r2)=pair
    computed_workload[r1]+=1
    computed_workload[r2]+=1

workload_df = pd.DataFrame([
    {
        "Reviewer": reviewers.loc[r, reviewer_name_col],
        "Papers": computed_workload[r]
    }
    for r in reviewer_ids
])

workload_df.to_excel("reviewer_workloads.xlsx", index=False)
print("Saved reviewer_workloads.xlsx")


# =========================================================
# 9. Co-reviewer sets
# =========================================================
co_reviewers = defaultdict(set)
for pair in reviewer_pairs:
    if pulp.value(pair_used[pair]) >= 0.5:
        r1, r2 = pair
        co_reviewers[r1].add(r2)
        co_reviewers[r2].add(r1)

print("\nCo-reviewer relationships:")
for r in reviewer_ids:
    print(
        reviewers.loc[r, reviewer_name_col],
        "->",
        [reviewers.loc[x, reviewer_name_col] for x in co_reviewers[r]]
    )
