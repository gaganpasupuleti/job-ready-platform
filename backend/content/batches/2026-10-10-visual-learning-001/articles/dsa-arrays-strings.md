# Arrays and strings

## Understand

An array stores values in contiguous indexed slots. A string is a sequence of characters that you can scan from left to right. Many interview warm-ups are “walk the sequence once and keep a running answer”.

## Visualize

![Array a, b, c, d with left on index 1 and right on index 4, then the reversed array d, c, b, a](/learning-visuals/dsa/array-reversal.svg "Swap the ends, then move both pointers inward. [a, b, c, d] becomes [d, c, b, a].")

Left starts at the first slot and right starts at the last. After each swap, left moves right by one and right moves left by one.

## Learning objectives

- Index from the start of an array without inventing off-by-one holes.
- Scan a string once while tracking a frequency or a previous character.
- Use a trace table instead of a coding provider to verify the idea.

## Walk through

Worked example: reverse in place idea.

```text
REVERSE(A):
  left ← 1
  right ← length(A)
  while left < right:
    swap A[left] and A[right]
    left ← left + 1
    right ← right - 1
```

Trace for `A = [a, b, c, d]`:

| left | right | array after swap |
| --- | --- | --- |
| 1 | 4 | [d, b, c, a] |
| 2 | 3 | [d, c, b, a] |
| 3 | 2 | stop |

## Worked example: first repeated character

```text
FIRST_REPEAT(S):
  seen ← empty set
  for each character ch in S:
    if ch is in seen:
      return ch
    add ch to seen
  return none
```

For `S = "abca"`, the answer is `a` after the fourth character. The scan is \(O(n)\) time with an auxiliary set.

## Review

## Common mistakes

- Starting indexes at the wrong end and dropping the middle element.
- Scanning twice when one pass is enough.
- Mutating a string while counting characters and then trusting the original length.

## Recap

Write the invariant (“everything outside left..right is already final”), then fill a tiny trace table. Conceptual practice here does not need a language runtime.
