# Checking a big-O claim

Big-O names how the number of steps grows with n. Count the dominant steps, then drop constants and lower-order terms.

## Learning objectives

- Multiply nested loops that each run n times.
- Count halvings as logarithmic.
- Keep a fixed setup from changing a linear loop into another class.
- Separate a closed formula from a loop that computes the same value.

## Worked algorithm

```text
for i ← 1 to n:
  for j ← 1 to n:
    constant work
```

Dry run n = 3: the body runs 9 times. The growth is O(n²). Extra space is O(1) when the body only updates a counter.

A loop that replaces x with floor(x/2) until x is 0 is O(log n). Dry run x = 8: 8, 4, 2, 1, 0.

## Formula and loop

The sum 1 + 2 + … + n equals n(n+1)/2.

The formula does a fixed amount of arithmetic, so it is O(1). Adding the integers in a loop is O(n). Both give 10 when n = 4. The costs are different.

## Common mistakes

- Calling every nested loop linear.
- Treating O(n + 20) as a different class from O(n).
- Using the best case of a search as the worst-case class.

## Related practice

The five complexity questions on this lesson. Read the published lesson “Time complexity with big-O” (dsa-complexity) for the pair-counting trace. This article is the checklist for the sprint questions.
