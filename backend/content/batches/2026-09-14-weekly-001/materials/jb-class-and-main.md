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

`public` means the runtime can call it. `static` means it belongs to the class, not to one object. `void` means it does not return a value. `String[] args` is the argument list. A method named `start` or `run` is not this entry point unless something else calls it.

## Worked example
`public class Ticket` is saved as `Ticket.java`. The compiler looks for the public class and the file name to match. Printing a title uses `System.out.println(title)`, which writes that text and then a line break to standard output. It does not save a ticket.

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
Oracle tutorial, "Classes": https://docs.oracle.com/javase/tutorial/java/javaOO/classes.html
