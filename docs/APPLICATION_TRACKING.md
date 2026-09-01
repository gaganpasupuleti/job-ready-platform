# Application tracking

## Statuses

`saved`, `preparing`, `applied`, `screening`, `assessment`, `interview`, `offer`, `rejected`, `withdrawn`, `accepted`, `ghosted`

## Rules

- One application per user per job (unique constraint)
- Mark Applied is idempotent
- Every status change appends `application_status_history` (immutable)
- `applied_at` set when status becomes `applied` if not already set

## Follow-ups

`next_follow_up_at` on application — surfaced as overdue / today / upcoming. No email automation in Build 9.

## Privacy

Students only see their own applications and notes. Admin manages job content, not a global student-notes browser.
