# Time complexity with big-O

Big-O describes how the number of steps grows as the input size \(n\) grows. It is a statement about growth, not about the exact millisecond time on one machine.

## Learning objectives

- Count dominant steps in a short block of pseudocode.
- Distinguish constant, linear, and quadratic growth.
- Use a trace table to justify a big-O claim without a coding provider.

## Worked example

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

## Common mistakes

- Confusing best-case with big-O worst-case growth.
- Calling every nested loop \(O(n)\) because “it uses n”.
- Measuring one laptop’s clock time and treating it as the complexity class.

## Recap

Identify the loops that grow with \(n\), multiply the dominant counts, and drop lower-order terms. This reading check does not require running code.
