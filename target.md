# Project Description

In the **Knapsack problem**, we are given `n` items with profits `p_1, …, p_n` and weights `w_1, …, w_n`, and a knapsack with capacity `c`. Our goal is to find a subset of items so that their total weight does not exceed `c` and their total profit is maximized.

This problem can be solved in `Θ(nc)` time using standard dynamic programming. For `0 ≤ i ≤ n` and `0 ≤ j ≤ c`, let `P[i][j]` be the maximum profit one can achieve using the first `i` items and a knapsack with capacity `j`. (For simplicity, we assume that `P[i][j] = −∞` if `j < 0`.) We have that

```
P[0][j] = 0                                             for all j
P[i][j] = max{ P[i−1][j], P[i−1][j−w_i] + p_i }         for all i ≥ 1 and all j
```

The recurrence can be solved in `Θ(nc)` time using two `for`-loops. Note that even in the best case, this algorithm needs as much as `Θ(nc)` time, and this is unpleasant in practice.

**Chapter 3.4** of the book in the Reference provides an alternative implementation of the dynamic programming algorithm, which has a better best-case running time when combined with a pruning idea.

**Chapter 3.5** of the book provides an idea for further improvement of the dynamic programming algorithm. You may implement it and compare it to the other two algorithms. Bonus will be granted depending on the quality of your work.

## Requirements

You are required to do the following:

1. Read chapter 3.4 & 3.5 of the book, and implement the algorithms.
2. Conduct experiments to compare the performance of these algorithms with the original DP we present in class.

For simplicity, we are only interested in the **optimal value** (rather than the optimal solution) of the knapsack problems considered in this project.

## Bonus

There is also an `O(n + w³)`-time algorithm, where `w` refers to the maximum item weight. See [docs/method.pdf](docs/method.pdf) for reference. You may implement this algorithm as well.

## Reference

H. Kellerer, U. Pferschy, D. Pisinger. 2004. *The Knapsack Problems*. Springer. (CH3.4&3.5.pdf, docs/Knapsack....pdf)

## Notation of the Book

In the above book:

- `w_j` and `p_j` are the weight and the profit (value) of item `j`.
- **DP-1** is the algorithm we present in class.
- `z_j(d)` is the maximum value we can achieve with capacity `d` when considering only the first `j` items.

## Grading Policy

### Programming and Testing

| Item | Points |
| --- | --- |
| Implement the main algorithms | 6 pts. |
| Write a test of performance program | 1 pt. |
| Generate test data | 1 pt. |

All the codes must be sufficiently commented.

### Report

| Item | Points |
| --- | --- |
| Cover page and introduction | 1 pt. |
| Problem description | 1 pt. |
| Algorithm description and analysis | 2 pts. |
| Experiment results and analysis | 7 pts. |
| Writing style | 1 pt. |

### Bonus

Implement and test the `O(n + w³)`-time algorithm.

> **Note:** Anyone who does an excellent job on answering the Bonus question will gain an extra point.
