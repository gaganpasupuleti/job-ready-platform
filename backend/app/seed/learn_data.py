# ruff: noqa: E501
"""Idempotent Build 5 seed: Practice Hub paths, the Python Foundations course, and the project catalog.

Every helper keys off a stable slug, so re-running the seed leaves existing rows untouched
and only fills in what is missing.
"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.coding import CodingProblem
from app.models.learn import (
    Course,
    CourseLesson,
    CourseModule,
    LessonDoubt,
    LessonHint,
    PracticePath,
    PracticePathItem,
    PracticePathSection,
    Project,
    ProjectModule,
    ProjectTask,
)
from app.models.learn_enums import (
    CourseLevel,
    LessonType,
    LessonUnlockMode,
    PathAvailability,
    PracticePathDifficulty,
    PracticePathItemType,
    PracticePathType,
    SolutionRevealPolicy,
)
from app.models.tagging import Company
from app.models.taxonomy import Topic

LEARN_COMPANIES = ["TCS", "Accenture", "Infosys", "Cognizant", "Capgemini", "Deloitte"]

COMPANY_DISCLAIMER = (
    "Community-curated preparation track inspired by publicly shared interview experiences. "
    "All questions and problems are original content written by our team. "
    "This track is not affiliated with, endorsed by, or sponsored by {company}, and it does not "
    "reproduce any confidential or proprietary assessment material."
)


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


# ----------------------------------------------------------------------
# Python Foundations course content
# ----------------------------------------------------------------------


def _text(value: str) -> dict[str, Any]:
    return {"type": "text", "value": value}


def _code(value: str, language: str = "python") -> dict[str, Any]:
    return {"type": "code", "language": language, "value": value}


def _bullets(title: str, items: list[str]) -> dict[str, Any]:
    return {"type": "list", "title": title, "items": items}


def _tip(value: str) -> dict[str, Any]:
    return {"type": "callout", "tone": "tip", "value": value}


PYTHON_COURSE_MODULES: list[dict[str, Any]] = [
    {
        "slug": "getting-started",
        "title": "Getting Started with Python",
        "summary": "What Python is, how a program runs, and how to print your first output.",
        "lessons": [
            {
                "slug": "what-is-python",
                "title": "What Python Is and Why It Is Used",
                "lesson_type": LessonType.CONCEPT,
                "estimated_minutes": 8,
                "statement": {
                    "summary": "Python is a high-level, interpreted language designed to be read easily by humans.",
                    "blocks": [
                        _text(
                            "Python is a general-purpose programming language. You write plain-text instructions in a "
                            "file, and an interpreter reads that file top to bottom and executes each instruction in order. "
                            "There is no separate compile step to worry about while you are learning."
                        ),
                        _bullets(
                            "Where you will see Python at work",
                            [
                                "Automating repetitive file, spreadsheet, and report tasks",
                                "Backend web services and internal tools",
                                "Data analysis, machine learning, and reporting pipelines",
                                "Interview rounds, because the syntax stays out of your way",
                            ],
                        ),
                        _text(
                            "Python is dynamically typed: a variable takes whatever type you assign to it, and that "
                            "type can change later. It is also indentation-sensitive, which means the whitespace at the "
                            "start of a line is part of the grammar, not just formatting."
                        ),
                        _code(
                            "# Every line below is a complete instruction\n"
                            "language = \"Python\"\n"
                            "year = 1991\n"
                            "print(language, \"was released in\", year)"
                        ),
                        _tip(
                            "Read Python code out loud as English. Well-written Python usually reads like a sentence, "
                            "and that habit makes debugging much faster."
                        ),
                    ],
                },
                "hints": [],
                "doubts": [
                    (
                        "Do I need to install anything before I can practise here?",
                        "No. The lessons in this course run in the browser editor, so you can read, type, and run code "
                        "without setting up a local Python installation first.",
                    ),
                    (
                        "Is Python slower than C or Java?",
                        "For raw number crunching, yes, Python is usually slower because it is interpreted. In practice "
                        "most programs are limited by input/output or by developer time, which is exactly where Python wins.",
                    ),
                ],
            },
            {
                "slug": "your-first-program",
                "title": "Your First Program: print()",
                "lesson_type": LessonType.INTERACTIVE_CODE,
                "estimated_minutes": 10,
                "statement": {
                    "summary": "Use print() to send text to the output stream.",
                    "blocks": [
                        _text(
                            "print() is a built-in function. You call a function by writing its name followed by "
                            "parentheses, and anything inside the parentheses is an argument passed into it."
                        ),
                        _code(
                            "print(\"Hello\")            # one argument\n"
                            "print(\"Hello\", \"World\")   # two arguments, joined by a space\n"
                            "print()                     # no arguments, prints an empty line"
                        ),
                        _text(
                            "Text wrapped in quotes is called a string. Single and double quotes behave identically in "
                            "Python, so pick one style and stay consistent."
                        ),
                    ],
                    "task": "Print the exact line: Hello, Job Ready!",
                    "expected_output": "Hello, Job Ready!",
                },
                "starter_code": {
                    "python": "# Print the exact line: Hello, Job Ready!\n\n"
                },
                "solution": {
                    "python": "print(\"Hello, Job Ready!\")",
                    "explanation": "A single print() call with one string argument writes the text followed by a newline.",
                },
                "hints": [
                    ("The whole message including the comma and the exclamation mark goes inside one pair of quotes.", 0),
                    ("print(\"...\") - replace the dots with the message text.", 1),
                ],
                "doubts": [
                    (
                        "Why does my output have extra spaces?",
                        "print() inserts a space between each argument. print(\"Hello,\", \"Job Ready!\") produces the "
                        "same visible text but as two arguments; passing one complete string is safer when the exact "
                        "spacing matters.",
                    ),
                    (
                        "Do I need a semicolon at the end of the line?",
                        "No. Python ends a statement at the end of the line. Semicolons are legal but unusual and are "
                        "considered poor style.",
                    ),
                ],
            },
            {
                "slug": "getting-started-checkpoint",
                "title": "Checkpoint: Getting Started",
                "lesson_type": LessonType.CHECKPOINT,
                "estimated_minutes": 5,
                "statement": {
                    "summary": "Confirm the basics before moving on to variables.",
                    "blocks": [
                        _text("Answer the questions below. They review only what this module covered.")
                    ],
                    "questions": [
                        {
                            "prompt": "What does the Python interpreter do with your source file?",
                            "options": [
                                "Converts it to a machine-code executable before running anything",
                                "Reads and executes the instructions in order",
                                "Uploads it to a server for execution",
                                "Formats it and does nothing else",
                            ],
                            "answer_index": 1,
                            "explanation": "Python reads the file top to bottom and executes each statement as it goes.",
                        },
                        {
                            "prompt": "Which call prints an empty line?",
                            "options": ["print(\"\\n\\n\")", "print()", "print(empty)", "println()"],
                            "answer_index": 1,
                            "explanation": "print() with no arguments emits just the trailing newline.",
                        },
                        {
                            "prompt": "In Python, leading whitespace on a line is:",
                            "options": [
                                "Ignored completely",
                                "Only a style preference",
                                "Part of the grammar and defines code blocks",
                                "Not allowed",
                            ],
                            "answer_index": 2,
                            "explanation": "Indentation determines which statements belong to which block.",
                        },
                    ],
                },
                "hints": [],
                "doubts": [
                    (
                        "Do checkpoints affect my course progress?",
                        "Yes. Marking a checkpoint complete unlocks the next module and counts toward the course "
                        "progress bar, the same as any other lesson.",
                    )
                ],
            },
        ],
    },
    {
        "slug": "core-syntax",
        "title": "Core Syntax and Variables",
        "summary": "Names, numbers, strings, and converting between types.",
        "lessons": [
            {
                "slug": "variables-and-assignment",
                "title": "Variables and Assignment",
                "lesson_type": LessonType.CONCEPT,
                "estimated_minutes": 9,
                "statement": {
                    "summary": "A variable is a name bound to a value; assignment creates or rebinds that name.",
                    "blocks": [
                        _text(
                            "The equals sign in Python is assignment, not mathematical equality. The right-hand side is "
                            "evaluated first, and the resulting value is bound to the name on the left."
                        ),
                        _code(
                            "total = 10          # bind the name 'total' to 10\n"
                            "total = total + 5   # evaluate 10 + 5, rebind 'total' to 15\n"
                            "print(total)        # 15"
                        ),
                        _bullets(
                            "Naming rules that the interpreter enforces",
                            [
                                "Names may contain letters, digits, and underscores",
                                "A name cannot start with a digit",
                                "Names are case-sensitive: score and Score are different",
                                "Reserved words such as if, for, and class cannot be used as names",
                            ],
                        ),
                        _tip(
                            "Use snake_case for variable names (total_marks, not totalMarks). It is the convention every "
                            "Python codebase follows."
                        ),
                    ],
                },
                "hints": [],
                "doubts": [
                    (
                        "What happens if I use a variable before assigning it?",
                        "Python raises a NameError at the moment the line runs, because the name has never been bound "
                        "to a value.",
                    ),
                    (
                        "Can one variable hold a number and later a string?",
                        "Yes. Python is dynamically typed, so rebinding a name to a different type is legal. It can "
                        "still make code harder to follow, so do it deliberately.",
                    ),
                ],
            },
            {
                "slug": "numbers-and-strings",
                "title": "Numbers and Strings",
                "lesson_type": LessonType.INTERACTIVE_CODE,
                "estimated_minutes": 12,
                "statement": {
                    "summary": "Work with int, float, and str, and combine them safely with f-strings.",
                    "blocks": [
                        _text(
                            "int holds whole numbers, float holds decimals, and str holds text. Arithmetic between an "
                            "int and a float produces a float."
                        ),
                        _code(
                            "count = 4          # int\n"
                            "price = 12.5       # float\n"
                            "label = \"pens\"     # str\n"
                            "print(count * price)   # 50.0"
                        ),
                        _text(
                            "An f-string lets you embed expressions directly inside a string. Prefix the string with f "
                            "and put the expression inside curly braces."
                        ),
                        _code("print(f\"{count} {label} cost {count * price}\")"),
                    ],
                    "task": "Given items = 4 and unit_price = 12.5, print exactly: 4 items cost 50.0",
                    "expected_output": "4 items cost 50.0",
                },
                "starter_code": {
                    "python": "items = 4\nunit_price = 12.5\n\n# Print: 4 items cost 50.0\n"
                },
                "solution": {
                    "python": "items = 4\nunit_price = 12.5\nprint(f\"{items} items cost {items * unit_price}\")",
                    "explanation": "int * float yields a float, so 4 * 12.5 renders as 50.0 inside the f-string.",
                },
                "hints": [
                    ("Start the string with f so the braces are evaluated instead of printed literally.", 0),
                    ("The multiplication can go straight inside the braces: {items * unit_price}.", 1),
                ],
                "doubts": [
                    (
                        "Why is the result 50.0 and not 50?",
                        "Multiplying an int by a float always produces a float, and floats always display a decimal part.",
                    ),
                    (
                        "What is the difference between \"4\" and 4?",
                        "\"4\" is a string of one character; 4 is an integer. \"4\" * 2 gives \"44\", while 4 * 2 gives 8.",
                    ),
                ],
            },
            {
                "slug": "type-conversion",
                "title": "Type Conversion and input()",
                "lesson_type": LessonType.INTERACTIVE_CODE,
                "estimated_minutes": 11,
                "statement": {
                    "summary": "Convert between types explicitly with int(), float(), and str().",
                    "blocks": [
                        _text(
                            "Python will not silently convert a string into a number. \"5\" + 1 raises a TypeError. "
                            "You convert explicitly instead."
                        ),
                        _code(
                            "raw = \"5\"\n"
                            "number = int(raw)   # 5 as an int\n"
                            "print(number + 1)   # 6\n"
                            "print(str(number) + \"1\")  # \"51\""
                        ),
                        _text(
                            "This matters most when reading input. input() always returns a string, even when the user "
                            "types digits, so numeric work needs a conversion first."
                        ),
                    ],
                    "task": "Convert the string \"27\" to an integer, add 3 to it, and print the result.",
                    "expected_output": "30",
                },
                "starter_code": {
                    "python": "raw_value = \"27\"\n\n# Convert raw_value to an int, add 3, and print the result\n"
                },
                "solution": {
                    "python": "raw_value = \"27\"\nprint(int(raw_value) + 3)",
                    "explanation": "int() parses the digits into an integer, so normal arithmetic applies.",
                },
                "hints": [
                    ("int(\"27\") returns the integer 27.", 0),
                    ("Wrap the conversion in print(): print(int(raw_value) + 3).", 1),
                ],
                "doubts": [
                    (
                        "What happens if the string is not a number?",
                        "int(\"abc\") raises a ValueError. Validate or wrap the conversion in try/except when the input "
                        "comes from a user.",
                    ),
                    (
                        "Does int(3.9) round to 4?",
                        "No, it truncates toward zero and gives 3. Use round(3.9) when you want 4.",
                    ),
                ],
            },
            {
                "slug": "core-syntax-checkpoint",
                "title": "Checkpoint: Syntax and Variables",
                "lesson_type": LessonType.CHECKPOINT,
                "estimated_minutes": 5,
                "statement": {
                    "summary": "Review assignment, types, and conversion.",
                    "blocks": [_text("Three quick questions on the module you just finished.")],
                    "questions": [
                        {
                            "prompt": "What is the value of x after: x = 2; x = x * 3?",
                            "options": ["2", "3", "6", "An error, x cannot reference itself"],
                            "answer_index": 2,
                            "explanation": "The right side evaluates to 6 first, then rebinds x.",
                        },
                        {
                            "prompt": "What does \"7\" + 2 do?",
                            "options": ["Returns 9", "Returns \"72\"", "Raises a TypeError", "Returns 72"],
                            "answer_index": 2,
                            "explanation": "Python refuses to add a str and an int implicitly.",
                        },
                        {
                            "prompt": "Which name is invalid in Python?",
                            "options": ["total_marks", "marks2", "2marks", "_marks"],
                            "answer_index": 2,
                            "explanation": "A name cannot begin with a digit.",
                        },
                    ],
                },
                "hints": [],
                "doubts": [],
            },
        ],
    },
    {
        "slug": "control-flow",
        "title": "Control Flow and Loops",
        "summary": "Make decisions with if/elif/else and repeat work with for and while.",
        "lessons": [
            {
                "slug": "conditionals",
                "title": "if, elif, and else",
                "lesson_type": LessonType.CONCEPT,
                "estimated_minutes": 10,
                "statement": {
                    "summary": "Branching runs a block only when its condition is true.",
                    "blocks": [
                        _text(
                            "An if statement evaluates a condition to True or False and runs the indented block below "
                            "it only when the condition is True. elif checks another condition, and else catches "
                            "everything remaining."
                        ),
                        _code(
                            "marks = 72\n"
                            "if marks >= 75:\n"
                            "    grade = \"Distinction\"\n"
                            "elif marks >= 40:\n"
                            "    grade = \"Pass\"\n"
                            "else:\n"
                            "    grade = \"Fail\"\n"
                            "print(grade)   # Pass"
                        ),
                        _bullets(
                            "Comparison operators",
                            [
                                "== equal to, != not equal to",
                                "< and > strictly less or greater",
                                "<= and >= inclusive comparisons",
                                "and, or, not to combine conditions",
                            ],
                        ),
                        _tip(
                            "Only the first matching branch runs. Order your conditions from most specific to most "
                            "general or a broad condition will shadow the narrow ones below it."
                        ),
                    ],
                },
                "hints": [],
                "doubts": [
                    (
                        "Why does my code fail with an IndentationError?",
                        "The block under if must be indented consistently, four spaces by convention, and every line of "
                        "that block must use the same indentation.",
                    ),
                    (
                        "Is elif the same as writing a second if?",
                        "No. A second if is evaluated even when the first one matched. elif is only checked when every "
                        "condition above it was False.",
                    ),
                ],
            },
            {
                "slug": "for-loops",
                "title": "for Loops and range()",
                "lesson_type": LessonType.INTERACTIVE_CODE,
                "estimated_minutes": 12,
                "statement": {
                    "summary": "A for loop repeats a block once for every item in a sequence.",
                    "blocks": [
                        _text(
                            "range(start, stop) produces the numbers from start up to but not including stop. It is the "
                            "usual way to run a loop a fixed number of times."
                        ),
                        _code(
                            "for number in range(1, 4):\n"
                            "    print(number)\n"
                            "# prints 1, then 2, then 3"
                        ),
                        _text(
                            "Loops also iterate directly over strings and lists, which is usually clearer than indexing "
                            "by position."
                        ),
                        _code(
                            "total = 0\n"
                            "for value in [4, 7, 9]:\n"
                            "    total = total + value\n"
                            "print(total)   # 20"
                        ),
                    ],
                    "task": "Print the sum of all integers from 1 to 10 inclusive.",
                    "expected_output": "55",
                },
                "starter_code": {
                    "python": "total = 0\n\n# Add every number from 1 to 10 to total, then print total\n"
                },
                "solution": {
                    "python": "total = 0\nfor number in range(1, 11):\n    total = total + number\nprint(total)",
                    "explanation": "range(1, 11) stops before 11, so it yields 1 through 10; the running total ends at 55.",
                },
                "hints": [
                    ("range() excludes its stop value, so reaching 10 needs range(1, 11).", 0),
                    ("Keep print(total) outside the loop, or you will print a value on every pass.", 1),
                    ("total = total + number inside the loop accumulates the sum.", 2),
                ],
                "doubts": [
                    (
                        "Why does range(1, 10) stop at 9?",
                        "The stop value is exclusive. This makes range(0, n) produce exactly n items, which lines up "
                        "with zero-based indexing.",
                    ),
                    (
                        "Can I loop backwards?",
                        "Yes, range takes a third step argument: range(10, 0, -1) counts down from 10 to 1.",
                    ),
                ],
            },
            {
                "slug": "while-loops",
                "title": "while Loops",
                "lesson_type": LessonType.INTERACTIVE_CODE,
                "estimated_minutes": 11,
                "statement": {
                    "summary": "A while loop repeats for as long as its condition stays true.",
                    "blocks": [
                        _text(
                            "Use while when you do not know in advance how many iterations you need. Something inside "
                            "the loop must eventually make the condition False, or the loop never ends."
                        ),
                        _code(
                            "count = 3\n"
                            "while count > 0:\n"
                            "    print(count)\n"
                            "    count = count - 1\n"
                            "print(\"Done\")"
                        ),
                        _tip(
                            "If a while loop appears to hang, the first thing to check is whether the variable in the "
                            "condition is actually being updated inside the body."
                        ),
                    ],
                    "task": "Starting from n = 40, keep halving it with integer division (n = n // 2) and print each value until n becomes 0.",
                    "expected_output": "20\n10\n5\n2\n1\n0",
                },
                "starter_code": {
                    "python": "n = 40\n\n# Halve n with // until it reaches 0, printing each new value\n"
                },
                "solution": {
                    "python": "n = 40\nwhile n > 0:\n    n = n // 2\n    print(n)",
                    "explanation": "// is floor division, so the sequence 20, 10, 5, 2, 1, 0 terminates the loop.",
                },
                "hints": [
                    ("// discards the remainder, so 5 // 2 is 2.", 0),
                    ("Update n before printing so the first line shown is 20 rather than 40.", 1),
                ],
                "doubts": [
                    (
                        "What is the difference between / and //?",
                        "/ always produces a float (5 / 2 is 2.5), while // floors the result to an integer (5 // 2 is 2).",
                    ),
                    (
                        "How do I break out of a loop early?",
                        "The break statement exits the nearest enclosing loop immediately; continue skips to the next "
                        "iteration instead.",
                    ),
                ],
            },
            {
                "slug": "control-flow-checkpoint",
                "title": "Checkpoint: Control Flow",
                "lesson_type": LessonType.CHECKPOINT,
                "estimated_minutes": 5,
                "statement": {
                    "summary": "Review branching and looping.",
                    "blocks": [_text("Answer all three to close out the module.")],
                    "questions": [
                        {
                            "prompt": "How many values does range(2, 7) produce?",
                            "options": ["4", "5", "6", "7"],
                            "answer_index": 1,
                            "explanation": "It yields 2, 3, 4, 5, 6 - five values, stopping before 7.",
                        },
                        {
                            "prompt": "When is an elif branch evaluated?",
                            "options": [
                                "Always, regardless of earlier branches",
                                "Only when every condition above it was False",
                                "Only when the if branch was True",
                                "Only when an else exists",
                            ],
                            "answer_index": 1,
                            "explanation": "elif is checked only after all preceding conditions fail.",
                        },
                        {
                            "prompt": "What is the most common cause of an infinite while loop?",
                            "options": [
                                "Using a comparison operator",
                                "Printing inside the loop",
                                "Never updating the variable in the condition",
                                "Indenting with four spaces",
                            ],
                            "answer_index": 2,
                            "explanation": "If the condition variable never changes, the condition stays True forever.",
                        },
                    ],
                },
                "hints": [],
                "doubts": [],
            },
        ],
    },
    {
        "slug": "functions-collections",
        "title": "Functions and Collections",
        "summary": "Package logic into functions and store data in lists and dictionaries.",
        "lessons": [
            {
                "slug": "defining-functions",
                "title": "Defining and Calling Functions",
                "lesson_type": LessonType.CONCEPT,
                "estimated_minutes": 10,
                "statement": {
                    "summary": "def creates a reusable block of logic with named inputs and a return value.",
                    "blocks": [
                        _text(
                            "A function groups statements under a name so you can run them again with different inputs. "
                            "Parameters are the names in the definition; arguments are the values you pass at the call site."
                        ),
                        _code(
                            "def area(width, height):\n"
                            "    return width * height\n"
                            "\n"
                            "print(area(3, 4))   # 12\n"
                            "print(area(5, 2))   # 10"
                        ),
                        _text(
                            "return sends a value back to the caller and ends the function immediately. A function "
                            "without a return statement returns None."
                        ),
                        _bullets(
                            "Why functions matter in interviews",
                            [
                                "They make a solution testable one piece at a time",
                                "They give reviewers a name for each step of your reasoning",
                                "They keep the main flow short and readable",
                            ],
                        ),
                    ],
                },
                "hints": [],
                "doubts": [
                    (
                        "What is the difference between return and print?",
                        "print displays text and returns nothing useful. return hands a value back to the caller so it "
                        "can be stored or used in further calculations.",
                    ),
                    (
                        "Can a function be defined after it is called?",
                        "The def must have executed before the call runs. Defining functions at the top of the file "
                        "avoids the problem entirely.",
                    ),
                ],
            },
            {
                "slug": "lists-and-tuples",
                "title": "Lists and Tuples",
                "lesson_type": LessonType.INTERACTIVE_CODE,
                "estimated_minutes": 12,
                "statement": {
                    "summary": "A list is an ordered, mutable sequence; a tuple is its immutable counterpart.",
                    "blocks": [
                        _code(
                            "scores = [40, 72, 65]\n"
                            "scores.append(90)      # [40, 72, 65, 90]\n"
                            "print(scores[0])       # 40, first item\n"
                            "print(scores[-1])      # 90, last item\n"
                            "print(len(scores))     # 4"
                        ),
                        _text(
                            "Indexing starts at 0, and negative indexes count from the end. Slicing with scores[1:3] "
                            "returns a new list containing positions 1 and 2."
                        ),
                        _text(
                            "A tuple uses parentheses and cannot be modified after creation, which makes it a good fit "
                            "for fixed records such as coordinates."
                        ),
                        _code("point = (3, 7)\nprint(point[0] + point[1])   # 10"),
                    ],
                    "task": "Given scores = [40, 72, 65, 90], print the highest score and the average on separate lines. The average should print as 66.75.",
                    "expected_output": "90\n66.75",
                },
                "starter_code": {
                    "python": "scores = [40, 72, 65, 90]\n\n# Print the maximum score, then the average\n"
                },
                "solution": {
                    "python": "scores = [40, 72, 65, 90]\nprint(max(scores))\nprint(sum(scores) / len(scores))",
                    "explanation": "max() finds the largest item; sum() / len() gives the mean as a float.",
                },
                "hints": [
                    ("max() and sum() are built in and both accept a list directly.", 0),
                    ("Use / rather than // so the average keeps its decimal part.", 1),
                ],
                "doubts": [
                    (
                        "When should I use a tuple instead of a list?",
                        "Use a tuple when the collection should not change after creation. It signals intent and can be "
                        "used as a dictionary key, which a list cannot.",
                    ),
                    (
                        "Does append return the new list?",
                        "No, it returns None and modifies the list in place, so scores = scores.append(1) would set "
                        "scores to None.",
                    ),
                ],
            },
            {
                "slug": "dictionaries",
                "title": "Dictionaries",
                "lesson_type": LessonType.INTERACTIVE_CODE,
                "estimated_minutes": 12,
                "statement": {
                    "summary": "A dictionary maps unique keys to values with fast lookup.",
                    "blocks": [
                        _code(
                            "student = {\"name\": \"Asha\", \"marks\": 82}\n"
                            "print(student[\"name\"])          # Asha\n"
                            "student[\"marks\"] = 88            # update\n"
                            "student[\"branch\"] = \"CSE\"       # add a new key\n"
                            "print(student.get(\"email\", \"-\"))  # '-' when the key is missing"
                        ),
                        _text(
                            "Square-bracket access raises a KeyError when the key is absent, while .get() returns a "
                            "default instead. Looping over a dictionary yields its keys."
                        ),
                        _code(
                            "for key in student:\n"
                            "    print(key, student[key])"
                        ),
                        _tip(
                            "Counting with a dictionary is one of the most common interview patterns: read an item, and "
                            "increase its stored count."
                        ),
                    ],
                    "task": "Count how many times each character appears in \"banana\" and print the count for the letter a.",
                    "expected_output": "3",
                },
                "starter_code": {
                    "python": "word = \"banana\"\ncounts = {}\n\n# Fill counts with each character's frequency, then print counts[\"a\"]\n"
                },
                "solution": {
                    "python": "word = \"banana\"\ncounts = {}\nfor char in word:\n    counts[char] = counts.get(char, 0) + 1\nprint(counts[\"a\"])",
                    "explanation": "counts.get(char, 0) treats an unseen character as 0, so the increment always works.",
                },
                "hints": [
                    ("Iterate the string directly: for char in word.", 0),
                    ("counts.get(char, 0) + 1 handles both the first and later occurrences.", 1),
                    ("banana contains three a characters.", 2),
                ],
                "doubts": [
                    (
                        "Can two keys be the same?",
                        "No. Assigning to an existing key overwrites its value rather than adding a second entry.",
                    ),
                    (
                        "Are dictionaries ordered?",
                        "Since Python 3.7 dictionaries preserve insertion order, so iteration follows the order keys "
                        "were first added.",
                    ),
                ],
            },
            {
                "slug": "functions-collections-checkpoint",
                "title": "Checkpoint: Functions and Collections",
                "lesson_type": LessonType.CHECKPOINT,
                "estimated_minutes": 6,
                "statement": {
                    "summary": "Final review for the course.",
                    "blocks": [_text("Finish these questions to complete Python Foundations.")],
                    "questions": [
                        {
                            "prompt": "What does a function return when it has no return statement?",
                            "options": ["0", "An empty string", "None", "It raises an error"],
                            "answer_index": 2,
                            "explanation": "Python implicitly returns None when the function body ends.",
                        },
                        {
                            "prompt": "Which expression safely reads a possibly missing dictionary key?",
                            "options": [
                                "data[\"key\"]",
                                "data.get(\"key\", 0)",
                                "data.key",
                                "data.find(\"key\")",
                            ],
                            "answer_index": 1,
                            "explanation": ".get() returns the supplied default instead of raising KeyError.",
                        },
                        {
                            "prompt": "What is scores[-1] for scores = [4, 8, 15]?",
                            "options": ["4", "8", "15", "An IndexError"],
                            "answer_index": 2,
                            "explanation": "Negative indexes count backwards, so -1 is the last element.",
                        },
                    ],
                },
                "hints": [],
                "doubts": [],
            },
        ],
    },
]


# Outline shown for languages whose guided course has not been written yet.
LANGUAGE_PATH_SECTIONS = [
    "Getting Started",
    "Syntax",
    "Variables and Data Types",
    "Operators",
    "Control Flow",
    "Functions",
    "Collections",
]

# Sections for a language path that is backed by a real course, mapped to course modules.
COURSE_PATH_SECTIONS = [
    ("Getting Started", "getting-started"),
    ("Syntax and Variables", "core-syntax"),
    ("Control Flow", "control-flow"),
    ("Functions and Collections", "functions-collections"),
]

LANGUAGE_PATHS = [
    {
        "slug": "learn-python",
        "title": "Python",
        "language": "python",
        "short_description": "Start from zero and build up to functions, lists, and dictionaries.",
        "availability": PathAvailability.AVAILABLE,
        "featured": True,
        "course_slug": "python-foundations",
        "estimated_minutes": 120,
    },
    {
        "slug": "learn-java",
        "title": "Java",
        "language": "java",
        "short_description": "Classes, types, and the JVM fundamentals used in campus placements.",
        "availability": PathAvailability.COMING_SOON,
        "featured": False,
        "course_slug": None,
        "estimated_minutes": None,
    },
    {
        "slug": "learn-c",
        "title": "C",
        "language": "c",
        "short_description": "Memory, pointers, and the procedural core that every other language borrows from.",
        "availability": PathAvailability.COMING_SOON,
        "featured": False,
        "course_slug": None,
        "estimated_minutes": None,
    },
    {
        "slug": "learn-cpp",
        "title": "C++",
        "language": "cpp",
        "short_description": "C fundamentals plus the STL containers interviewers expect you to know.",
        "availability": PathAvailability.COMING_SOON,
        "featured": False,
        "course_slug": None,
        "estimated_minutes": None,
    },
    {
        "slug": "learn-javascript",
        "title": "JavaScript",
        "language": "javascript",
        "short_description": "The language of the browser, from values and scope to array methods.",
        "availability": PathAvailability.COMING_SOON,
        "featured": False,
        "course_slug": None,
        "estimated_minutes": None,
    },
]

BEGINNER_DSA_PATHS = [
    ("beginner-strings", "Strings", "strings", "Traverse, slice, and compare strings without reaching for a library."),
    ("beginner-arrays", "Arrays", "arrays", "Indexing, prefix sums, and the scanning patterns most problems start with."),
    ("beginner-basic-math", "Basic Math", "basics", "Divisibility, digits, primes, and the arithmetic warm-ups interviewers open with."),
    ("beginner-sorting", "Sorting", "sorting", "Order data first, then watch how many problems become straightforward."),
    ("beginner-hashing", "Hashing Basics", "hash-maps", "Trade memory for speed with sets and dictionaries."),
    ("beginner-two-pointers", "Two Pointers", "two-pointers", "Walk a sequence from both ends to replace a nested loop."),
    ("beginner-searching", "Basic Searching", "searching", "Linear scans and your first look at binary search."),
]

DATA_STRUCTURE_PATHS = [
    ("ds-arrays", "Arrays and Strings", "arrays", PathAvailability.AVAILABLE),
    ("ds-hash-tables", "Hash Tables", "hash-maps", PathAvailability.AVAILABLE),
    ("ds-linked-lists", "Linked Lists", "linked-lists", PathAvailability.COMING_SOON),
    ("ds-stacks", "Stacks", "stack", PathAvailability.COMING_SOON),
    ("ds-queues", "Queues and Deques", "queue", PathAvailability.COMING_SOON),
    ("ds-trees", "Trees and Binary Trees", "trees", PathAvailability.COMING_SOON),
    ("ds-heaps", "Heaps and Priority Queues", None, PathAvailability.COMING_SOON),
    ("ds-graphs", "Graphs", None, PathAvailability.COMING_SOON),
    ("ds-tries", "Tries", None, PathAvailability.COMING_SOON),
    ("ds-union-find", "Disjoint Set Union", None, PathAvailability.COMING_SOON),
]

ALGORITHM_PATHS = [
    ("algo-sorting", "Sorting Algorithms", "sorting", PathAvailability.AVAILABLE),
    ("algo-binary-search", "Binary Search", "binary-search", PathAvailability.AVAILABLE),
    ("algo-two-pointers", "Two Pointers", "two-pointers", PathAvailability.AVAILABLE),
    ("algo-sliding-window", "Sliding Window", "sliding-window", PathAvailability.COMING_SOON),
    ("algo-recursion", "Recursion", "recursion", PathAvailability.COMING_SOON),
    ("algo-backtracking", "Backtracking", None, PathAvailability.COMING_SOON),
    ("algo-greedy", "Greedy Algorithms", None, PathAvailability.COMING_SOON),
    ("algo-dynamic-programming", "Dynamic Programming", "dynamic-programming", PathAvailability.COMING_SOON),
    ("algo-graph-traversal", "Graph Traversal", None, PathAvailability.COMING_SOON),
    ("algo-bit-manipulation", "Bit Manipulation", None, PathAvailability.COMING_SOON),
]

DIFFICULTY_PATHS = [
    ("difficulty-beginner", "Beginner", PracticePathDifficulty.BEGINNER, "beginner", "Guided problems with heavy scaffolding and worked explanations."),
    ("difficulty-easy", "Easy", PracticePathDifficulty.EASY, "easy", "Single-concept problems you should finish inside fifteen minutes."),
    ("difficulty-medium", "Medium", PracticePathDifficulty.MEDIUM, "medium", "Two ideas combined - the band most interview rounds sit in."),
    ("difficulty-hard", "Hard", PracticePathDifficulty.HARD, "hard", "Multi-step problems for contests and senior interview loops."),
]

PROJECT_CATEGORIES = [
    ("python", "Python Projects", "Automation scripts, command-line tools, and small services written in pure Python.", "Python"),
    ("java", "Java Projects", "Console and desktop applications that exercise object-oriented design.", "Java"),
    ("javascript", "JavaScript Projects", "Browser-based apps built with vanilla JavaScript and the DOM.", "JavaScript"),
    ("web-development", "Web Development Projects", "Responsive multi-page sites using HTML, CSS, and modern layout techniques.", "HTML/CSS"),
    ("mern", "MERN Stack Projects", "Full-stack applications with MongoDB, Express, React, and Node.", "MERN"),
    ("sql", "SQL and Database Projects", "Schema design, reporting queries, and data modelling exercises.", "SQL"),
    ("data-analysis", "Data Analysis Projects", "Clean, aggregate, and visualise real datasets end to end.", "Pandas"),
    ("machine-learning", "Machine Learning Projects", "Classical models from feature engineering through evaluation.", "scikit-learn"),
    ("deep-learning", "Deep Learning Projects", "Neural networks for vision and sequence tasks.", "PyTorch"),
    ("generative-ai", "Generative AI Projects", "Retrieval-augmented apps, prompt pipelines, and agent workflows.", "LLM"),
    ("spring-boot", "Spring Boot Projects", "REST services, persistence, and layered architecture in Java.", "Spring Boot"),
    ("devops", "DevOps Projects", "Pipelines, containers, and deployment automation.", "Docker"),
    ("cloud", "Cloud Projects", "Deploy and operate workloads on managed cloud services.", "Cloud"),
    ("cybersecurity", "Cybersecurity Projects", "Hands-on labs covering web, network, and application security.", "Security"),
]


# ----------------------------------------------------------------------
# Seed helpers
# ----------------------------------------------------------------------


async def _ensure_companies(session) -> dict[str, Company]:
    companies: dict[str, Company] = {}
    for name in LEARN_COMPANIES:
        slug = slugify(name)
        company = (
            await session.execute(select(Company).where(Company.slug == slug))
        ).scalar_one_or_none()
        if company is None:
            company = Company(name=name, slug=slug)
            session.add(company)
            await session.flush()
        companies[name] = company
    return companies


async def _problems_for_topic(session, topic_slug: str | None, limit: int = 6) -> list[CodingProblem]:
    if not topic_slug:
        return []
    topic_ids = (
        await session.execute(select(Topic.id).where(Topic.slug == topic_slug))
    ).scalars().all()
    if not topic_ids:
        return []
    rows = (
        await session.execute(
            select(CodingProblem)
            .where(CodingProblem.topic_id.in_(topic_ids), CodingProblem.is_active.is_(True))
            .order_by(CodingProblem.title)
            .limit(limit)
        )
    ).scalars().all()
    return list(rows)


async def _ensure_path(session, slug: str, **kwargs: Any) -> tuple[PracticePath, bool]:
    path = (
        await session.execute(select(PracticePath).where(PracticePath.slug == slug))
    ).scalar_one_or_none()
    if path is not None:
        return path, False
    path = PracticePath(slug=slug, **kwargs)
    session.add(path)
    await session.flush()
    return path, True


def _add_section(session, path: PracticePath, title: str, sort_order: int, key: str | None = None) -> PracticePathSection:
    section = PracticePathSection(
        path_id=path.id,
        title=title,
        section_key=key or slugify(title),
        sort_order=sort_order,
    )
    session.add(section)
    return section


async def _ensure_python_course(session) -> Course:
    course = (
        await session.execute(select(Course).where(Course.slug == "python-foundations"))
    ).scalar_one_or_none()
    if course is not None:
        return course

    course = Course(
        slug="python-foundations",
        title="Python Foundations",
        summary=(
            "A hands-on introduction to Python for placement preparation. Read a short concept, type the code "
            "yourself, then confirm what you learned at each checkpoint."
        ),
        level=CourseLevel.BEGINNER,
        primary_language_key="python",
        estimated_minutes=150,
        is_published=True,
        is_featured=True,
        sort_order=1,
        certificate_enabled=False,
    )
    session.add(course)
    await session.flush()

    for module_index, module_spec in enumerate(PYTHON_COURSE_MODULES):
        module = CourseModule(
            course_id=course.id,
            slug=module_spec["slug"],
            title=module_spec["title"],
            summary=module_spec["summary"],
            sort_order=module_index,
        )
        session.add(module)
        await session.flush()

        for lesson_index, spec in enumerate(module_spec["lessons"]):
            lesson = CourseLesson(
                module_id=module.id,
                slug=spec["slug"],
                title=spec["title"],
                sort_order=lesson_index,
                lesson_type=spec["lesson_type"],
                statement_json=spec["statement"],
                estimated_minutes=spec.get("estimated_minutes"),
                unlock_mode=LessonUnlockMode.PREVIOUS_COMPLETE,
                solution_reveal=SolutionRevealPolicy.AFTER_COMPLETION,
                solution_json=spec.get("solution"),
                starter_code=spec.get("starter_code") or {},
                is_published=True,
                # Judge0 is optional for this course: learners can mark a lesson complete
                # after typing the code, without a graded submission.
                completion_requires_submit=False,
            )
            session.add(lesson)
            await session.flush()

            for hint_index, (hint_text, unlock_after) in enumerate(spec.get("hints", [])):
                session.add(
                    LessonHint(
                        lesson_id=lesson.id,
                        hint_text=hint_text,
                        sort_order=hint_index,
                        unlock_after_attempts=unlock_after,
                    )
                )
            for doubt_index, (question, answer) in enumerate(spec.get("doubts", [])):
                session.add(
                    LessonDoubt(
                        lesson_id=lesson.id,
                        question=question,
                        answer=answer,
                        sort_order=doubt_index,
                    )
                )
    await session.flush()
    return course


async def _ensure_projects(session) -> None:
    for index, (key, title, description, technology) in enumerate(PROJECT_CATEGORIES):
        slug = f"{key}-projects"
        existing = await session.scalar(select(Project.id).where(Project.slug == slug))
        if existing is not None:
            continue
        session.add(
            Project(
                slug=slug,
                title=title,
                short_description=description,
                description=(
                    f"{description} Guided builds for this track are being written now - "
                    "follow the track to be notified when the first project ships."
                ),
                difficulty=PracticePathDifficulty.BEGINNER,
                technology=technology,
                category_key=key,
                is_published=True,
                is_featured=False,
                sort_order=index,
                availability=PathAvailability.COMING_SOON,
            )
        )

    sample_slug = "python-cli-toolkit"
    if await session.scalar(select(Project.id).where(Project.slug == sample_slug)) is None:
        project = Project(
            slug=sample_slug,
            title="Python CLI Toolkit",
            short_description="Build a small command-line toolkit that reports on a text file.",
            description=(
                "Write a self-contained command-line program that reads a text file and reports word counts and "
                "the most frequent words. You will practise file handling, dictionaries, sorting, and argument "
                "parsing - the same building blocks that show up in scripting interview rounds."
            ),
            difficulty=PracticePathDifficulty.BEGINNER,
            technology="Python",
            category_key="python",
            estimated_minutes=90,
            is_published=True,
            is_featured=True,
            sort_order=0,
            availability=PathAvailability.AVAILABLE,
        )
        session.add(project)
        await session.flush()

        module = ProjectModule(project_id=project.id, title="Core Toolkit", sort_order=0)
        session.add(module)
        await session.flush()

        session.add(
            ProjectTask(
                module_id=module.id,
                title="Read a file and count words",
                sort_order=0,
                summary=(
                    "Open a text file, split its contents into words, and print the total count. Handle a missing "
                    "file cleanly instead of letting the traceback escape."
                ),
            )
        )
        session.add(
            ProjectTask(
                module_id=module.id,
                title="Report the top five most frequent words",
                sort_order=1,
                summary=(
                    "Build a frequency dictionary, sort it by count descending, and print the five most common "
                    "words with their counts. Ignore case so 'The' and 'the' are counted together."
                ),
            )
        )
    await session.flush()


async def _ensure_language_paths(session, course: Course) -> None:
    lessons_by_module: dict[str, list[CourseLesson]] = {}
    modules = (
        await session.execute(
            select(CourseModule).where(CourseModule.course_id == course.id).order_by(CourseModule.sort_order)
        )
    ).scalars().all()
    for module in modules:
        lessons = (
            await session.execute(
                select(CourseLesson)
                .where(CourseLesson.module_id == module.id)
                .order_by(CourseLesson.sort_order)
            )
        ).scalars().all()
        lessons_by_module[module.slug] = list(lessons)

    for index, spec in enumerate(LANGUAGE_PATHS):
        path, created = await _ensure_path(
            session,
            spec["slug"],
            title=spec["title"],
            short_description=spec["short_description"],
            description=(
                f"A structured route through {spec['title']} for placement preparation, starting from the very "
                "first program and ending with the constructs interviewers actually ask about."
            ),
            path_type=PracticePathType.LANGUAGE,
            difficulty=PracticePathDifficulty.BEGINNER,
            language=spec["language"],
            estimated_minutes=spec["estimated_minutes"],
            availability=spec["availability"],
            is_active=True,
            is_featured=spec["featured"],
            sort_order=index,
            icon_key=spec["language"],
        )
        if not created:
            continue

        if spec["course_slug"] is None:
            for section_index, title in enumerate(LANGUAGE_PATH_SECTIONS):
                _add_section(session, path, title, section_index)
            continue

        # Course-backed paths mirror the course modules one-to-one so no lesson is listed twice.
        for section_index, (title, module_slug) in enumerate(COURSE_PATH_SECTIONS):
            section = _add_section(session, path, title, section_index)
            await session.flush()

            sort_order = 0
            if section_index == 0:
                session.add(
                    PracticePathItem(
                        section_id=section.id,
                        item_type=PracticePathItemType.COURSE,
                        title=course.title,
                        sort_order=sort_order,
                        course_id=course.id,
                    )
                )
                sort_order += 1
            for lesson in lessons_by_module.get(module_slug, []):
                session.add(
                    PracticePathItem(
                        section_id=section.id,
                        item_type=PracticePathItemType.LESSON,
                        title=lesson.title,
                        sort_order=sort_order,
                        lesson_id=lesson.id,
                    )
                )
                sort_order += 1
    await session.flush()


async def _ensure_topic_path(
    session,
    *,
    slug: str,
    title: str,
    topic_slug: str | None,
    description: str,
    path_type: PracticePathType,
    difficulty: PracticePathDifficulty,
    availability: PathAvailability,
    sort_order: int,
) -> None:
    path, created = await _ensure_path(
        session,
        slug,
        title=title,
        short_description=description,
        description=description,
        path_type=path_type,
        difficulty=difficulty,
        estimated_minutes=None,
        availability=availability,
        is_active=True,
        is_featured=False,
        sort_order=sort_order,
        icon_key=topic_slug,
    )
    if not created:
        return

    section = _add_section(session, path, "Practice Problems", 0)
    await session.flush()

    problems = await _problems_for_topic(session, topic_slug)
    if problems:
        for problem_index, problem in enumerate(problems):
            session.add(
                PracticePathItem(
                    section_id=section.id,
                    item_type=PracticePathItemType.CODING_PROBLEM,
                    title=problem.title,
                    sort_order=problem_index,
                    coding_problem_id=problem.id,
                )
            )
    else:
        session.add(
            PracticePathItem(
                section_id=section.id,
                item_type=PracticePathItemType.EXTERNAL_ROUTE,
                title=f"Browse all {title} problems",
                sort_order=0,
                external_route=f"/practice/dsa?topic={topic_slug or slugify(title)}",
            )
        )


async def _ensure_dsa_paths(session) -> None:
    for index, (slug, title, topic_slug, description) in enumerate(BEGINNER_DSA_PATHS):
        await _ensure_topic_path(
            session,
            slug=slug,
            title=title,
            topic_slug=topic_slug,
            description=description,
            path_type=PracticePathType.BEGINNER_DSA,
            difficulty=PracticePathDifficulty.BEGINNER,
            availability=PathAvailability.AVAILABLE,
            sort_order=index,
        )
    await session.flush()


async def _ensure_structure_and_algorithm_paths(session) -> None:
    for index, (slug, title, topic_slug, availability) in enumerate(DATA_STRUCTURE_PATHS):
        await _ensure_topic_path(
            session,
            slug=slug,
            title=title,
            topic_slug=topic_slug,
            description=f"Core operations, trade-offs, and interview patterns for {title.lower()}.",
            path_type=PracticePathType.DATA_STRUCTURE,
            difficulty=PracticePathDifficulty.EASY,
            availability=availability,
            sort_order=index,
        )
    for index, (slug, title, topic_slug, availability) in enumerate(ALGORITHM_PATHS):
        await _ensure_topic_path(
            session,
            slug=slug,
            title=title,
            topic_slug=topic_slug,
            description=f"Recognise when {title.lower()} applies, then drill it until the pattern is automatic.",
            path_type=PracticePathType.ALGORITHM,
            difficulty=PracticePathDifficulty.MEDIUM,
            availability=availability,
            sort_order=index,
        )
    await session.flush()


async def _ensure_difficulty_paths(session) -> None:
    for index, (slug, title, difficulty, query_value, description) in enumerate(DIFFICULTY_PATHS):
        await _ensure_path(
            session,
            slug,
            title=title,
            short_description=description,
            description=description,
            path_type=PracticePathType.DIFFICULTY,
            difficulty=difficulty,
            estimated_minutes=None,
            availability=PathAvailability.AVAILABLE,
            is_active=True,
            is_featured=False,
            sort_order=index,
            icon_key=query_value,
            external_route=f"/practice/dsa?difficulty={query_value}",
        )
    await session.flush()


async def _ensure_company_paths(session, companies: dict[str, Company]) -> None:
    for index, name in enumerate(LEARN_COMPANIES):
        company = companies.get(name)
        await _ensure_path(
            session,
            f"company-{slugify(name)}",
            title=name,
            short_description=f"Aptitude, coding, and interview practice modelled on a typical {name} hiring process.",
            description=COMPANY_DISCLAIMER.format(company=name),
            path_type=PracticePathType.COMPANY,
            difficulty=PracticePathDifficulty.MIXED,
            estimated_minutes=None,
            availability=PathAvailability.AVAILABLE,
            is_active=True,
            is_featured=False,
            sort_order=index,
            icon_key=slugify(name),
            company_id=company.id if company else None,
            external_route=f"/company-prep?company={slugify(name)}",
        )
    await session.flush()


async def _ensure_misc_paths(session) -> None:
    await _ensure_path(
        session,
        "interview-preparation",
        title="Interview Preparation",
        short_description="Technical, HR, and behavioural questions with model answers and key points.",
        description=(
            "Work through curated interview questions by role and skill, review the expected answer structure, "
            "and rehearse until your explanation is tight."
        ),
        path_type=PracticePathType.INTERVIEW,
        difficulty=PracticePathDifficulty.MIXED,
        estimated_minutes=None,
        availability=PathAvailability.AVAILABLE,
        is_active=True,
        is_featured=True,
        sort_order=0,
        icon_key="interview",
        external_route="/interviews",
    )
    await _ensure_path(
        session,
        "sql-practice",
        title="SQL Practice",
        short_description="Write real queries against seeded schemas and get instant result comparison.",
        description=(
            "Joins, aggregation, subqueries, and window functions practised against live tables rather than "
            "multiple-choice questions."
        ),
        path_type=PracticePathType.CUSTOM,
        difficulty=PracticePathDifficulty.MIXED,
        estimated_minutes=None,
        availability=PathAvailability.AVAILABLE,
        is_active=True,
        is_featured=True,
        sort_order=1,
        icon_key="sql",
        external_route="/practice/sql",
    )
    await _ensure_path(
        session,
        "projects-hub",
        title="Build Projects",
        short_description="Ship something you can put on a resume, one guided task at a time.",
        description=(
            "Project tracks across Python, web, data, and cloud. Each project breaks down into modules and tasks "
            "so you always know the next concrete step."
        ),
        path_type=PracticePathType.PROJECT,
        difficulty=PracticePathDifficulty.MIXED,
        estimated_minutes=None,
        availability=PathAvailability.AVAILABLE,
        is_active=True,
        is_featured=True,
        sort_order=0,
        icon_key="projects",
        external_route="/practice/projects",
    )
    await session.flush()


async def seed_learn_content() -> None:
    """Seed Build 5 Practice Hub content. Safe to run repeatedly."""
    async with AsyncSessionLocal() as session:
        companies = await _ensure_companies(session)
        course = await _ensure_python_course(session)
        await _ensure_projects(session)
        from app.seed.build51_seed import seed_build51_content

        await seed_build51_content(session)
        await _ensure_language_paths(session, course)
        await _ensure_dsa_paths(session)
        await _ensure_structure_and_algorithm_paths(session)
        await _ensure_difficulty_paths(session)
        await _ensure_company_paths(session, companies)
        await _ensure_misc_paths(session)
        await session.commit()
        print("Build 5 learn content seeded.")
