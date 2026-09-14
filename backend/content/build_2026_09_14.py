"""Write the 2026-09-14 weekly learning batch. Does not touch a database.

Asia/Kolkata date 2026-09-14. Rotation group 2: java-backend,
frontend-react, fullstack-web, plus a shared CRT pack.

Run from backend: python -m content.build_2026_09_14
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "batches" / "2026-09-14-weekly-001"
BATCH_ID = "2026-09-14-weekly-001"
AUDIENCE = "Fresher and Entry (1-2 yrs)"

MATERIALS = [
    {
        "key": "jb-class-and-main",
        "title": "A Java class and the method that starts it",
        "kind": "article",
        "level": "beginner",
        "audience": "Fresher",
        "minutes": 25,
        "families": ["java-backend"],
        "skills": ["java", "classes"],
        "objectives": [
            "Name a class and one object of that class",
            "Recognize the standard application entry method",
            "State that this site does not compile or run Java",
        ],
        "prerequisites": ["You can read a short code block and say what a file is named"],
        "summary": "A class is the blueprint. An object is one ticket built from it. A standard application starts at public static void main(String[] args). This site will not compile the file.",
        "sources": [
            {"label": "Oracle tutorial: A Closer Look at the Hello World Application", "url": "https://docs.oracle.com/javase/tutorial/getStarted/application/index.html"},
            {"label": "Oracle tutorial: Creating a Package", "url": "https://docs.oracle.com/javase/tutorial/java/package/createpkgs.html"},
            {"label": "Java SE 21 PrintStream.println", "url": "https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/io/PrintStream.html#println(java.lang.String)"},
        ],
        "examples": ["public class Ticket { } lives in Ticket.java"],
        "exercises": ["Write the class line and the main method signature only. Do not add a framework."],
        "body": """## Objective
Name a class, one object, and the method a standard Java application starts in.

## Prerequisite
You can read a short code block and match a public class name to a file name.

## What a class is
A class describes the fields and methods a ticket can have. It is not a ticket yet. `new Ticket(4, "VPN")` builds one object: ticket 4, title VPN. A second `new` builds a different object even if the title text is the same.

## The entry method
A standard application starts in:

```
public static void main(String[] args)
```

The closer-look tutorial says every application must contain a `main` method with that signature. It is the entry point. `void` means the method does not return a value. `String[] args` is the argument list; the tutorial says the argument may be named something other than `args`. That page does not define the words `public` and `static` beyond requiring them in the signature. A method named `start` or `run` is not this entry point unless something else calls it.

## Worked example
If a source file declares a public type, the packages tutorial says only one type in that file may be public, and it must have the same name as the source file. `public class TicketSummary` belongs in `TicketSummary.java`. A `.class` file is compiler output. The Windows "Hello World!" instructions save `HelloWorldApp.java`, run `javac`, and show a generated `HelloWorldApp.class`.

`System.out.println(title)` writes that text and then ends the line. The Java SE 21 `PrintStream.println(String)` documentation says it prints a string and then terminates the line. It does not save a ticket.

## Common mistakes
- Calling the file `Main.java` while the public class is `Ticket`.
- Writing `public void main()` and expecting the application to start.
- Treating the class as the ticket. The class is the blueprint; the object is the ticket.

## Exercise
On paper, write the class line for `TicketSummary` and the `main` signature. Do not install a framework for this step.

## What this site will not do
This application does not compile or run Java. There is no Judge0 runner for this assignment. A local JDK, if you choose to use one, is on your computer. The site only stores the text or an HTTPS URL for a person to review.

## Summary
Class, then object. Public class name matches the file name. The start method is `public static void main(String[] args)`.

## References
Oracle tutorial, "A Closer Look at the Hello World Application": https://docs.oracle.com/javase/tutorial/getStarted/application/index.html
Oracle tutorial, "Creating a Package": https://docs.oracle.com/javase/tutorial/java/package/createpkgs.html
Java SE 21 `PrintStream.println(String)`: https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/io/PrintStream.html#println(java.lang.String)
""",
    },
    {
        "key": "jb-methods-and-blank-title",
        "title": "Methods that return a title or refuse a blank one",
        "kind": "worked_example",
        "level": "intermediate",
        "audience": "Entry (1-2 yrs)",
        "minutes": 30,
        "families": ["java-backend"],
        "skills": ["java", "methods"],
        "objectives": [
            "Write a method that returns a cleaned title",
            "Refuse a blank title instead of inventing one",
            "Catch only the failure you named",
        ],
        "prerequisites": ["jb-class-and-main"],
        "summary": "Trim the title, then reject it when nothing remains. Compare text with equals, not ==. Catch IllegalArgumentException, not every Exception.",
        "sources": [
            {"label": "Oracle tutorial: Defining Methods", "url": "https://docs.oracle.com/javase/tutorial/java/javaOO/methods.html"},
            {"label": "Oracle tutorial: Comparing Strings", "url": "https://docs.oracle.com/javase/tutorial/java/data/comparestrings.html"},
            {"label": "Oracle tutorial: Primitive Data Types", "url": "https://docs.oracle.com/javase/tutorial/java/nutsandbolts/datatypes.html"},
            {"label": "Oracle tutorial: The catch Blocks", "url": "https://docs.oracle.com/javase/tutorial/essential/exceptions/catch.html"},
        ],
        "examples": ["if (title == null || title.trim().isEmpty()) throw new IllegalArgumentException(\"title is blank\");"],
        "exercises": ["Show one accepted call and one rejected call. Do not invent Untitled."],
        "body": """## Objective
Return a usable title, or stop when the title is blank. Do not invent a replacement.

## Prerequisite
You can write a class and the `main` signature from `jb-class-and-main`.

## A method returns one result
A method has a name, parameters, and a return type. `String cleaned(String title)` promises a `String` or a thrown exception. It does not silently replace a blank title with `Untitled` unless a brief explicitly says to.

## Worked example
Input `" VPN "` becomes `"VPN"` after trim. Input `"   "` becomes empty after trim, so the method throws `IllegalArgumentException` with the reason `title is blank`. Input `null` fails the same check before `trim` is called, so it does not throw `NullPointerException` from `trim`.

## Comparing text
`title.equals("VPN")` asks whether the characters match. The comparing-strings tutorial says `equals` returns true when the argument is a `String` with the same sequence of characters. `title == "VPN"` is a different operator. This lesson does not treat `==` as a character comparison.

## Common mistakes
- Calling `trim` on null.
- Catching `Exception` and then treating the ticket as saved. The catch-blocks tutorial says a multi-type catch exists partly to lessen the temptation to catch an overly broad exception. `Exception` is broader than `IllegalArgumentException`.
- Reading a local `int count;` before assigning it. The data-types tutorial says the compiler never assigns a default to an uninitialized local variable, and reading it is a compile-time error. That default rule is for fields, not for this local variable.

## Exercise
On your computer, call the check with `" VPN "` and with `"   "`. Record the returned title and the exception message. This site will not run the file.

## Summary
Trim, then reject an empty result. Use `equals` for characters. Catch the exception you named.

