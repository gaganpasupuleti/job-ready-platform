## Objective
Return a usable title, or stop when the title is blank. Do not invent a replacement.

## Prerequisite
You can write a class and the `main` signature from `jb-class-and-main`.

## A method returns one result
A method has a name, parameters, and a return type. `String cleaned(String title)` promises a `String` or a thrown exception. It does not silently replace a blank title with `Untitled` unless a brief explicitly says to.

## Worked example
Input `" VPN "` becomes `"VPN"` after trim. Input `"   "` becomes empty after trim, so the method throws `IllegalArgumentException` with the reason `title is blank`. Input `null` fails the same check before `trim` is called, so it does not throw `NullPointerException` from `trim`.

## Comparing text
`title.equals("VPN")` asks whether the characters match. `title == "VPN"` asks whether both sides are the same object. Two different `String` objects can hold the same characters. Use `equals` for the title check.

## Common mistakes
- Calling `trim` on null.
- Catching `Exception` and printing `failed`, which also hides failures you did not mean to handle.
- Reading a local `int count;` before assigning it. The compiler does not give a local variable a default.

## Exercise
On your computer, call the check with `" VPN "` and with `"   "`. Record the returned title and the exception message. This site will not run the file.

## Summary
Trim, then reject an empty result. Use `equals` for characters. Catch the exception you named.

## References
Oracle tutorial, "Defining Methods": https://docs.oracle.com/javase/tutorial/java/javaOO/methods.html
Oracle tutorial, "What Is an Exception?": https://docs.oracle.com/javase/tutorial/essential/exceptions/definition.html
