# Linear and binary search

Linear search checks indexes in order. Binary search discards half of a sorted array after each comparison.

## Learning objectives

- Count the comparisons linear search makes before a hit.
- State the worst case when the target is missing: every cell is checked.
- Trace binary search with one mid formula on a sorted array.
- Refuse binary search on unsorted data.

## Worked algorithm: linear search

Start at the first cell. Compare. Stop on a match. If the loop ends, the target is absent.

Dry run of 9 in [4, 1, 9, 7]: compare 4, compare 1, compare 9, return the third cell's index.

Time: O(1) best case when the first cell matches, Θ(n) worst case when it is missing or last. Space O(1).

Edge case: an empty array is absent without a comparison.

## Worked algorithm: binary search

The array must be sorted. low starts at the first index. high starts at the last. mid = low + floor((high−low)/2).

If the middle equals the target, return it. If the target is greater, set low = mid + 1. If it is smaller, set high = mid − 1. Stop when low passes high.

Dry run of 6 in [2, 4, 6, 8, 10]: mid index 2 holds 6, so the search returns 2.

Dry run of 7 in [1, 3, 5, 7, 9, 11]: middle values 5, then 9, then 7. Return the index of 7.

Time O(log n). Iterative extra space O(1). A recursive form uses O(log n) stack space.

Edge cases: empty input is absent. An unsorted array can discard the half that holds the target, so the result is not reliable. The low + (high−low)//2 form avoids adding two huge indexes in fixed-width arithmetic.

## Related practice

The five searching questions on this lesson. In the DSA practice list, the coding problems are named linear-search and binary-search. The published complexity lesson explains why halving is logarithmic. It does not replace this trace.
