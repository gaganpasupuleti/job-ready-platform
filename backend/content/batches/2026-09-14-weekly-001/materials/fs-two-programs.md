## Objective
Keep the browser page and the ticket API as two programs that exchange messages.

## Prerequisite
You can read method, path, and status from `fs-request-response`.

## Two programs
The page is what a person looks at. The API is what answers `/tickets`. They can fail separately. A heading that shows `Printer` is the page. It is not, by itself, the JSON the API stored. The successful create in the log is the evidence for what the API received: JSON `{ "title": "VPN" }` and response `{ "id": 4, "title": "VPN" }`.

## Worked example
Request 4 in the log from `fs-request-response` is `POST /tickets` with `{}` and status 400. The page may still show an empty input. The API rejected the request because the title was missing. Request 6 is `GET /tickets/3` with status 500. RFC 9110 puts 500 in the 5xx (Server Error) class. That class does not say the browser calculated a title incorrectly. The conclusion that a 500 does not prove a page calculation error is an application of that class, not a sentence copied from the RFC.

## Common mistakes
- Using a 500 as evidence that the page's arithmetic was wrong.
- Treating the page field and the JSON field as the same store.
- Claiming this JobReady application executed the page or the API. It stores the log and a written review. It does not run Java, React, or the ticket service.

## Exercise
Write two sentences. One names a field the page shows. One names a field the API received on the 201 response. Do not add a field that is not in the log.

## Summary
The page shows. The API receives and answers. Status 400 and status 500 are different failures. This site does not execute either side.

## References
RFC 9110, HTTP Semantics, status codes (plain text, section 15): https://www.rfc-editor.org/rfc/rfc9110.txt
