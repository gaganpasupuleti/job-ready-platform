"""Write the first Saturday content batch as Markdown and JSON.

Run from backend: python -m content.build_saturday_001
Does not touch a database.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "batches" / "2026-09-19-saturday-001"
BATCH_ID = "2026-09-19-saturday-001"

MATERIALS = [
    {
        "key": "da-sql-filter-agg",
        "title": "SQL filtering and aggregation for analysts",
        "kind": "article",
        "level": "beginner",
        "audience": "Fresher",
        "minutes": 25,
        "families": ["data-analyst"],
        "skills": ["sql", "aggregation"],
        "objectives": ["Filter rows with WHERE before grouping", "Use COUNT, SUM, and AVG without inventing zeros", "Read a grouped result against the source rows"],
        "prerequisites": ["You can read a table of rows and columns"],
        "summary": "WHERE chooses rows. GROUP BY builds one row per group. Aggregates ignore NULL in SUM and AVG, and COUNT(column) ignores NULL too.",
        "sources": [{"label": "PostgreSQL aggregate functions", "url": "https://www.postgresql.org/docs/current/functions-aggregate.html"}],
        "examples": ["SELECT status, COUNT(*) FROM orders WHERE status <> 'cancelled' GROUP BY status;"],
        "exercises": ["Count paid orders only. Then sum their amounts. A missing payment is not an amount of zero unless you write COALESCE."],
        "body": """## Objective
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
""",
    },
    {
        "key": "da-read-a-table",
        "title": "Reading a business table without inventing a story",
        "kind": "worked_example",
        "level": "beginner",
        "audience": "Internship",
        "minutes": 20,
        "families": ["data-analyst"],
        "skills": ["data-interpretation"],
        "objectives": ["Name the grain of a table", "Separate a count of rows from a sum of money", "Refuse a conclusion the columns do not support"],
        "prerequisites": ["da-sql-filter-agg is helpful, not required"],
        "summary": "The grain is what one row means. A revenue column is not a profit column. A missing cell is missing, not automatically zero.",
        "sources": [],
        "examples": ["If one row is one order, do not call the row count a customer count."],
        "exercises": ["Given orders and a city on the customer table, explain why you cannot report city revenue until you join and state how you treat cancelled orders."],
        "body": """## Objective
Say what one row represents before you calculate.

## Grain
If each row is one order, 40 rows are 40 orders, not 40 customers. Customers appear only after a join, and a customer can have many orders.

## Units
Revenue is money. Units are counts. Do not add them. If the brief does not define currency, say the unit is unspecified rather than guessing rupees or dollars.

## Summary
A mapped job skill is a topic cue. It is not proof that an employer confirmed that skill for a listing.
""",
    },
    {
        "key": "de-joins-nulls",
        "title": "SQL joins and NULL handling",
        "kind": "article",
        "level": "intermediate",
        "audience": "Entry (1-2 yrs)",
        "minutes": 30,
        "families": ["data-engineer"],
        "skills": ["sql", "joins"],
        "objectives": ["Choose INNER JOIN when both sides must exist", "Keep unmatched rows with LEFT JOIN", "Stop treating NULL as equal to NULL"],
        "prerequisites": ["You can filter and group a single table"],
        "summary": "An inner join drops orders with no matching payment. A left join keeps them. NULL = NULL is unknown, so use IS NULL.",
        "sources": [{"label": "PostgreSQL comparison functions", "url": "https://www.postgresql.org/docs/current/functions-comparison.html"}],
        "examples": ["SELECT o.id FROM orders o LEFT JOIN payments p ON p.order_id = o.id WHERE p.id IS NULL;"],
        "exercises": ["Explain why WHERE p.amount IS NULL after a left join is not the same as filtering inside the join condition."],
        "body": """## Objective
Preserve the rows the question asked for.

## Inner and left
An inner join answers "orders that have a payment." A left join from orders answers "every order, and its payment if one exists."

## NULL
`NULL = NULL` is not true in PostgreSQL. Use `IS NULL`. `SUM` skips NULL. `COUNT(*)` still counts the order row.

## Summary
These rules are PostgreSQL rules for this batch. Do not copy them onto a dialect you have not named.
""",
    },
    {
        "key": "de-python-validation",
        "title": "Python ingestion checks you can run on your own computer",
        "kind": "article",
        "level": "intermediate",
        "audience": "Fresher",
        "minutes": 25,
        "families": ["data-engineer"],
        "skills": ["python", "validation"],
        "objectives": ["Reject a row with a missing required key", "Refuse a negative amount when the brief forbids it", "Keep validation separate from a database write"],
        "prerequisites": ["You can write a Python function on your own computer"],
        "summary": "Online Python execution is locked. These checks are for a local script. A failed check returns a reason. It does not invent a repaired row.",
        "sources": [{"label": "Python exceptions tutorial", "url": "https://docs.python.org/3/tutorial/errors.html"}],
        "examples": ["def require_amount(row):\n    if 'amount' not in row or row['amount'] is None:\n        raise ValueError('amount is required')"],
        "exercises": ["Write a local function that rejects duplicate order ids and returns the rejected ids. Do not submit it to the locked playground."],
        "body": """## Objective