## References
Oracle tutorial, "Defining Methods": https://docs.oracle.com/javase/tutorial/java/javaOO/methods.html
Oracle tutorial, "Comparing Strings and Portions of Strings": https://docs.oracle.com/javase/tutorial/java/data/comparestrings.html
Oracle tutorial, "Primitive Data Types": https://docs.oracle.com/javase/tutorial/java/nutsandbolts/datatypes.html
Oracle tutorial, "The catch Blocks": https://docs.oracle.com/javase/tutorial/essential/exceptions/catch.html
""",
    },
    {
        "key": "fr-component-props",
        "title": "A React component and the props a parent passes",
        "kind": "article",
        "level": "beginner",
        "audience": "Fresher",
        "minutes": 25,
        "families": ["frontend-react"],
        "skills": ["react", "props"],
        "objectives": [
            "Describe a component as a function that returns UI",
            "Read a title from props",
            "State that this site will not render the component",
        ],
        "prerequisites": ["You can read a function call and a returned value"],
        "summary": "A component function returns a description of UI. Props are inputs from the parent. The child reads them. This application does not render the JSX.",
        "sources": [
            {"label": "React docs: Your First Component", "url": "https://react.dev/learn/your-first-component"},
            {"label": "React docs: Passing Props to a Component", "url": "https://react.dev/learn/passing-props-to-a-component"},
            {"label": "React docs: Writing Markup with JSX", "url": "https://react.dev/learn/writing-markup-with-jsx"},
        ],
        "examples": ["function TicketCard({ title }) { return <h1>{title}</h1>; }"],
        "exercises": ["Name the prop and the parent value that fills it. Do not add a data fetch."],
        "body": """## Objective
Show a ticket title that the parent passed in. Do not fetch it inside this component.

## Prerequisite
You can read a JavaScript function and a value in curly braces.

## A component returns UI
In this material, a component is a function. It returns a description of what should appear, not a screenshot and not a saved ticket. `function TicketCard({ title }) { return <h1>{title}</h1>; }` shows the `title` prop.

The parent supplies the value: `<TicketCard title="VPN" />`. The child does not invent a title when the prop is missing. A missing title should be visible as missing, not replaced with a guessed label.

## JSX names
The HTML `class` attribute is written `className` in JSX. React's JSX page says this is because `class` is a reserved word, and the attribute is named after the DOM `className` property. It is not a second kind of CSS.

## Worked example
Parent data: ticket 4, title VPN. Parent renders `<TicketCard title="VPN" />`. The card shows VPN. If the parent passes `title=""`, the card shows an empty heading. It does not mean the ticket was created.

## Common mistakes
- Putting the title only in a comment and expecting the screen to show it.
- Editing props inside the child. The parent owns the value it passed.
- Claiming this website rendered the component. It does not run React for student submissions.

## Exercise
On paper, write a component that receives `title` and returns one heading. Then write the parent line that passes `"Printer"`.

## What this site will not do
This application does not render JSX, start a React dev server, or require a paid plugin. Review is of the text or an HTTPS URL you submit.

## Summary
The component returns UI. Props come from the parent. `className` is the JSX name for the CSS class.

## References
React docs, "Your First Component": https://react.dev/learn/your-first-component
React docs, "Passing Props to a Component": https://react.dev/learn/passing-props-to-a-component
React docs, "Writing Markup with JSX": https://react.dev/learn/writing-markup-with-jsx
""",
    },
    {
        "key": "fr-state-input",
        "title": "State and a controlled title input",
        "kind": "worked_example",
        "level": "intermediate",
        "audience": "Entry (1-2 yrs)",
        "minutes": 30,
        "families": ["frontend-react"],
        "skills": ["react", "state"],
        "objectives": [
            "Start a title with useState",
            "Wire an input so React holds the current title",
            "Avoid reading the new title on the next line of the same handler",
        ],
        "prerequisites": ["fr-component-props"],
        "summary": "useState keeps the title between renders. A controlled input uses value and onChange. setTitle schedules the next render; the next line still sees the old title.",
        "sources": [
            {"label": "React docs: State: A Component's Memory", "url": "https://react.dev/learn/state-a-components-memory"},
            {"label": "React docs: useState", "url": "https://react.dev/reference/react/useState"},
            {"label": "React docs: Rendering Lists", "url": "https://react.dev/learn/rendering-lists"},
        ],
        "examples": ["const [title, setTitle] = useState(''); <input value={title} onChange={(event) => setTitle(event.target.value)} />"],
        "exercises": ["Write the setter call for a blank title, then say what title still holds on the next line."],
        "body": """## Objective
Let the user type a title, and keep that title in component state.

## Prerequisite
You can pass a `title` prop from `fr-component-props`.

## State is this component's memory
`const [title, setTitle] = useState("")` starts the title as an empty string on the first render. `title` is the current value. `setTitle` asks React to render again with a new value. Assigning `title = "VPN"` does not do that. React was not told to remember the change.

## Controlled input
A controlled input displays the state and writes back through the setter:

```
<input value={title} onChange={(event) => setTitle(event.target.value)} />
```

`value` is what the field shows. `onChange` receives the browser event. `event.target.value` is the text the user typed. Both pieces are required. An input with only `onChange` is not controlled by this state.

## Worked example
The user types `V`. React calls `setTitle("V")`. The next render shows `V` in the field. The next character works the same way. A submit handler that checks `title.trim()` uses the state React already stored, not a guessed value from the DOM.

## The next line still sees the old value
After `setTitle("VPN")`, a read of `title` on the next line of the same event handler still sees the previous title. The setter asked React to render again. It did not change the `title` variable in the function that is already running. The `useState` reference says calling the set function does not change the current state in the already executing code. The state-memory page shows the related stuck-input case: assigning `title = event.target.value` without the setter does not make React remember the new text.

## Lists
When you render several tickets, give each item a `key` that identifies that ticket, such as `ticket.id`. Pushing into an array with `tickets.push(row)` does not call the setter, so React is not asked to render the new list.

## Common mistakes
- Reading `title` immediately after `setTitle` and treating that as the new value.
- Mutating an array and expecting a new render without the setter.
- Using the array index as a key after the list can be reordered or filtered.

## Exercise
Write the `useState` line and the input. In one sentence, say what `title` holds on the line after `setTitle("VPN")` if it was empty before the click.

## What this site will not do
This application will not mount the component or type into the input for you. A local preview, if you run one, stays on your computer.

## Summary
State starts at the `useState` argument. A controlled input uses `value` and `onChange`. The setter updates the next render, not the current line.

## References
React docs, "State: A Component's Memory": https://react.dev/learn/state-a-components-memory
React docs, "useState": https://react.dev/reference/react/useState
React docs, "Rendering Lists": https://react.dev/learn/rendering-lists
""",
    },
    {
        "key": "fs-request-response",
        "title": "Read one HTTP request and its status",
        "kind": "article",
        "level": "beginner",
        "audience": "Fresher",
        "minutes": 25,
        "families": ["fullstack-web"],
        "skills": ["http", "status-codes"],
        "objectives": [
            "Name method, path, and status on one exchange",
            "Separate 201, 400, and 404 in the supplied log",
            "Refuse a conclusion the status does not support",
        ],
        "prerequisites": ["You can read a small table of rows"],
        "summary": "A request has a method and a path. The response has a status. In this log, 201 means created, 400 means the request was rejected, and 404 means that ticket was not found.",
        "sources": [
            {"label": "RFC 9110, HTTP Semantics: Status Codes", "url": "https://www.rfc-editor.org/rfc/rfc9110.html#name-status-codes"}
        ],
        "examples": ["POST /tickets 201 means the create request was accepted and a ticket was created."],
        "exercises": ["From the project log, count 200 responses without treating 201 as 200."],
        "body": """## Objective
Read one line of a request log without inventing a second request.

## Prerequisite
You can read a table and count rows that share a value.

## Method, path, status
A request line in this batch has a method and a path. The matching response has a status code. Status classes in RFC 9110: 1xx informational, 2xx success, 3xx redirection, 4xx client error, 5xx server error. This material uses only the codes in the supplied log.

This is the log. Do not add a row.

