## Objective
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