Fail a bad row with a reason.

## Locked runner
JobReady's Python runner is unavailable. This page does not grade a script you paste into the playground.

## Checks
Require the keys the schema names. Reject a string where an amount is required. Do not replace a missing amount with zero unless the brief says so.

## Summary
A local script and a repository URL can be evidence for a manual review. They are not an automatic grade.
""",
    },
    {
        "key": "py-collections-flow",
        "title": "Python collections and control flow",
        "kind": "article",
        "level": "beginner",
        "audience": "Fresher",
        "minutes": 25,
        "families": ["python-dev"],
        "skills": ["python", "collections"],
        "objectives": ["Pick a list, dict, or set for the access you need", "Avoid mutating a list while iterating it", "Use a guard clause instead of a buried return"],
        "prerequisites": ["You can run Python 3 on your own computer"],
        "summary": "A list keeps order and duplicates. A set does not. A dict maps a key to one value. The playground will not execute these examples.",
        "sources": [{"label": "Python data structures", "url": "https://docs.python.org/3/tutorial/datastructures.html"}],
        "examples": ["seen = set()\nfor order_id in order_ids:\n    if order_id in seen:\n        continue\n    seen.add(order_id)"],
        "exercises": ["On your computer, write a function that returns names longer than 3 characters. Do not expect the locked editor to run it."],
        "body": """## Objective
Choose a collection that matches the question.

## Lists, sets, dicts
Use a list when order and duplicates matter. Use a set for membership. Use a dict when each key has one current value.

## Flow
`if` chooses a branch. `for` visits items. `break` leaves the loop. A function that returns `None` did not return an empty list unless you wrote `return []`.

## Summary
Reading this material is self-reported study, not assessed competence.
""",
    },
    {
        "key": "py-functions-exceptions",
        "title": "Python functions and exceptions",
        "kind": "cheatsheet",
        "level": "beginner",
        "audience": "Fresher",
        "minutes": 20,
        "families": ["python-dev"],
        "skills": ["python", "exceptions"],
        "objectives": ["Write a function with an explicit return", "Catch the exception you can handle", "Avoid a bare except that hides bugs"],
        "prerequisites": ["py-collections-flow"],
        "summary": "A function without return yields None. except ValueError handles ValueError. except Exception hides more than you intend.",
        "sources": [{"label": "Python errors and exceptions", "url": "https://docs.python.org/3/tutorial/errors.html"}],
        "examples": ["def parse_amount(text):\n    try:\n        return int(text)\n    except ValueError:\n        raise ValueError('amount must be an integer') from None"],
        "exercises": ["Locally, call parse_amount('12') and parse_amount('no'). Record both results in a repository note. The site will not run them."],
        "body": """## Objective
Return a value or raise a named error.

## Functions
Default arguments that are mutable are shared across calls. Prefer `None` and create a new list inside the function.

## Exceptions
Catch `ValueError` when the text is not an integer. Do not catch `Exception` just to print "failed" and continue as if the row were valid.

