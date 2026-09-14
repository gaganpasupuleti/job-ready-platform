## Objective
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
