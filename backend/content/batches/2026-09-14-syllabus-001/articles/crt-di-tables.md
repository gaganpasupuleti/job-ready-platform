# Reading a simple data table

Data interpretation starts with reading the labels before the numbers. A table of status codes is useless until you know which column is the count.

## Learning objectives

- Read column headers before computing.
- Compute a share only after the total is known.
- Separate a count from a percentage.

## Worked example

Status counts for six ticket requests:

| Status | Count |
| --- | --- |
| 200 | 2 |
| 201 | 1 |
| 400 | 1 |
| 404 | 1 |
| 500 | 1 |

Total requests = \(2+1+1+1+1 = 6\).

Share of successful 200 responses = \(2/6 = 1/3\) ≈ 33%.

The value “2” is a count. It is not already a percentage.

## Common mistakes

- Dividing by the wrong total.
- Treating a count as a percentage.
- Ignoring a row that belongs in the total.

## Recap

Confirm the unit of each column, sum the relevant rows, then divide. Mark-as-read is not assessed competence.
