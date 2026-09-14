## Objective
Show a ticket title that the parent passed in. Do not fetch it inside this component.

## Prerequisite
You can read a JavaScript function and a value in curly braces.

## A component returns UI
In this material, a component is a function. It returns a description of what should appear, not a screenshot and not a saved ticket. `function TicketCard({ title }) { return <h1>{title}</h1>; }` shows the `title` prop.

The parent supplies the value: `<TicketCard title="VPN" />`. The child does not invent a title when the prop is missing. A missing title should be visible as missing, not replaced with a guessed label.

## JSX names
The HTML `class` attribute is written `className` in JSX. That is a JavaScript name, not a second kind of CSS.

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
