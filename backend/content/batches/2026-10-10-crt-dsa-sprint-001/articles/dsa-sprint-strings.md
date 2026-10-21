# Scanning a string

A string is a sequence of characters with indexes. In this lesson the first character is index 0.

## Learning objectives

- Reverse by swapping the ends or by writing a new string from the end.
- Count vowels with one pass.
- Test a palindrome and an anagram from character counts or two pointers.

## Worked algorithm: reverse

Set left at the first character and right at the last. Swap, then move inward, until left meets or passes right.

Dry run of "ab": one swap produces "ba".

Time: O(n). Extra space: O(1) in an editable buffer, and O(n) if the language must allocate a new string.

Edge cases: the empty string stays empty. One character stays unchanged. Do not add a space.

## Worked algorithm: vowel count

Walk once. Add 1 when the character is a, e, i, o, or u. This lesson does not treat y as a vowel.

Dry run of "team": e and a, so the count is 2.

Time O(n). Space O(1). An empty string counts 0.

## Worked algorithm: anagram

Count the letters in the first word and decrement with the second. Both words are anagrams if every count returns to zero and the lengths match.

Dry run: listen and silent both contain one of each of e, i, l, n, s, t.

Time O(n) for a fixed alphabet. Space O(1) for that alphabet. Different lengths fail immediately.

## Related practice

The ten string questions on this lesson. In the DSA practice list, the coding problems are named reverse-string and count-vowels. Those names are the related coding practice. This article does not start a code runner.