## Summary
This cheat sheet is study material. It does not unlock the online runner.
""",
    },
]


def _q(key, stem, skill, difficulty, options, correct, why, explanation, table=None):
    letters = ["A", "B", "C", "D"]
    built = []
    correct_set = {correct} if isinstance(correct, int) else set(correct)
    for index, text in enumerate(options):
        built.append({"key": letters[index], "text": text, "correct": index in correct_set, "why": why[index]})
    return {
        "key": key,
        "stem": stem if not table else stem + "\n\n" + table,
        "skill": skill,
        "difficulty": difficulty,
        "mode": "multi" if isinstance(correct, list) else "single",
        "options": built,
        "explanation": explanation,
    }


DI = """| Category | Units sold | Revenue | Returns |
| --- | --- | --- | --- |
| Books | 40 | 8000 | 2 |
| Pens | 100 | 2500 | 5 |
| Bags | 10 | 6000 | 1 |
| Cards | 50 | 1500 | 0 |"""


def questions():
    items = []
    items.append(_q("da-q01", "A table has one row per order. Which clause keeps only status = 'paid' before you count rows?", "sql-filter", "easy", ["GROUP BY", "WHERE", "ORDER BY", "HAVING"], 1, ["Groups after filtering.", "WHERE chooses rows before aggregates.", "Sorts the output.", "Filters groups, not source rows."], "WHERE removes rows first. HAVING filters groups after GROUP BY."))
    items.append(_q("da-q02", "Select every statement that is true for PostgreSQL when amount can be NULL.", "sql-aggregation", "medium", ["SUM(amount) skips NULL", "COUNT(amount) skips NULL", "COUNT(*) skips NULL amounts", "SUM of only NULL amounts is 0"], [0, 1], ["SUM ignores NULL and adds the remaining numbers.", "COUNT(column) ignores NULL.", "COUNT(*) counts the row even when amount is NULL.", "SUM of no non-NULL values is NULL, not 0."], "Two statements are true. COUNT(*) still counts the row. A sum of only NULLs is NULL unless you COALESCE."))
    items.append(_q("da-q03", "You need one row per status with the number of orders. Which pair is required?", "sql-aggregation", "easy", ["WHERE and ORDER BY", "GROUP BY and COUNT(*)", "JOIN and DISTINCT only", "LIMIT and OFFSET"], 1, ["That pair does not build groups.", "GROUP BY status plus COUNT(*) builds the summary.", "A join is not required on one table.", "LIMIT only trims output."], "Group by the status, then count rows in each group."))
    items.append(_q("da-q04", "Paid orders have amounts 1000 and NULL. In PostgreSQL, what is SUM(amount)?", "sql-aggregation", "medium", ["1000", "0", "NULL", "2000"], 0, ["SUM skips NULL, so the total is 1000.", "SUM does not turn the remaining NULL into a zero total.", "SUM of a non-NULL value is not NULL.", "NULL is not treated as 1000."], "SUM ignores NULL. It does not add a zero unless you COALESCE."))
    items.append(_q("da-q05", "Which statement about a grouped result is supported by the columns you selected?", "tabular", "easy", ["Two status rows mean two customers", "Two status rows mean two groups of orders", "The row count is profit", "Alphabetical status means newest first"], 1, ["Customer is not in the result.", "Each group is one status.", "No profit column exists.", "Order is unspecified without ORDER BY."], "Do not read a grain the SELECT list does not contain."))
    items.append(_q("da-q06", "A filter 'groups with more than 3 orders' belongs in which clause?", "sql-aggregation", "medium", ["WHERE", "HAVING", "SELECT only", "FROM"], 1, ["WHERE cannot see the group total unless you repeat a subquery.", "HAVING filters after grouping.", "SELECT does not filter rows.", "FROM names tables."], "Conditions on aggregates belong in HAVING."))
    items.append(_q("da-q07", "DISTINCT city after a customer join tells you what?", "tabular", "medium", ["Number of orders", "Set of city values present", "Profit by city", "That every city has an order"], 1, ["DISTINCT is not a count of orders.", "It returns unique city values in the result.", "No profit column is named.", "Cities with no join match never appear."], "DISTINCT removes duplicate values. It is not a business total."))
    items.append(_q("da-q08", "An analyst writes AVG(amount) on paid orders. A NULL amount is in the paid set. PostgreSQL AVG...", "sql-aggregation", "medium", ["Counts that NULL as 0", "Ignores that NULL", "Fails the query", "Returns 0"], 1, ["AVG does not treat NULL as 0.", "AVG skips NULL, like SUM.", "A NULL in the column does not fail AVG.", "It returns the average of the non-NULL amounts."], "If you want a missing amount to act as zero, write that with COALESCE."))
    items.append(_q("da-q09", "Which comparison is safe when the brief never defines currency?", "tabular", "easy", ["Call the column profit in rupees", "Report the number and say the unit is unspecified", "Convert it to USD", "Drop the column"], 1, ["That invents both profit and a currency.", "State the unknown instead of guessing.", "No rate was given.", "The column can still be used if labeled as stored."], "Do not invent units the table does not give."))
    items.append(_q("da-q10", "You have SELECT city, SUM(amount) without GROUP BY or an aggregate-only query. In PostgreSQL this is...", "sql-aggregation", "hard", ["Always valid", "Invalid unless city is grouped or aggregated", "A window function", "A left join"], 1, ["PostgreSQL rejects a bare city beside SUM.", "city must be in GROUP BY or wrapped.", "No OVER clause is present.", "This is not a join."], "PostgreSQL requires grouped columns to appear in GROUP BY."))

    items.append(_q("de-q01", "You need every order, including those with no payment row. Which join from orders?", "joins", "easy", ["INNER JOIN payments", "LEFT JOIN payments", "CROSS JOIN customers", "NATURAL JOIN only"], 1, ["Inner join drops unpaid orders.", "Left join keeps every order.", "Cross join multiplies rows.", "Natural join depends on shared names and can surprise you."], "Start from orders and left join payments."))
    items.append(_q("de-q02", "In PostgreSQL, which predicate finds a missing payment id after a left join?", "nulls", "easy", ["p.id = NULL", "p.id IS NULL", "p.id = 0", "p.id <> p.id"], 1, ["= NULL is unknown, not true.", "IS NULL is the SQL null test.", "Zero is a value, not missing.", "That comparison is not the null test."], "Use IS NULL. Do not use = NULL."))
    items.append(_q("de-q03", "WHERE p.amount > 0 placed after a LEFT JOIN payments removes what?", "joins", "medium", ["Nothing", "Orders whose joined amount is NULL or not greater than 0", "Only cancelled orders", "Duplicate customers"], 1, ["The WHERE still filters the result.", "NULL > 0 is unknown, so those rows drop, and the left join behaves like an inner join.", "Status is not in the predicate.", "This does not deduplicate."], "A WHERE on the right table after a left join drops unmatched rows."))
    items.append(_q("de-q04", "Two rows have amount NULL. SUM(amount) in PostgreSQL is...", "nulls", "easy", ["0", "NULL", "2", "An error"], 1, ["SUM of no non-NULL values is NULL, not 0.", "There is no number to add.", "COUNT would be the row count, not SUM.", "SUM of all NULL inputs returns NULL."], "If you need zero, write COALESCE(SUM(amount), 0)."))
    items.append(_q("de-q05", "A Python row is {'id': 1} and amount is required. What should a strict local check do?", "validation", "easy", ["Store amount 0", "Reject the row because amount is missing", "Skip the key and continue as valid", "Call the online runner"], 1, ["Zero was not in the row.", "A required key that is absent fails the check.", "Silent skip hides the defect.", "Online Python execution is locked and is not the check."], "Reject missing required fields. Do not invent zero."))
    items.append(_q("de-q06", "A payload uses the string '12' for an integer amount. A strict validator should...", "validation", "medium", ["Accept it because it looks numeric", "Reject it until the brief allows coercion", "Save it as a date", "Drop the id"], 1, ["Looking numeric is not the declared type.", "Reject unless the brief says to coerce.", "The field is an amount.", "The id is not the defect."], "Type checks follow the schema, not a guess."))
    items.append(_q("de-q07", "An ingestion run sees the same order id twice. The brief says ids are unique. The load should...", "validation", "medium", ["Keep both rows", "Reject the duplicate with the id in the reason", "Average the amounts", "Mark both paid"], 1, ["Both rows violate uniqueness.", "Report the duplicate id and do not silently merge.", "Averaging invents a value.", "Status was not in the defect."], "Uniqueness failures are rejected, not repaired by invention."))
    items.append(_q("de-q08", "COALESCE(p.amount, 0) means...", "nulls", "medium", ["Drop the row if amount is NULL", "Use 0 when amount is NULL", "Convert text to a date", "Inner-join the payment"], 1, ["COALESCE replaces a value; it does not drop the row.", "The first non-NULL argument is used.", "No date cast is involved.", "COALESCE is not a join."], "Use COALESCE only when the brief wants a replacement."))
    items.append(_q("de-q09", "Which Python exception fits int('no') during a local parse?", "python", "easy", ["KeyError", "ValueError", "ImportError", "StopIteration"], 1, ["KeyError is a missing mapping key.", "int() raises ValueError on a non-integer string.", "Nothing is being imported.", "The iterator is not exhausted here."], "Catch ValueError if the brief says invalid text is a handled case."))
    items.append(_q("de-q10", "A left join keeps an order when the payment table has no match. The payment columns in that result are...", "joins", "medium", ["0", "NULL", "The order id copied again", "An empty string"], 1, ["Zero is not supplied by the join.", "Unmatched right-side columns are NULL.", "The order id stays on the order side.", "PostgreSQL does not insert an empty string."], "NULL means no matching payment row, not a zero payment."))

    items.append(_q("py-q01", "You need to remember order ids in arrival order, including a repeated id. Which collection?", "collections", "easy", ["set", "list", "The keys of a dict only", "A single integer"], 1, ["A set drops duplicates and does not promise your visit order for this need.", "A list keeps order and duplicates.", "Dict keys are unique.", "One integer cannot hold the sequence."], "Use a list when both order and duplicates matter."))
    items.append(_q("py-q02", "A set is the better default when the only question is whether an id was already seen. Why?", "collections", "easy", ["Sets keep every duplicate", "Membership tests are the job a set is built for", "Sets sort amounts", "Sets replace exceptions"], 1, ["Sets do not keep duplicates.", "Membership is the set operation you need.", "A set is not a numeric sort.", "Sets do not handle errors."], "seen = set() then `if id in seen` matches the question."))
    items.append(_q("py-q03", "d.get('city') when 'city' is absent returns...", "collections", "easy", ["KeyError", "None, unless you pass a default", "An empty list", "The string 'city'"], 1, ["d['city'] raises KeyError. get does not.", "get returns None by default.", "You did not pass a list default.", "The key is not returned as the value."], "Use get when absence is a normal case. Use brackets when absence is a bug."))
    items.append(_q("py-q04", "A function has no return statement and you call it. The result is...", "functions", "easy", ["[]", "None", "0", "False"], 1, ["An empty list is written return [].", "A missing return yields None.", "0 must be returned.", "False must be returned."], "None and [] are different. Do not treat them as the same empty result."))
    items.append(_q("py-q05", "Why is `def f(items=[]):` a poor default for a fresh list each call?", "functions", "medium", ["The list is copied every call", "The same list object is reused", "Python rejects the syntax", "It always raises TypeError"], 1, ["The default is not copied per call.", "The default object is created once and shared.", "The syntax is legal.", "It does not always raise."], "Use None and create a new list inside the function."))
    items.append(_q("py-q06", "int('12.5') raises which exception?", "exceptions", "medium", ["ValueError", "TypeError", "IndexError", "None"], 0, ["The string is not an integer literal.", "TypeError is the wrong type of object, not this parse.", "No index is used.", "A raised exception is not None."], "int() accepts '12' and rejects '12.5' with ValueError."))
    items.append(_q("py-q07", "Which handler matches the stated failure and nothing broader?", "exceptions", "medium", ["except:", "except Exception:", "except ValueError:", "except BaseException: pass"], 2, ["A bare except hides control-flow exceptions too.", "Exception is still very wide.", "ValueError matches the parse failure named in the brief.", "BaseException also catches system exits."], "Catch the exception you can handle."))
    items.append(_q("py-q08", "for name in names: if name == 'stop': break. What happens when 'stop' is seen?", "control-flow", "easy", ["The loop leaves", "The name is skipped and the loop continues", "The function returns 0", "An exception is raised"], 0, ["break exits the loop.", "continue would skip to the next item.", "There is no return.", "break is not an exception."], "break leaves. continue goes to the next item."))
    items.append(_q("py-q09", "A local script should record a rejected row by...", "control-flow", "medium", ["Printing nothing and returning the row as valid", "Returning the row and a reason, or raising a named error", "Calling the locked playground", "Deleting the source file"], 1, ["Silence marks a bad row as valid.", "The caller needs the reason.", "The playground cannot execute it.", "Do not destroy the input."], "Validation reports a reason. It does not pretend the row was clean."))
    items.append(_q("py-q10", "Which pair is a list method that adds one item at the end, and the mistake of using it on a set?", "collections", "hard", ["append, and sets use add", "add, and lists use append", "push, and both use push", "insert, and sets use append"], 0, ["list.append adds one item. set.add is the set operation.", "Those names are swapped.", "Python lists do not use push.", "Sets do not use append."], "Match the method to the collection. A locked editor will not correct this for you."))

    items.append(_q("crt-q01", "A book costs 240. A 25% discount is applied once. What is the sale price?", "quantitative", "easy", ["180", "200", "215", "60"], 0, ["240 minus 25% is 180.", "That is a smaller discount.", "That is not 25% off 240.", "60 is the discount, not the price."], "25% of 240 is 60. 240 - 60 = 180."))
    items.append(_q("crt-q02", "A train covers 180 km in 3 hours at a steady speed. What is the speed in km/h?", "quantitative", "easy", ["50", "60", "90", "540"], 1, ["180/3 is not 50.", "180/3 = 60.", "That would be 180/2.", "That multiplies instead of dividing."], "Speed = distance / time = 60 km/h. No stops are stated."))
    items.append(_q("crt-q03", "The ratio of apples to oranges is 3:2. There are 20 oranges. How many apples?", "quantitative", "medium", ["12", "30", "32", "8"], 1, ["That uses 20 as the apples.", "3/2 * 20 = 30.", "That is not the stated ratio.", "That subtracts instead of scaling."], "If 2 parts are 20, 1 part is 10, so 3 parts are 30."))
    items.append(_q("crt-q04", "Simple interest on 2000 at 5% per year for 2 years is...", "quantitative", "medium", ["100", "200", "2100", "500"], 1, ["That is one year.", "2000 * 0.05 * 2 = 200.", "That adds a year of interest into the principal label.", "5% of 2000 is 100, not 500."], "Simple interest does not compound. The interest is 200, not the amount 2200."))
    items.append(_q("crt-q05", "A rectangle is 8 by 5. A wrong answer treats those numbers as the perimeter. What is the area?", "quantitative", "easy", ["13", "26", "40", "80"], 2, ["That adds one pair of sides.", "That is the perimeter.", "8 * 5 = 40.", "That doubles the area."], "Area is length times width. Perimeter would be 26."))
    items.append(_q("crt-q06", "All coaches in a set are mentors. Some mentors are alumni. Which conclusion must follow?", "reasoning", "medium", ["All coaches are alumni", "Some coaches may be alumni, but it is not forced", "No mentor is a coach", "Every alumni is a coach"], 1, ["Some mentors are alumni does not force every coach to be one.", "The overlap with coaches is not required by the sentences.", "Coaches are mentors, so that is false.", "The sentences do not reverse that way."], "Do not promote 'some' into 'all'."))
    items.append(_q("crt-q07", "Find the next number: 2, 6, 12, 20, ?", "reasoning", "medium", ["28", "30", "32", "24"], 1, ["The gaps are 4, 6, 8, so the next gap is 10, not 8.", "20 + 10 = 30.", "The gap is not 12.", "That repeats a gap of 4."], "The differences increase by 2: 4, 6, 8, 10."))
    items.append(_q("crt-q08", "If North becomes West by a rotation of the map labels, a person facing East after the same rotation faces...", "reasoning", "hard", ["North", "South", "West", "East"], 0, ["If every direction label turns the same way, East moves to the old North position in this consistent turn.", "South is a 180-degree turn.", "West was the image of North, not East.", "The facing label changes with the same rotation."], "North->West is a 90-degree turn. East follows to North."))
    items.append(_q("crt-q09", "Five people sit in a row. A is left of B. C is right of B. D is between A and B. Who is immediately right of A?", "reasoning", "medium", ["C", "D", "B", "Cannot be anyone but C"], 1, ["C is on the other side of B.", "D is between A and B, so D sits immediately right of A if A is left of B.", "B is further right, with D between.", "C is not between A and B."], "Order from the left is A, D, B, and C further right. Immediate right of A is D."))
    items.append(_q("crt-q10", "A statement says 'only pens are blue' in a puzzle. Which reading is the careful one?", "reasoning", "hard", ["Every pen is blue", "If it is blue, it is a pen; a pen might not be blue", "Nothing blue exists", "Every object is a pen"], 1, ["'Only pens are blue' does not say every pen is blue.", "Blue things are pens. Pens can be other colors.", "The sentence does not deny blue things.", "It does not speak about every object."], "Only A are B means B implies A, not that every A is B."))
    items.append(_q("crt-q11", "Choose the sentence that is grammatically consistent.", "verbal", "easy", ["The report were filed yesterday.", "The report was filed yesterday.", "The report filed were yesterday.", "Were filed the report."], 1, ["'Report' is singular, so 'were' does not agree.", "Singular subject with 'was' agrees.", "The verb phrase is out of order and does not agree.", "The auxiliary is placed without a question structure."], "A singular subject takes 'was' in this past statement."))
    items.append(_q("crt-q12", "'The brief is ambiguous about units' means the writer...", "verbal", "easy", ["Named rupees", "Did not make the unit clear", "Proved the total", "Removed the table"], 1, ["Ambiguous means the unit was not settled.", "The unit is unclear.", "Ambiguity is not a proof.", "The table may still be present."], "Ambiguous means more than one reading is open."))
    items.append(_q("crt-q13", "Which revision removes a vague claim without adding a fact?", "verbal", "medium", ["Revenue is excellent.", "The table shows revenue of 8000 for Books.", "The employer demands this skill.", "The candidate is hired."], 1, ["Excellent is not measured.", "8000 is the table value, not a new claim.", "The mapping does not prove an employer demand.", "Hiring is not in the table."], "Cite the number that is on the page."))
    items.append(_q("crt-q14", "Select the pair that matches in meaning.", "verbal", "medium", ["omit / include", "prerequisite / requirement that comes first", "null / zero in every dialect", "submit / delete"], 1, ["Those are opposites.", "A prerequisite is something required beforehand.", "NULL is not defined as zero.", "Submit does not mean delete."], "Use the ordinary meaning. Do not import a SQL rule into the word 'null' here."))
    items.append(_q("crt-q15", "A concise instruction for a locked tool is...", "verbal", "easy", ["Use three badges and also a warning panel that repeats the same sentence", "Say once that execution is unavailable", "Claim the tool graded the draft", "Tell the student the draft was deleted"], 1, ["Repeating the same lock does not add information.", "One lock message is enough.", "A locked tool did not grade anything.", "Drafts must not be deleted by the lock."], "State the lock once. Do not invent a result."))

    items += [
        _q("crt-q16", "Using only this table, which category has the highest revenue?", "data-interpretation", "easy", ["Pens", "Books", "Bags", "Cards"], 1, ["Pens have the most units, not the most revenue.", "Books show 8000.", "Bags show 6000.", "Cards show 1500."], "Compare the Revenue column only.", DI),
        _q("crt-q17", "Using only this table, which category sold the most units?", "data-interpretation", "easy", ["Books", "Bags", "Pens", "Cards"], 2, ["40 is less than 100.", "10 is the smallest.", "Pens show 100.", "50 is less than 100."], "Units sold is the second column.", DI),
        _q("crt-q18", "Revenue per unit for Books, using only this table, is...", "data-interpretation", "medium", ["20", "200", "8000", "40"], 1, ["That divides the wrong way.", "8000 / 40 = 200.", "That is total revenue, not per unit.", "That is the unit count."], "Divide Books revenue by Books units. No rounding is required.", DI),
        _q("crt-q19", "The return rate for Pens, as returns divided by units sold, is...", "data-interpretation", "medium", ["5%", "20%", "50%", "1%"], 0, ["5 / 100 = 0.05, which is 5%.", "That uses a different pair of cells.", "That treats 50 cards as the denominator.", "1 return belongs to Bags."], "State the rate as returns / units sold. Pens are 5/100.", DI),
        _q("crt-q20", "Total revenue across the four categories is...", "data-interpretation", "easy", ["16000", "18000", "200", "8000"], 1, ["That drops Cards or mis-adds.", "8000+2500+6000+1500 = 18000.", "200 is a per-unit figure, not a total.", "8000 is Books alone."], "Add the four revenue cells. Returns are not subtracted unless the question says so.", DI),
    ]
    return items


ASSIGNMENTS = [
    {
        "key": "da-assign-paid-totals",
        "title": "Report paid order totals",
        "families": ["data-analyst"],
        "skills": ["sql", "aggregation"],
        "mode": "sql_evidence",
        "minutes": 40,
        "audience": "Fresher",
        "goal": "Write the paid-order count and amount total for the sample orders, and explain NULL handling.",
        "requirements": ["Use the orders table in the linked SQL problem", "PostgreSQL dialect", "Do not treat a NULL amount as zero unless you write COALESCE"],
        "deliverables": ["The query you submitted in SQL Studio", "Two sentences on what COUNT(*) counted"],
        "hints": ["Filter status before you aggregate"],
        "prerequisites": ["da-sql-filter-agg"],
        "rubric": [{"criterion": "Filters paid rows", "points": 2}, {"criterion": "Count and sum match the seed", "points": 2}, {"criterion": "NULL explanation is accurate", "points": 1}],
        "sql_problem_slug": "orders-paid-totals",
        "brief": "Submit the SQL Studio result for the linked problem. A written claim without an accepted server-side submission does not satisfy the SQL part.",
        "version": 1,
    },
    {
        "key": "de-assign-local-validate",
        "title": "Validate an order row on your computer",
        "families": ["data-engineer"],
        "skills": ["python", "validation"],
        "mode": "local_python",
        "minutes": 45,
        "audience": "Fresher",
        "goal": "Write a local Python function that rejects a missing amount and a duplicate id, then share the code as text or an HTTPS repository URL.",
        "requirements": ["Run it on your own computer. The site will not execute it.", "Do not claim an automatic grade.", "Manual review only."],
        "deliverables": ["Function text or HTTPS repository URL", "Two example inputs and the reasons they were rejected"],
        "hints": ["Raise ValueError with the field name"],
        "prerequisites": ["de-python-validation"],
        "rubric": [{"criterion": "Missing amount is rejected", "points": 2}, {"criterion": "Duplicate id is rejected", "points": 2}, {"criterion": "Examples match the code", "points": 1}],
        "sql_problem_slug": None,
        "brief": "This assignment is local execution and manual review. The locked playground is not part of the submission path.",
    },
    {
        "key": "py-assign-exceptions",
        "title": "Functions that return or raise",
        "families": ["python-dev"],
        "skills": ["python", "exceptions"],
        "mode": "local_python",
        "minutes": 40,
        "audience": "Fresher",
        "goal": "On your computer, write parse_amount and a caller that records ValueError. Submit the code as text or an HTTPS URL.",
        "requirements": ["Local execution only", "No automatic Python grading", "Do not use a bare except"],
        "deliverables": ["Code text or HTTPS repository URL", "One successful call and one ValueError call"],
        "hints": ["int('no') raises ValueError"],
        "prerequisites": ["py-functions-exceptions"],
        "rubric": [{"criterion": "Success path returns an int", "points": 2}, {"criterion": "Invalid text raises or records ValueError", "points": 2}, {"criterion": "No bare except", "points": 1}],
        "sql_problem_slug": None,
        "brief": "Label: solve this on your own computer. The online runner stays locked and will not grade this work.",
    },
]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    materials_dir = ROOT / "materials"
    materials_dir.mkdir(parents=True, exist_ok=True)
    material_rows = []
    for item in MATERIALS:
        body = item["body"].strip() + "\n"
        rel = f"materials/{item['key']}.md"
        _write(ROOT / rel, body)
        material_rows.append({k: v for k, v in item.items() if k != "body"} | {"body_file": rel, "version": 1})
    questions_payload = {"version": 1, "questions": questions()}
    for row in questions_payload["questions"]:
        if row["key"] == "da-q02":
            row["version"] = 2
    _write(ROOT / "questions.json", json.dumps(questions_payload, indent=2) + "\n")
    _write(ROOT / "assignments.json", json.dumps({"version": 1, "assignments": ASSIGNMENTS}, indent=2) + "\n")
    project = {
        "key": "orders-payment-quality",
        "version": 1,
        "title": "Orders and payment quality",
        "families": ["data-analyst", "data-engineer"],
        "skills": ["sql", "joins"],
        "scenario": "A small shop recorded orders and payments in separate tables. Some orders have no payment row. Cancelled orders must not be treated as revenue.",
        "outcome": "A reviewer can see which orders are paid, which have no payment, and a written note that does not invent zeros.",
        "dataset_file": "dataset.sql",
        "milestones": [
            {"title": "Paid totals", "type": "sql", "sql_problem_slug": "orders-paid-totals", "deliverable": "Accepted SQL Studio submission for paid count and sum."},
            {"title": "Orders missing a payment", "type": "sql", "sql_problem_slug": "orders-missing-payment", "deliverable": "Accepted SQL Studio submission using IS NULL."},
            {"title": "Revenue by customer", "type": "sql", "sql_problem_slug": "orders-revenue-by-customer", "deliverable": "Accepted SQL Studio submission excluding cancelled orders."},
            {"title": "Findings note", "type": "review", "deliverable": "Short note on what a missing payment means. This is not an automatic grade."},
        ],
    }
    _write(ROOT / "project.json", json.dumps(project, indent=2) + "\n")
    _write(
        ROOT / "dataset.sql",
        """-- Original synthetic shop. PostgreSQL. Amounts are rupees. No employer source.
