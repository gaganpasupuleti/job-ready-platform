## Objective
Read one line of a request log without inventing a second request.

## Prerequisite
You can read a table and count rows that share a value.

## Method, path, status
A request line in this batch has a method and a path. The matching response has a status code. RFC 9110 defines the class by the first digit: 1xx (Informational), 2xx (Successful), 3xx (Redirection), 4xx (Client Error), and 5xx (Server Error). This material uses only the codes in the supplied log.

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
RFC 9110, HTTP Semantics, status codes (plain text, section 15): https://www.rfc-editor.org/rfc/rfc9110.txt
