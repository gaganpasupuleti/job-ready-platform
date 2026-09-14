## Objective
Choose the rows first, then summarize them.

## Prerequisite
You can point to a row and a column in a table.

## Filtering
`WHERE` runs before `GROUP BY`. A condition on a total, such as groups with more than two orders, belongs in `HAVING`.

| order_id | status | amount |
| --- | --- | --- |
| 1 | paid | 1000 |
| 2 | pending | 500 |
| 3 | paid | NULL |

`SUM(amount)` for paid rows is 1000, not 1000 plus zero. `COUNT(*)` counts rows. `COUNT(amount)` skips the NULL amount, so it returns 1.

## Summary
State the dialect when you write SQL. These examples are PostgreSQL. They do not claim an employer interview source.
