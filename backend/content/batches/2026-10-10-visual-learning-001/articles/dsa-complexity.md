# Time complexity with big-O

## Understand

Big-O describes how the number of steps grows as the input size \(n\) grows. It is a statement about growth, not about the exact millisecond time on one machine.

## Visualize

![Grouped bars comparing a single pass of n steps with pair counts of 1, 6, and 28 at n = 2, 4, and 8](/learning-visuals/dsa/complexity-growth.svg "A single pass grows with n. Pair counting is n(n−1)/2: 1, 6, and 28 steps at n = 2, 4, and 8.")

At n = 2 the pair count is still small. By n = 8 it is 28, while one pass over the input is 8.

## Learning objectives

- Count dominant steps in a short block of pseudocode.
- Distinguish constant, linear, and quadratic growth.
- Use a trace table to justify a big-O claim without a coding provider.

## Walk through

Worked example.

```text
COUNT_PAIRS(A):
  count ← 0
  for i ← 1 to n:
    for j ← i+1 to n:
      count ← count + 1
  return count
```

Outer loop runs about \(n\) times. Inner loop length shrinks, but the total pairs are about \(n(n-1)/2\), which is quadratic. Big-O is \(O(n^2)\).

| n | Approximate steps | Pattern |
| --- | --- | --- |
| 2 | 1 | grows faster than n |
| 4 | 6 | roughly n²/2 |
| 8 | 28 | still ~n² |

A single loop that visits each element once is \(O(n)\). Two independent nested loops over the full range are \(O(n^2)\).

## Review

## Common mistakes

- Confusing best-case with big-O worst-case growth.
- Calling every nested loop \(O(n)\) because “it uses n”.
- Measuring one laptop’s clock time and treating it as the complexity class.

## Recap

Identify the loops that grow with \(n\), multiply the dominant counts, and drop lower-order terms. This reading check does not require running code.