| # | Method | Path | Body sent | Status | Body returned |
| --- | --- | --- | --- | --- | --- |
| 1 | GET | /tickets/1 | none | 200 | {"id": 1, "title": "Printer"} |
| 2 | POST | /tickets | {"title": "VPN"} | 201 | {"id": 4, "title": "VPN"} |
| 3 | GET | /tickets/9 | none | 404 | {"error": "not found"} |
| 4 | POST | /tickets | {} | 400 | {"error": "title is required"} |
| 5 | GET | /tickets/2 | none | 200 | {"id": 2, "title": "Laptop"} |
| 6 | GET | /tickets/3 | none | 500 | {"error": "server failed"} |

In this log, and not as a claim about every API on the internet:

- GET reads a ticket
- POST creates a ticket
- 200 means the read succeeded
- 201 means the create succeeded
- 400 means the server rejected the request as sent, here because the title was missing
- 404 means no ticket with that id
- 500 means the server failed while handling the request

## Worked example
`POST /tickets` with JSON `{ "title": "VPN" }` returns 201 and `{ "id": 4, "title": "VPN" }`. A different `POST /tickets` with `{}` returns 400. Those are two requests. Do not average them into one outcome.

`GET /tickets/9` returns 404. That does not mean ticket 1 is missing. `GET /tickets/1` returns 200.

## Common mistakes
- Calling 201 a failure because it is not 200.
- Calling 404 a server crash. 404 is 4xx. 500 is 5xx.
- Treating a title in the query string as if it were a JSON body field. `GET /tickets?title=VPN` does not put `title` inside a JSON body.

## Exercise
Using only the six-row log in the project `ticket-request-log`, count each status. 200 and 201 are different cells.

## What this site will not do
This application does not host the ticket API and will not send these requests for you. The log is synthetic data supplied with the batch.

## Summary
Read method, path, and status together. Keep 200, 201, 400, 404, and 500 distinct. Do not invent a request that is not in the log.

## References
RFC 9110, HTTP Semantics, status codes: https://www.rfc-editor.org/rfc/rfc9110.html#name-status-codes
""",
    },
    {
        "key": "fs-two-programs",
        "title": "The page and the API are two programs",
        "kind": "article",
        "level": "intermediate",
        "audience": "Entry (1-2 yrs)",
        "minutes": 25,
        "families": ["fullstack-web"],
        "skills": ["http", "boundaries"],
        "objectives": [
            "Separate what the page shows from what the API received",
            "Explain one 400 and one 500 without swapping them",
            "Say what this application will not execute",
        ],
        "prerequisites": ["fs-request-response"],
        "summary": "The page can show a title the API never received. A 400 is a rejected request. A 500 is a server failure. This app does not run either program.",
        "sources": [
            {"label": "RFC 9110, HTTP Semantics: Status Codes", "url": "https://www.rfc-editor.org/rfc/rfc9110.html#name-status-codes"}
        ],
        "examples": ["A heading that says Printer is not proof that POST /tickets received title Printer."],
        "exercises": ["Name one field the page shows and one field the API received on the successful create."],
        "body": """## Objective
Keep the browser page and the ticket API as two programs that exchange messages.

## Prerequisite
You can read method, path, and status from `fs-request-response`.

## Two programs
The page is what a person looks at. The API is what answers `/tickets`. They can fail separately. A heading that shows `Printer` is the page. It is not, by itself, the JSON the API stored. The successful create in the log is the evidence for what the API received: JSON `{ "title": "VPN" }` and response `{ "id": 4, "title": "VPN" }`.

## Worked example
Request 4 in the log from `fs-request-response` is `POST /tickets` with `{}` and status 400. The page may still show an empty input. The API rejected the request because the title was missing. Request 6 is `GET /tickets/3` with status 500. RFC 9110 puts 500 in the server-error class. That class does not say the browser calculated a title incorrectly. The conclusion that a 500 does not prove a page calculation error is an application of that class, not a sentence copied from the RFC.

## Common mistakes
- Using a 500 as evidence that the page's arithmetic was wrong.
- Treating the page field and the JSON field as the same store.
- Claiming this JobReady application executed the page or the API. It stores the log and a written review. It does not run Java, React, or the ticket service.

## Exercise
Write two sentences. One names a field the page shows. One names a field the API received on the 201 response. Do not add a field that is not in the log.

## Summary
The page shows. The API receives and answers. Status 400 and status 500 are different failures. This site does not execute either side.

## References
RFC 9110, HTTP Semantics, status codes: https://www.rfc-editor.org/rfc/rfc9110.html#name-status-codes
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
        "version": 1,
    }


DI = """| Channel | Opened | Closed | Reopened |
| --- | --- | --- | --- |
| Email | 40 | 30 | 4 |
| Chat | 25 | 20 | 1 |
| Phone | 15 | 10 | 2 |
| Form | 20 | 18 | 0 |"""

LOG = """| # | Method | Path | Body sent | Status | Body returned |
| --- | --- | --- | --- | --- | --- |
| 1 | GET | /tickets/1 | none | 200 | {"id": 1, "title": "Printer"} |
| 2 | POST | /tickets | {"title": "VPN"} | 201 | {"id": 4, "title": "VPN"} |
| 3 | GET | /tickets/9 | none | 404 | {"error": "not found"} |
| 4 | POST | /tickets | {} | 400 | {"error": "title is required"} |
| 5 | GET | /tickets/2 | none | 200 | {"id": 2, "title": "Laptop"} |
| 6 | GET | /tickets/3 | none | 500 | {"error": "server failed"} |"""