CREATE TABLE customers (id int primary key, name text not null, city text not null);
CREATE TABLE orders (
  id int primary key,
  customer_id int not null references customers(id),
  status text not null,
  amount numeric,
  ordered_on date not null
);
CREATE TABLE payments (
  id int primary key,
  order_id int not null references orders(id),
  amount numeric not null,
  paid_on date not null
);
INSERT INTO customers (id, name, city) VALUES
  (1, 'Ada', 'Hyderabad'),
  (2, 'Ben', 'Bengaluru'),
  (3, 'Cho', 'Pune');
INSERT INTO orders (id, customer_id, status, amount, ordered_on) VALUES
  (1, 1, 'paid', 1000, DATE '2026-01-02'),
  (2, 1, 'pending', 500, DATE '2026-01-05'),
  (3, 2, 'paid', 800, DATE '2026-01-03'),
  (4, 2, 'cancelled', 200, DATE '2026-01-04'),
  (5, 3, 'shipped', 1500, DATE '2026-01-06');
INSERT INTO payments (id, order_id, amount, paid_on) VALUES
  (1, 1, 1000, DATE '2026-01-02'),
  (2, 3, 800, DATE '2026-01-04');
""",
    )
    packs = [
        {"key": "pack-data-analyst", "title": "Data analyst SQL and tables", "kind": "technical", "families": ["data-analyst"], "prefix": "da-"},
        {"key": "pack-data-engineer", "title": "Data engineer joins and validation", "kind": "technical", "families": ["data-engineer"], "prefix": "de-"},
        {"key": "pack-python-dev", "title": "Python collections and exceptions", "kind": "technical", "families": ["python-dev"], "prefix": "py-"},
        {"key": "pack-crt-shared", "title": "CRT: aptitude, reasoning, verbal, and tables", "kind": "crt", "families": [], "prefix": "crt-"},
    ]
    by_key = {row["key"]: row for row in questions_payload["questions"]}
    pack_rows = []
    for pack in packs:
        keys = [key for key in by_key if key.startswith(pack["prefix"])]
        pack_rows.append({k: v for k, v in pack.items() if k != "prefix"} | {"version": 1, "question_keys": keys, "instructions": "Practice mode reveals explanations after you answer, using the existing practice rules. There is no negative marking. SQL items are PostgreSQL. Amounts in the CRT table are unnamed currency units unless a question says otherwise. A job skill tag is topic context, not an employer confirmation."})
    files = {
        "materials.json": {"version": 1, "materials": material_rows},
        "assignments.json": json.loads((ROOT / "assignments.json").read_text(encoding="utf-8")),
        "questions.json": questions_payload,
        "project.json": project,
        "packs.json": {"version": 1, "packs": pack_rows},
    }
    _write(ROOT / "packs.json", json.dumps(files["packs.json"], indent=2) + "\n")
    _write(ROOT / "materials.json", json.dumps(files["materials.json"], indent=2) + "\n")
    manifest_items = []
    for name in files:
        digest = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        manifest_items.append({"path": name, "sha256": digest, "content_type": name.split(".")[0]})
    dataset = (ROOT / "dataset.sql").read_bytes()
    manifest_items.append({"path": "dataset.sql", "sha256": hashlib.sha256(dataset).hexdigest(), "content_type": "dataset"})
    for row in material_rows:
        blob = (ROOT / row["body_file"]).read_bytes()
        manifest_items.append({"path": row["body_file"], "sha256": hashlib.sha256(blob).hexdigest(), "content_type": "material_body", "key": row["key"]})
    manifest = {
        "batch_id": BATCH_ID,
        "schema_version": 1,
        "change_reason": "Initial Saturday batch for data analyst, data engineer, and Python developer, plus a shared CRT pack.",
        "authorization": "local-apply-only until an explicit production publication decision",
        "items": manifest_items,
    }
    _write(ROOT / "manifest.json", json.dumps(manifest, indent=2) + "\n")
    print("WROTE", ROOT)
    print("QUESTIONS", len(questions_payload["questions"]))
    print("MATERIALS", len(material_rows))


if __name__ == "__main__":
    main()
