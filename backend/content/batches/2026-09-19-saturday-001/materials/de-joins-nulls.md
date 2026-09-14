## Objective
Preserve the rows the question asked for.

## Inner and left
An inner join answers "orders that have a payment." A left join from orders answers "every order, and its payment if one exists."

## NULL
`NULL = NULL` is not true in PostgreSQL. Use `IS NULL`. `SUM` skips NULL. `COUNT(*)` still counts the order row.

## Summary
These rules are PostgreSQL rules for this batch. Do not copy them onto a dialect you have not named.