def questions():
    items = []
    items.append(_q("jb-q01", "Which method is the standard starting point of a Java application?", "classes", "easy", ["public static void main(String[] args)", "public void start()", "static run()", "public Ticket main()"], 0, ["That is the entry method the Oracle tutorial shows.", "start is not the standard entry method.", "run is not the application entry signature.", "main must return void and take String[]."], "A standard Java application starts at public static void main(String[] args)."))
    items.append(_q("jb-q02", "Which statement matches the class and object distinction in this batch?", "classes", "easy", ["The class is the blueprint; new Ticket(4, \"VPN\") is one object", "The class is already ticket 4", "An object is the file name", "A class cannot have two objects"], 0, ["The class describes tickets. new builds one ticket.", "The class is not the ticket.", "The file name is not the object.", "You can construct more than one object."], "Class is the blueprint. The object is one ticket built from it."))
    items.append(_q("jb-q03", "What does System.out.println(\"VPN\") do?", "classes", "easy", ["Writes VPN and then a line break to standard output", "Saves a ticket named VPN", "Compiles Ticket.java", "Starts the Java runtime"], 0, ["println writes the text and a newline.", "It does not persist a ticket.", "It is not the compiler.", "The runtime is already running if this line runs."], "println writes to standard output. It does not save a ticket."))
    items.append(_q("jb-q04", "The brief says a blank title must be refused. Which result matches it?", "methods", "easy", ["Throw IllegalArgumentException and do not invent a title", "Store the title Untitled", "Store an empty string and continue", "Return null and treat it as a saved title"], 0, ["Refusal is the named failure, not a guessed title.", "Untitled was not in the brief.", "An empty string is the failure, not a saved title.", "null is not a saved title."], "Refuse the blank title. Do not invent Untitled."))
    items.append(_q("jb-q05", "How does this JobReady site grade a Java file pasted into the browser?", "methods", "easy", ["It does not compile or run it. Text or an HTTPS URL is for manual review.", "Judge0 compiles it and returns a score", "The SQL sandbox compiles it", "A paid plugin must be installed first"], 0, ["Java execution is not hosted here.", "Judge0 stays disabled and is not a required key.", "The SQL sandbox does not compile Java.", "No paid plugin is required to complete the batch."], "Submit text or an HTTPS URL. This site does not run the Java file."))
    items.append(_q("jb-q06", "A method trims the title, then rejects it when nothing remains. What happens to the input \"   \"?", "methods", "medium", ["It is rejected as blank", "It is stored as three spaces", "It becomes Untitled", "trim throws NullPointerException"], 0, ["After trim the text is empty, so the check rejects it.", "The brief rejects a blank result after trim.", "Untitled is not part of the check.", "The input is not null, so trim itself is not a null failure."], "Trim first. An all-space title is empty and must be rejected."))
    items.append(_q("jb-q07", "Which check asks whether two strings have the same characters?", "methods", "medium", ["title == other", "title.equals(other)", "title = other", "System.out.println(title)"], 1, ["== asks whether they are the same object.", "equals asks about the characters.", "A single = assigns. It does not compare.", "Printing does not compare."], "Use equals for character content. == is an object identity check."))
    items.append(_q("jb-q08", "A method declares int count; and then reads count before any assignment. What happens?", "methods", "medium", ["The compiler rejects the read of an unassigned local variable", "count is silently 0", "count is null", "The program prints count and continues"], 0, ["Local variables have no compiler-supplied default.", "That default applies to fields, not to this unread local.", "int is not null.", "The compiler does not let this read through."], "The compiler never assigns a default to an uninitialized local variable."))
    items.append(_q("jb-q09", "A folder has Main.java whose text is public class TicketSummary, TicketSummary.class, and Helper.java whose text is class Helper only. Which source-file name matches the public type, and which existing file is not that source?", "classes", "hard", ["TicketSummary.java, and TicketSummary.class is compiler output rather than the source file", "Main.java, because the public class text is already stored there", "Helper.java, because any .java file can hold the public class", "TicketSummary.class, because the class name matches the compiled file"], 0, ["The packages tutorial says a public type must have the same name as the source file. A .class file is what javac writes.", "The file name does not match TicketSummary.", "Helper is not the public type.", "The compiled file is not the source file you save."], "public class TicketSummary belongs in TicketSummary.java. TicketSummary.class is compiler output."))
    items.append(_q("jb-q10", "The constructor throws IllegalArgumentException when the title is blank. A handler does: try { summary = new TicketSummary(4, \"   \"); saved = true; } catch (Exception ex) { saved = true; } Why is this a weak match for a brief that says refuse a blank title?", "methods", "hard", ["The blank-title failure is caught and then marked saved, and Exception also catches unrelated failures", "Exception cannot catch IllegalArgumentException", "A blank title never throws in this constructor", "catch is illegal in Java"], 0, ["The catch runs for the blank title and sets saved to true. Exception is broader than the named failure. The catch-blocks tutorial warns against an overly broad exception.", "IllegalArgumentException is an Exception, so this catch does run, and that is the problem.", "The constructor in this lesson does throw for an all-space title.", "catch is legal. The problem is what the handler does and how wide it is."], "A refusal that sets saved to true did not refuse the title. Exception is also wider than IllegalArgumentException."))

    items.append(_q("fr-q01", "In this batch, what does a React component function do?", "components", "easy", ["Returns a description of UI", "Saves a ticket on a server", "Compiles Java", "Replaces the need for a parent"], 0, ["The component returns UI.", "Saving is not this function's job.", "React is not a Java compiler.", "The parent still supplies props."], "A component returns a description of UI. It does not save a ticket."))
    items.append(_q("fr-q02", "Where does a prop value come from?", "props", "easy", ["The child invents it at render time", "The parent passes it in, and the child reads it", "The CSS file", "The SQL sandbox"], 1, ["A missing prop should stay missing, not be invented.", "Props are inputs from the parent.", "CSS does not pass the title.", "The SQL sandbox is not the component parent."], "The parent passes the prop. The child reads it."))
    items.append(_q("fr-q03", "const [title, setTitle] = useState(\"\"). What is title on the first render?", "state", "easy", ["null", "\"Untitled\"", "\"\"", "The previous user's title"], 2, ["The argument was an empty string, not null.", "Untitled was not passed to useState.", "useState(\"\") starts title as an empty string.", "This state is local to the component. It is not another user's value."], "The first render uses the initial value passed to useState."))
    items.append(_q("fr-q04", "How is an HTML class attribute written in JSX?", "components", "easy", ["class", "className", "css", "styleClass"], 1, ["class is the HTML name, not the JSX name.", "className is the JSX name.", "css is not the attribute.", "styleClass is not the JSX attribute."], "JSX uses className, not class."))
    items.append(_q("fr-q05", "How does this JobReady site render a JSX file you submit?", "components", "easy", ["It does not render it. Review is of the text or an HTTPS URL.", "It mounts the component and types into the input", "It requires a paid React plugin", "The SQL sandbox renders it"], 0, ["React execution is not hosted here.", "No browser preview is run on the server for this assignment.", "No paid plugin is required.", "SQL does not render JSX."], "Submit the component as text or an HTTPS URL. This site will not render it."))
    items.append(_q("fr-q06", "Which input is controlled by title state?", "state", "medium", ["<input onChange={(event) => setTitle(event.target.value)} />", "<input value={title} onChange={(event) => setTitle(event.target.value)} />", "<input value={title} />", "<input defaultValue=\"VPN\" />"], 1, ["onChange alone does not display the state as the current value.", "value and onChange together keep the field tied to state.", "value without onChange does not write the next keystroke back through the setter in this pattern.", "defaultValue does not keep the field controlled by title."], "A controlled input uses value={title} and an onChange that calls setTitle."))
    items.append(_q("fr-q07", "A list of tickets can be filtered. Which key identifies a row?", "lists", "medium", ["The array index", "ticket.id", "The word key as the title", "The CSS class"], 1, ["The index changes when the list is filtered or reordered.", "ticket.id stays with that ticket.", "The word key is not an identity.", "A CSS class does not identify the row."], "Use a stable id. Do not use the array index when the list can change order."))
    items.append(_q("fr-q08", "A handler does tickets.push(row) and does not call the state setter. What does React do?", "state", "medium", ["It is not asked to render the new list from state", "It saves the ticket on the server", "It resets title to null", "It treats push as setState"], 0, ["The setter was not called, so React was not told to render the new list.", "push does not perform an HTTP create.", "This line does not touch title.", "push is an array method, not the setter."], "Mutating the array does not schedule the render. Call the setter with the next list."))
    items.append(_q("fr-q09", "title starts as \"Ada\". The handler runs setTitle(\"VPN\") and then returns title. What does the return see, and what does the next render show?", "state", "hard", ["The return sees Ada; the next render shows VPN", "The return sees VPN; the next render shows VPN", "The return sees Ada; the next render shows Ada", "The return sees VPN; the next render shows Ada"], 0, ["The set function does not change title in the already executing code, and it does request a later render with VPN.", "The return cannot already see VPN. The useState reference says the set function does not change current state in the running code.", "The next render is the scheduled update. It does not stay Ada.", "The two moments are not swapped. The running code is stale; the next render is not."], "The return still sees Ada. The next render shows VPN. That split is the useState rule, not a guess."))
    items.append(_q("fr-q10", "An input uses value={title}. The change handler does title = event.target.value and does not call setTitle. title started as \"\". After the user types VPN, what does the field keep showing?", "state", "medium", ["The empty string, because the assignment does not ask React to remember a new value", "VPN, because the assignment is the state update", "null", "The parent's prop, even when no prop was passed"], 0, ["The state-memory page shows this stuck input: value stays tied to the old variable, and assigning it does not make React remember the text.", "A plain assignment is not setTitle.", "The initial value was an empty string, not null.", "This input reads title state, not a missing prop."], "Without the setter, React does not store the typed text. The field stays on the empty initial value."))

    items.append(_q("fs-q01", "In this batch's log, what is GET /tickets/1 used for?", "http", "easy", ["To read ticket 1", "To create ticket 1", "To delete ticket 1", "To compile a Java class"], 0, ["GET on that path is the read in this log.", "Create is the POST that returned 201.", "No delete appears in the log.", "The log is HTTP, not a Java compile."], "In this log, GET reads an existing ticket. It is not a create."))
    items.append(_q("fs-q02", "Using only this log, what does status 201 on row 2 mean?", "http", "easy", ["The ticket was not found", "The create succeeded", "The server crashed", "The title was missing"], 1, ["Not found is 404 on row 3.", "Row 2 returned 201 and a ticket id.", "A server failure is 500 on row 6.", "A missing title is 400 on row 4."], "201 on the POST means the ticket was created. It is not a failure just because it is not 200.", LOG))
    items.append(_q("fs-q03", "Using only this log, what does status 404 on row 3 mean?", "http", "easy", ["Ticket 9 was not found", "Ticket 1 was not found", "The server crashed", "The page failed to start"], 0, ["The path is /tickets/9 and the body says not found.", "Ticket 1 returned 200 on row 1.", "Crash is 500, which is a different row.", "404 is about that resource, not the page program starting."], "404 means no ticket with id 9. It does not erase the 200 on ticket 1.", LOG))
    items.append(_q("fs-q04", "Which description matches the page and the API in this project?", "boundaries", "easy", ["They are the same program and the same store", "They are two programs. The page does not contain the API's stored tickets.", "The page is the SQL sandbox", "The API is a React prop"], 1, ["A heading is not the JSON the API stored.", "They exchange messages. They are not one store.", "The SQL sandbox is a different tool and is not this API.", "A prop is a React input, not the ticket API."], "The page shows. The API answers. They are separate programs."))
    items.append(_q("fs-q05", "Using only this log, how many responses are status 200?", "http", "easy", ["1", "2", "3", "6"], 1, ["Row 1 is one 200, but row 5 is also 200.", "Rows 1 and 5 are 200. Row 2 is 201, not 200.", "That would count 201 as 200.", "Only two rows are 200."], "Count the Status column. 200 appears on rows 1 and 5. 201 is not 200.", LOG))
    items.append(_q("fs-q06", "Using only this log, why did row 4 return 400?", "http", "medium", ["The server crashed", "The client sent no title, so the request was rejected", "Ticket 4 was not found", "The browser calculated a title incorrectly"], 1, ["A crash in this log is status 500.", "The body sent is {} and the error says title is required.", "Not found is 404, and this row is a POST.", "The response names the missing field, not a browser calculation."], "400 here means the request was rejected because title was missing.", LOG))
    items.append(_q("fs-q07", "Using only this log, what does status 500 on row 6 mean?", "http", "medium", ["The browser could not parse JSX", "The server failed while handling GET /tickets/3", "The title was missing on a POST", "Ticket 3 was created"], 1, ["JSX is not in this row.", "The returned body says server failed, and the class is 5xx.", "A missing title is row 4, status 400.", "Created is row 2, status 201."], "500 means the server failed on that request. It is not a missing title.", LOG))
    items.append(_q("fs-q08", "A title appears only as GET /tickets?title=VPN. What is true of the JSON body?", "http", "medium", ["The JSON body automatically contains title VPN", "A query parameter is not automatically a JSON body field", "The status must be 201", "The page and the API are the same program"], 1, ["The question places the title in the query, not in a JSON body.", "The query string and the JSON body are different places.", "201 is a create status. This line is a GET.", "The page and the API remain separate."], "A title in the query string is not a JSON body field unless the request also sends that body."))
    items.append(_q("fs-q09", "Using only this log, what does status 500 on row 6 prove about the page?", "http", "hard", ["The page computed the title incorrectly", "It does not prove a page calculation error. It reports a server failure.", "The page never rendered a heading", "Ticket 9 was created"], 1, ["The status is about the server handling GET /tickets/3.", "A 500 is a server failure. It is not evidence that the page arithmetic was wrong.", "The log does not say the page failed to render.", "Ticket 9 is the 404 row, and it was not created."], "A 500 proves the server reported a failure. It does not prove the page calculated the title incorrectly.", LOG))
    items.append(_q("fs-q10", "Using the six-row log and RFC 9110 classes, row 2 is 201, row 3 is 404, and row 6 is 500. Which statement is true?", "http", "hard", ["201 is success-class, 404 is client-error-class, and 500 is server-error-class. A 404 is not a server failure.", "201, 404, and 500 are all failures because none of them is 200", "404 and 500 are the same class", "201 is a client error because the client sent the POST"], 0, ["RFC 9110 puts 2xx in successful, 4xx in client error, and 5xx in server error. 201 is 2xx, 404 is 4xx, and 500 is 5xx.", "201 is in the success class. It is not a failure only because it is not 200.", "404 is 4xx and 500 is 5xx.", "Sending a POST does not move 201 into the client-error class."], "Classify each code by its class. 201 is success, 404 is client error, and 500 is server error. Do not treat every non-200 code as the same failure.", LOG))

    items.append(_q("crt2-q01", "The numbers 10, 20, and 30 are one set. What is their average?", "quantitative", "easy", ["15", "20", "30", "60"], 1, ["That drops the 30.", "10 + 20 + 30 = 60, and 60 / 3 = 20.", "30 is the largest value, not the average.", "60 is the sum, not the average."], "Add the three numbers and divide by 3. The average is 20."))
    items.append(_q("crt2-q02", "What is 15% of 200?", "quantitative", "easy", ["15", "30", "150", "215"], 1, ["15 is the percent, not the part of 200.", "0.15 * 200 = 30.", "150 would be 75% of 200.", "215 adds the percent to the base."], "15% of 200 is 30. No further increase is stated."))
    items.append(_q("crt2-q03", "Pipe A fills a tank in 12 hours. Pipe B fills the same tank in 6 hours. How long do they take together, if both fill and neither leaks?", "quantitative", "hard", ["4 hours", "9 hours", "18 hours", "2 hours"], 0, ["1/12 + 1/6 = 1/12 + 2/12 = 3/12 = 1/4, so 4 hours.", "Adding the hours is not the combined rate.", "18 is the product of the hours.", "2 would be a faster rate than the two pipes together."], "Add the rates, not the hours. Together they fill one quarter of the tank per hour."))
    items.append(_q("crt2-q04", "A fee of 400 increases by 10%. What is the increase, not the new fee?", "quantitative", "medium", ["10", "40", "440", "360"], 1, ["10 is the percent, not the money.", "10% of 400 is 40.", "440 is the new fee.", "360 subtracts the increase."], "The question asks for the increase. 10% of 400 is 40."))
    items.append(_q("crt2-q05", "Pipe A fills a tank in 8 hours. Pipe B empties the same tank in 24 hours. Both are open. How long does a full fill take from empty?", "quantitative", "hard", ["6 hours", "12 hours", "16 hours", "32 hours"], 1, ["6 would be a faster net rate than A alone minus B.", "1/8 - 1/24 = 3/24 - 1/24 = 2/24 = 1/12, so 12 hours.", "16 adds the hours in a way the rates do not support.", "32 is slower than the empty rate alone."], "Subtract the emptying rate from the filling rate. The net rate fills the tank in 12 hours."))
    items.append(_q("crt2-q06", "Which number is the odd one out: 2, 4, 8, 9, 16?", "reasoning", "easy", ["2", "4", "9", "16"], 2, ["2 is a power of 2.", "4 is a power of 2.", "9 is not a power of 2.", "16 is a power of 2."], "2, 4, 8, and 16 are powers of 2. 9 is not."))
    items.append(_q("crt2-q07", "What is the next letter: A, C, E, G, ?", "reasoning", "easy", ["H", "I", "J", "K"], 1, ["H would be a step of 1 from G.", "The letters skip one each time: A, C, E, G, I.", "J skips two from G.", "K is further than the pattern."], "The pattern moves two letters each step. After G comes I."))
    items.append(_q("crt2-q08", "Ravi is Meera's brother. Meera is Ali's mother. Which relation must hold?", "reasoning", "medium", ["Ravi is Ali's maternal uncle", "Ravi is Ali's father", "Ali is Ravi's mother", "Meera is Ali's brother"], 0, ["Meera is the mother, and Ravi is her brother, so Ravi is Ali's maternal uncle.", "The sentences do not make Ravi the father.", "Ali is the child, not Ravi's mother.", "Meera is the mother, not the brother."], "Use only the two sentences. Ravi is the mother's brother."))
    items.append(_q("crt2-q09", "Every developer in the room has a laptop. Some people with laptops are interns. Which conclusion must follow?", "reasoning", "medium", ["Every developer is an intern", "Some developers must be interns", "The intern overlap with developers is not required", "No developer has a laptop"], 2, ["Some people with laptops are interns does not force every developer to be one.", "The interns could be people who are not developers.", "The sentences do not require any developer to be an intern.", "The first sentence says every developer has a laptop."], "Do not turn some into all, and do not force the two groups to overlap."))
    items.append(_q("crt2-q10", "What is the next letter: A, C, F, J, ?", "reasoning", "hard", ["N", "O", "P", "K"], 1, ["N is a step of 4 from J. The gaps are 2, 3, 4, so the next gap is 5.", "A to C is 2, C to F is 3, F to J is 4, J to O is 5.", "P is a step of 6.", "K is a step of 1."], "The gaps increase by one. After J, five letters on is O."))
    items.append(_q("crt2-q11", "Which sentence agrees in number?", "verbal", "easy", ["The tickets was closed.", "The ticket were closed.", "The ticket was closed.", "Were closed the ticket without a question."], 2, ["tickets is plural, so was does not agree.", "ticket is singular, so were does not agree.", "A singular subject takes was in this past statement.", "The auxiliary is placed as if this were a question, and it still does not form one."], "ticket is singular. Use was."))
    items.append(_q("crt2-q12", "In the phrase a brief note, which meaning of brief fits?", "verbal", "easy", ["A court case", "Short", "Loud", "Empty"], 1, ["A legal brief is a different use.", "A brief note is a short note.", "Loud is not the meaning.", "Empty is not the meaning."], "Here brief means short, not a legal case."))
    items.append(_q("crt2-q13", "Which sentence is consistent?", "verbal", "easy", ["She submit the form.", "She submits the form.", "She submitting the form.", "Submit she the form."], 1, ["submit does not agree with She in the present.", "submits agrees with a singular subject.", "submitting is not a finite verb here.", "The verb is placed before the subject without a question form."], "A singular subject in the present uses submits."))
    items.append(_q("crt2-q14", "Which sentence states a status without adding a cause the code does not show?", "verbal", "medium", ["The API returned 404.", "The API returned 404 because the intern was careless.", "The page must be broken because the status is 404.", "404 means the server crashed."], 0, ["The sentence names the status and stops.", "Carelessness is not in the status.", "A missing resource is not proof the page failed to start.", "404 is not a 5xx crash."], "Name the status. Do not add a person or a crash that the code does not show."))
    items.append(_q("crt2-q15", "Choose the completion: A prerequisite is something required ____ the next step.", "verbal", "medium", ["after", "before", "instead of", "without looking at"], 1, ["A prerequisite comes first, not after.", "before matches the ordinary meaning: required beforehand.", "instead of replaces the next step.", "The word does not mean ignoring the next step."], "A prerequisite is required before the next step."))
    items.append(_q("crt2-q16", "Using only this table, which channel opened the most tickets?", "data-interpretation", "easy", ["Email", "Chat", "Phone", "Form"], 0, ["Email shows 40 opened.", "Chat shows 25.", "Phone shows 15.", "Form shows 20."], "Compare the Opened column. Email is 40.", DI))
    items.append(_q("crt2-q17", "Using only this table, what is the total of the Opened column?", "data-interpretation", "easy", ["80", "100", "78", "40"], 1, ["80 drops Form or mis-adds.", "40 + 25 + 15 + 20 = 100.", "78 is the Closed column total, not Opened.", "40 is Email alone."], "Add the four Opened cells. Do not add Closed.", DI))
    items.append(_q("crt2-q18", "Using only this table, which channel has 0 in Reopened?", "data-interpretation", "easy", ["Email", "Chat", "Phone", "Form"], 3, ["Email shows 4.", "Chat shows 1.", "Phone shows 2.", "Form shows 0."], "Read the Reopened column. Form is 0.", DI))
    items.append(_q("crt2-q19", "Using only this table, what is Email's closed count divided by its opened count, as a percent?", "data-interpretation", "medium", ["40%", "75%", "30%", "133%"], 1, ["40 is the opened count, not the rate.", "30 / 40 = 0.75, which is 75%.", "30 is the closed count, not the percent.", "That divides opened by closed."], "Email closed 30 of 40 opened. That rate is 75%. Reopened is not in this ratio.", DI))
    items.append(_q("crt2-q20", "Using only Closed and Reopened, what is Phone's Closed minus Reopened?", "data-interpretation", "medium", ["8", "10", "12", "15"], 0, ["10 - 2 = 8.", "10 is Closed alone.", "12 adds them.", "15 is Phone's Opened count, not this difference."], "Subtract the two named cells. Do not call the result net success. The table does not define that.", DI))
    return items


