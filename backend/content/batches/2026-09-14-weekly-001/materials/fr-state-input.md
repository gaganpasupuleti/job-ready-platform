## Objective
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
