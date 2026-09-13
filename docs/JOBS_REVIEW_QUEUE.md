# Manual review queue — open these 10

Checked 2026-09-13. No further automated page requests. These are not approvals. Record `publish` or `withhold` in the application after you look; do not update the Jobs server.

Open `docs/JOBS_REVIEW_QUEUE.html` in a normal browser. `indeed / CQJ-20260909-0097` is local `withhold` and not verified. `CQJ-20260909-0303` and `CQJ-20260909-0071` are local `publish` evidence and still unverified, not a launch batch. The other seven IDs stay undecided.

| job_id | title | company | posted | Open this | Also recorded | Unresolved check |
|---|---|---|---|---|---|---|
| CQJ-20260909-0097 | Devops Interns | Unikwork | 2026-09-08 | [Employer page](https://unikwork.com/career-details/eyJpdiI6InE0K3dGbFpOODlLNkxkelk3L0tmdlE9PSIsInZhbHVlIjoiWUlGSmNPWDI4Q0srWk0rZStxYU5TZz09IiwibWFjIjoiYzE1MzBiZTdmNTQ4Y2RjYjlmMTk3ZjE4NWRhYTc0NTNmYWNiNDEwOGRjMGUzNmZkMmYzMDVkOGYzYzVkZmFmYSIsInRhZyI6IiJ9) | [Indeed](https://in.indeed.com/viewjob?jk=83211278d115c7c7) | Page showed the title. Confirm it is still accepting applications. Catalog role says Python Developer. |
| CQJ-20260909-0303 | Junior Data Engineer | AHL - Saaf AI | 2026-09-07 | [Ashby](https://jobs.ashbyhq.com/AHL-SaafAI/ed53ed8f-00aa-4fe6-b177-e1679143e32c) | [Indeed](https://in.indeed.com/viewjob?jk=a3fac1971c7af381) | Fetched page did not show the posting body. Confirm the requisition is this job and still open. |
| CQJ-20260909-0071 | Python Full Stack Developer | Young Minds Technology Solutions Pvt Ltd | 2026-09-08 | [Indeed](https://in.indeed.com/viewjob?jk=801ddca2ad29b100) | http apply URL, not opened | Indeed returned a shell. Confirm the listing is this job and still open. |
| CQJ-20260906-0057 | Full stack intern | ASCENT E-DIGIT SOLUTIONS PVT LTD | 2026-09-05 | [Indeed](https://in.indeed.com/viewjob?jk=96484bab41d90856) | http apply URL, not opened | Indeed shell. Catalog summary mentions React and FastAPI. Confirm it is an open internship, not a training ad. |
| CQJ-20260831-0092 | Full Stack Python Developer Intern | Kyle Solutions Private Limited | 2026-08-29 | [Indeed](https://in.indeed.com/viewjob?jk=368d94045f51f1e4) | http apply URL, not opened | Indeed shell. Confirm the posting is still this role. |
| CQJ-20260709-0143 | Data Analyst Project Intern | ByteDance | 2026-07-06 | [ByteDance careers](https://joinbytedance.com/search/7654066732550785333) | [Indeed](https://in.indeed.com/viewjob?jk=eb1095f4d42d82ca) | Careers chrome matched the host. Confirm requisition 7654066732550785333 is this intern role and still open. |
| CQJ-20260903-0068 | Software Intern | Blue Ripples Technologies | 2026-09-02 | [Zoho Recruit](https://blueripples.zohorecruit.com/jobs/Careers/446326000011053008/Software-Intern?source=CareerSite) | [Indeed](https://in.indeed.com/viewjob?jk=f0752dd4d9d7e1df) | Company page did not include the job title in fetched text. Confirm the requisition is this internship. |
| CQJ-20260822-0090 | PYTHON DJANGO DEVELOPER | bluegen solutions | 2026-08-22 | [Indeed](https://in.indeed.com/viewjob?jk=86342340a3d3ba69) | http apply URL, not opened | Indeed shell. Confirm it is an open fresher developer role. |
| CQJ-20260822-0093 | Python Full Stack Developer Intern | CLUSTOR COMPUTING | 2026-08-21 | [Indeed](https://in.indeed.com/viewjob?jk=d1d57530d9d11067) | http apply URL, not opened | Indeed shell. Confirm the posting is still this internship. |
| CQJ-20260909-0073 | Python Developer | Zooye Info Technologies | 2026-09-08 | [Indeed](https://in.indeed.com/viewjob?jk=fac62e57f0030fa3) | http apply URL, not opened | Indeed challenge/shell. Confirm the fresher Python role is still open. |

## Not in this queue

These are different findings. Do not treat them as the same check.

**Inaccessible.** Board or host blocked the earlier fetch. Not closed, not verified. Naukri rows `CQJ-20260712-0857`, `CQJ-20260712-0821`, `CQJ-20260909-0089`, `CQJ-20260831-0104`, `CQJ-20260831-0075`, `CQJ-20260816-0559`, `CQJ-20260719-0426`, `CQJ-20260719-0487`, `CQJ-20260719-0414`, `CQJ-20260712-1249`, `CQJ-20260712-1218`. Also `CQJ-20260831-0306` (Crypto Mize careers blocked), `CQJ-20260630-0023` (UPS careers blocked), `CQJ-20260906-0064` (medindia apply URL 403).

**Broken recorded apply URL.** `CQJ-20260903-0064` Arihant AI `https://arihantai.com/jobs/python-odoo-developer-internship-42` returned 404. That does not prove the job is closed. Indeed copy: https://in.indeed.com/viewjob?jk=fb92d2f3a38d0b3b

**Unsuitable from catalog text, already not proposed for publish.** Civil lab, electrical substation, tax, financial analyst, data-center technician, voice-process caller, and the Python training offer. See `docs/JOBS_REVIEW_BATCH.md`.