ASSIGNMENTS = [
    {
        "key": "jb-assign-ticket-summary",
        "title": "Reject a blank ticket title in Java",
        "families": ["java-backend"],
        "skills": ["java", "methods"],
        "mode": "manual_review",
        "minutes": 50,
        "audience": "Fresher",
        "goal": "Write a TicketSummary type that keeps an id and a title, and refuses a blank title. Do not invent Untitled.",
        "requirements": [
            "Write the Java on your own computer or on paper. This site will not compile it.",
            "A public class named TicketSummary belongs in a file you can name TicketSummary.java.",
            "A null title and a title that is empty after trim both throw IllegalArgumentException with a reason that names title.",
            "Do not require a paid library or an API key.",
            "Do not claim this website ran the program.",
        ],
        "deliverables": [
            "The class text, or an HTTPS URL to a file a reviewer can open without a login wall",
            "One accepted call: id 4 and title \" VPN \" stores id 4 and title VPN",
            "One rejected call: title \"   \" throws and does not store a title",
        ],
        "hints": ["Check null before calling trim", "Use equals only if you compare titles; this assignment is about refusing a blank one"],
        "prerequisites": ["jb-class-and-main", "jb-methods-and-blank-title"],
        "rubric": [
            {"criterion": "Stores id and a trimmed non-blank title", "points": 25},
            {"criterion": "Rejects null and an all-space title with a reason that names title", "points": 25},
            {"criterion": "Does not invent Untitled or another replacement", "points": 15},
            {"criterion": "Accepted example and rejected example match the code", "points": 20},
            {"criterion": "States that this site did not compile or run the file", "points": 15},
        ],
        "sql_problem_slug": None,
        "brief": "Input data: id 4 with title \" VPN \", and a second call with title \"   \". Also consider null. Constraints: local or written Java only; no Spring; no paid plugin; HTTPS URL if you submit a URL. Estimated effort 50 minutes. A reviewer reads the text. The online runner stays locked.",
        "version": 1,
    },
    {
        "key": "fr-assign-ticket-form",
        "title": "A controlled ticket title field",
        "families": ["frontend-react"],
        "skills": ["react", "state"],
        "mode": "manual_review",
        "minutes": 45,
        "audience": "Fresher",
        "goal": "Write a small React function that shows a ticket title from props and edits a draft title in state.",
        "requirements": [
            "The card shows the title prop. Do not invent a title when the prop is missing.",
            "The draft field is a controlled input: value and onChange.",
            "After setTitle, do not claim the same line already sees the new value.",
            "This site will not render the component. No paid plugin.",
            "Submit text or an HTTPS URL a reviewer can open.",
        ],
        "deliverables": [
            "The component text, or an HTTPS URL",
            "The prop example title=\"Printer\"",
            "The state and input lines for the draft title",
            "One sentence on what title holds on the line after setTitle(\"VPN\") if it was empty",
        ],
        "hints": ["className if you add a CSS class", "Do not fetch /tickets inside this component"],
        "prerequisites": ["fr-component-props", "fr-state-input"],
        "rubric": [
            {"criterion": "Shows the title prop and does not invent a missing one", "points": 20},
            {"criterion": "Draft input is controlled with value and onChange", "points": 30},
            {"criterion": "Correctly states that the next line still sees the old title", "points": 20},
            {"criterion": "Does not claim this site rendered the component", "points": 15},
            {"criterion": "Submission is text or an HTTPS URL a reviewer can open", "points": 15},
        ],
        "sql_problem_slug": None,
        "brief": "Input data: parent title Printer, then a typed draft that should become VPN only on the next render. Constraints: local text only; this app will not mount React; no API key. Estimated effort 45 minutes. Manual review.",
        "version": 1,
    },
    {
        "key": "fs-assign-read-the-log",
        "title": "Read the six-row ticket log",
        "families": ["fullstack-web"],
        "skills": ["http", "status-codes"],
        "mode": "manual_review",
        "minutes": 40,
        "audience": "Fresher",
        "goal": "Count the statuses in the supplied log and explain one 400 and one 500 without swapping them.",
        "requirements": [
            "Use only the six rows in the brief. Do not add a request.",
            "Count 200, 201, 400, 404, and 500 separately.",
            "Name one field the page can show and one field the API received on the 201.",
            "State that this app does not execute the page or the API.",
            "Submit text. An HTTPS URL is allowed only if it is not required to complete the count.",
        ],
        "deliverables": [
            "Status counts",
            "Two sentences: why row 4 is 400, and why row 6 is 500",
            "One page field and one API field from the 201 row",
        ],
        "hints": ["201 is not a 200", "The query string is not used in this log"],
        "prerequisites": ["fs-request-response", "fs-two-programs"],
        "rubric": [
            {"criterion": "Status counts match the six rows, with 200 and 201 separate", "points": 30},
            {"criterion": "400 and 500 explanations are not swapped", "points": 25},
            {"criterion": "Names a page field without treating it as stored JSON", "points": 15},
            {"criterion": "Names a field the 201 response actually returned", "points": 15},
            {"criterion": "States that this app did not send the requests", "points": 15},
        ],
        "sql_problem_slug": None,
        "brief": "Input data, and the only rows you may use:\n\n| # | Method | Path | Body sent | Status | Body returned |\n| --- | --- | --- | --- | --- | --- |\n| 1 | GET | /tickets/1 | none | 200 | {\"id\": 1, \"title\": \"Printer\"} |\n| 2 | POST | /tickets | {\"title\": \"VPN\"} | 201 | {\"id\": 4, \"title\": \"VPN\"} |\n| 3 | GET | /tickets/9 | none | 404 | {\"error\": \"not found\"} |\n| 4 | POST | /tickets | {} | 400 | {\"error\": \"title is required\"} |\n| 5 | GET | /tickets/2 | none | 200 | {\"id\": 2, \"title\": \"Laptop\"} |\n| 6 | GET | /tickets/3 | none | 500 | {\"error\": \"server failed\"} |\n\nConstraints: no extra rows; no hosted API call; no paid tool. Estimated effort 40 minutes. Manual review of the written counts. This site will not send these requests.",
        "version": 2,
    },
]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    questions_payload = {"version": 1, "questions": questions()}
    difficulties = Counter(row["difficulty"] for row in questions_payload["questions"])
    expected = {"easy": 25, "medium": 17, "hard": 8}
    if dict(difficulties) != expected:
        raise SystemExit(f"difficulty {dict(difficulties)} != {expected}")
    prefixes = {"jb-": 10, "fr-": 10, "fs-": 10, "crt2-": 20}
    for prefix, count in prefixes.items():
        found = [row for row in questions_payload["questions"] if row["key"].startswith(prefix)]
        if len(found) != count:
            raise SystemExit(f"{prefix} has {len(found)}")
    crt = [row for row in questions_payload["questions"] if row["key"].startswith("crt2-")]
    skills = Counter(row["skill"] for row in crt)
    if skills != {"quantitative": 5, "reasoning": 5, "verbal": 5, "data-interpretation": 5}:
        raise SystemExit(f"CRT skills {dict(skills)}")
    for row in questions_payload["questions"]:
        if row["skill"] == "data-interpretation" and DI not in row["stem"]:
            raise SystemExit(f"{row['key']} DI table missing")
        correct = [opt for opt in row["options"] if opt["correct"]]
        if row["mode"] == "single" and len(correct) != 1:
            raise SystemExit(f"{row['key']} correct count")
    for assignment in ASSIGNMENTS:
        total = sum(item["points"] for item in assignment["rubric"])
        if total != 100:
            raise SystemExit(f"{assignment['key']} rubric {total}")

    materials_dir = ROOT / "materials"
    materials_dir.mkdir(parents=True, exist_ok=True)
    material_rows = []
    for item in MATERIALS:
        body = item["body"].strip() + "\n"
        rel = f"materials/{item['key']}.md"
        _write(ROOT / rel, body)
        material_rows.append({k: v for k, v in item.items() if k != "body"} | {"body_file": rel, "version": 2})

    log_rows = [
        {"n": 1, "method": "GET", "path": "/tickets/1", "body_sent": None, "status": 200, "body_returned": {"id": 1, "title": "Printer"}},
        {"n": 2, "method": "POST", "path": "/tickets", "body_sent": {"title": "VPN"}, "status": 201, "body_returned": {"id": 4, "title": "VPN"}},
        {"n": 3, "method": "GET", "path": "/tickets/9", "body_sent": None, "status": 404, "body_returned": {"error": "not found"}},
        {"n": 4, "method": "POST", "path": "/tickets", "body_sent": {}, "status": 400, "body_returned": {"error": "title is required"}},
        {"n": 5, "method": "GET", "path": "/tickets/2", "body_sent": None, "status": 200, "body_returned": {"id": 2, "title": "Laptop"}},
        {"n": 6, "method": "GET", "path": "/tickets/3", "body_sent": None, "status": 500, "body_returned": {"error": "server failed"}},
    ]
    status_counts = Counter(row["status"] for row in log_rows)
    if dict(status_counts) != {200: 2, 201: 1, 404: 1, 400: 1, 500: 1}:
        raise SystemExit(f"log counts {dict(status_counts)}")

    solutions = {
        "private": True,
        "note": "Reviewer file. Not imported into student briefs, packs, or the project description.",
        "assignments": {
            "jb-assign-ticket-summary": {
                "accepted": {"id": 4, "title": "VPN"},
                "rejected": "title is blank",
                "reference": "public class TicketSummary { private final int id; private final String title; public TicketSummary(int id, String title) { if (title == null || title.trim().isEmpty()) throw new IllegalArgumentException(\"title is blank\"); this.id = id; this.title = title.trim(); } }",
            },
            "fr-assign-ticket-form": {
                "prop": "Printer",
                "after_set_title_same_line": "",
                "reference": "function TicketCard({ title }) { const [draft, setDraft] = useState(''); return (<section><h1>{title}</h1><input value={draft} onChange={(event) => setDraft(event.target.value)} /></section>); }",
            },
            "fs-assign-read-the-log": {
                "counts": {"200": 2, "201": 1, "400": 1, "404": 1, "500": 1},
                "row4": "400 because the body was empty and the error says title is required",
                "row6": "500 because the server failed on GET /tickets/3",
                "page_field": "A heading can show Printer without that being the stored JSON",
                "api_field_on_201": "id 4 and title VPN",
            },
        },
        "project": {
            "milestone_counts": dict(status_counts),
            "do_not_execute": "This app does not run Java, React, or the ticket API.",
        },
    }
    dataset = {"synthetic": True, "currency": None, "requests": log_rows, "status_counts": {str(k): v for k, v in status_counts.items()}}

    revised = {"jb-q09", "jb-q10", "fr-q09", "fr-q10", "fs-q10", "crt2-q03"}
    for row in questions_payload["questions"]:
        if row["key"] in revised:
            row["version"] = 2
    _write(ROOT / "questions.json", json.dumps(questions_payload, indent=2) + "\n")
    _write(ROOT / "assignments.json", json.dumps({"version": 1, "assignments": ASSIGNMENTS}, indent=2) + "\n")
    _write(ROOT / "solutions.json", json.dumps(solutions, indent=2) + "\n")
    _write(ROOT / "dataset.json", json.dumps(dataset, indent=2) + "\n")

    scenario = (
        "A small desk logged six ticket requests. The page a person sees and the API that answers /tickets are two programs. "
        "This JobReady app stores the log so you can read it. It does not send the requests, compile Java, or render React.\n\n"
        "Related material: /learn/materials/fs-request-response and /learn/materials/fs-two-programs. "
        "Related assignments: /learn/assignments/jb-assign-ticket-summary, /learn/assignments/fr-assign-ticket-form, "
        "/learn/assignments/fs-assign-read-the-log. Related quiz: /learn/quizzes/pack-fullstack-web.\n\n"
        + LOG
        + "\n\nValidation: status counts are 200 twice, 201 once, 400 once, 404 once, 500 once. "
        "A missing payment table from last week's shop project is not this log. Do not invent a seventh request."
    )
    project = {
        "key": "ticket-request-log",
        "version": 1,
        "title": "Read a ticket request log",
        "families": ["java-backend", "frontend-react", "fullstack-web"],
        "skills": ["http", "status-codes"],
        "technology": "http",
        "category_key": "web",
        "module_title": "Request log",
        "minutes": 70,
        "scenario": scenario,
        "outcome": "A reviewer can see status counts, a 400 that is not a 500, and a note that this app did not execute the page or the API.",
        "dataset_file": "dataset.json",
        "materials": ["fs-request-response", "fs-two-programs", "jb-class-and-main", "fr-component-props"],
        "assignments": ["fs-assign-read-the-log", "jb-assign-ticket-summary", "fr-assign-ticket-form"],
        "reviewer_rubric": [
            {"criterion": "Counts match the six rows", "points": 30},
            {"criterion": "400 and 500 are not swapped", "points": 25},
            {"criterion": "Page field and API field are distinguished", "points": 25},
            {"criterion": "Note says this app did not execute the log", "points": 20},
        ],
        "milestones": [
            {"title": "Count the statuses", "type": "review", "deliverable": "Write the counts for 200, 201, 400, 404, and 500. Expected from the log: 2, 1, 1, 1, 1. Marking complete is not an automatic grade."},
            {"title": "Separate a 400 from a 500", "type": "review", "deliverable": "Explain row 4 and row 6. 400 is a rejected request with no title. 500 is a server failure on GET /tickets/3."},
            {"title": "Name the page field and the API field", "type": "review", "deliverable": "Name one thing a page can show, and one field the 201 response returned (id 4, title VPN). Do not treat them as the same store."},
            {"title": "Say what this app does not run", "type": "review", "deliverable": "Write that Java, React, and the ticket API are not executed here. Link the written assignment if you completed fs-assign-read-the-log."},
        ],
    }
    rubric_total = sum(item["points"] for item in project["reviewer_rubric"])
    if rubric_total != 100:
        raise SystemExit(f"project rubric {rubric_total}")
    _write(ROOT / "project.json", json.dumps(project, indent=2) + "\n")

    packs = [
        {"key": "pack-java-backend", "title": "Java classes, main, and blank titles", "kind": "technical", "families": ["java-backend"], "prefix": "jb-"},
        {"key": "pack-frontend-react", "title": "React props, state, and a controlled input", "kind": "technical", "families": ["frontend-react"], "prefix": "fr-"},
        {"key": "pack-fullstack-web", "title": "HTTP status codes in a ticket log", "kind": "technical", "families": ["fullstack-web"], "prefix": "fs-"},
        {"key": "pack-crt-2026-09-14", "title": "CRT: averages, rates, relations, sentences, and a channel table", "kind": "crt", "families": [], "prefix": "crt2-"},
    ]
    by_key = {row["key"]: row for row in questions_payload["questions"]}
    pack_rows = []
    instructions = (
        "Practice mode reveals explanations after you answer, using the existing practice rules. There is no negative marking. "
        "Java and React items are reading checks. This site does not compile Java or render React. "
        "HTTP items use the six-row log printed in the question. CRT data-interpretation items use the channel table printed in the question. "
        "Currency is unnamed. A job skill tag is topic context, not an employer confirmation. "
        "This pack is not last week's shop table."
    )
    for pack in packs:
        keys = [key for key in by_key if key.startswith(pack["prefix"])]
        if len(keys) != 10 and pack["kind"] == "technical":
            raise SystemExit(pack["key"])
        if pack["kind"] == "crt" and len(keys) != 20:
            raise SystemExit(pack["key"])
        pack_rows.append({k: v for k, v in pack.items() if k != "prefix"} | {"version": 1, "question_keys": keys, "instructions": instructions})

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
    for name in ("materials.json", "assignments.json", "questions.json", "project.json", "packs.json", "solutions.json", "dataset.json"):
        digest = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        manifest_items.append({"path": name, "sha256": digest, "content_type": name.split(".")[0]})
    for row in material_rows:
        blob = (ROOT / row["body_file"]).read_bytes()
        manifest_items.append({"path": row["body_file"], "sha256": hashlib.sha256(blob).hexdigest(), "content_type": "material_body", "key": row["key"]})
    manifest = {
        "batch_id": BATCH_ID,
        "schema_version": 1,
        "batch_date": "2026-09-14",
        "timezone": "Asia/Kolkata",
        "weekday": "Monday",
        "rotation_group": 2,
        "families": ["java-backend", "frontend-react", "fullstack-web"],
        "audience": AUDIENCE,
        "difficulty_questions": expected,
        "topic_overrides": None,
        "update_ids": None,
        "publish_mode": "PREVIEW",
        "change_reason": "Weekly preview batch for rotation group 2. Java class and methods, React props and state, HTTP request log. CRT uses a channel table, not the prior shop table.",
        "authorization": "local preview only; not a production publication",
        "items": manifest_items,
    }
    _write(ROOT / "manifest.json", json.dumps(manifest, indent=2) + "\n")
    print("WROTE", ROOT)
    print("QUESTIONS", len(questions_payload["questions"]), dict(difficulties))
    print("MATERIALS", len(material_rows))
    print("MANIFEST", hashlib.sha256((ROOT / "manifest.json").read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
