# Jobs catalog review batch — 2026-09-13

Not executed. Do not write these statuses to the Jobs server until Gk approves a specific `job_id` list. This pass did not change source production data.

## How statuses are maintained

No approval interface exists in this application or on the Jobs server.

- Engine: PostgreSQL 18.6, database `railway`, schema `public`, only table `validated_jobs`.
- No column comments, triggers, functions, or check constraint on `approved_status`.
- Observed values only: `NEEDS_REVIEW` (4590, `manual_review_needed=true`) and `PENDING` (731, flag false). Both have `link_status=active`.
- `PENDING` is not approval. `link_status=active` is not publication approval.
- `APPROVED` and `PUBLISHED` are the publication-gate values agreed for this pilot. The catalog writer has never stored them. Do not add a competing `REJECTED` status.
- The admin Jobs screen edits canonical `jobs` rows. It does not review `validated_jobs`.
- The documented writer is the external CodeQuest collector `push_validated_to_job_ready`. That code is not in this repository. The 2026-09-06 sync note (`aa4c311`) imported active links and explicitly did not gate on `approved_status`. This pilot does not restore that bypass.

Reject below means: leave `PENDING`, and do not include the id in a later approve list. It is not a new status.

## Verification

Checked 2026-09-13 20:34 IST (15:04 UTC) with a browser-like GET, 12 second timeout. HTTP 200, HTTPS, and `link_status=active` are not treated as proof the posting is open.

Indeed 200 responses were job-board page shells. Title text in the shell or URL is not evidence the application still targets that open job. Naukri and several employer hosts returned 403. Those rows are manual checks. A 404 on one recorded apply URL is not treated as “job closed.”

Proposed source writes: **none**.

```sql
-- NOT EXECUTED. Do not run.
-- UPDATE public.validated_jobs
-- SET approved_status = 'APPROVED', updated_at = now()
-- WHERE job_id IN (/* Gk-approved ids only */)
--   AND approved_status = 'PENDING'
--   AND manual_review_needed IS FALSE;
```

The `IN` list is empty until a later manual check confirms the open posting.

## Batch (39)

Experience is the catalog bucket, not a verified years requirement. Role is the catalog `actual_role_name`; several are classification errors. Apply URL is the recorded `apply_url`. Job URL is `job_url`.

### Reject — do not approve, no status write

Catalog text shows the labeled role is wrong, or the title is not an open technology job. Page fetch was not used as the reject reason.

| job_id | title | company | bucket / role | source | posted | Why reject |
|---|---|---|---|---|---|---|
| CQJ-20260822-0302 | Lab Analyst - Civil | ECO Paryavaran Group | Fresher / Data Analyst | indeed | 2026-08-22 | Civil lab work labeled data analyst |
| CQJ-20260822-0412 | Associate Engineer-Electrical (Substation) | Black & Veatch | Fresher / Data Engineer | indeed | 2026-08-21 | Electrical role labeled data engineer |
| CQJ-20260902-0250 | Analyst - TAX - Transfer Pricing - Pune | EY | Fresher / Data Analyst | indeed | 2026-08-28 | Tax role labeled data analyst |
| CQJ-20260909-0250 | Financial Analyst - Equity and Fixed Income | Bahar Infocons Pvt. Ltd. | Fresher / Data Analyst | indeed | 2026-09-07 | Finance role labeled data analyst |
| CQJ-20260906-0279 | Data Center Technician Intern, 2027 | Google | Internship / Data Engineer | indeed | 2026-09-04 | Facilities technician labeled data engineer |
| CQJ-20260719-0399 | Walk-in Freshers - AR caller | AGS Health | Internship / Python Developer | naukri | unknown | Voice-process role labeled Python |
| CQJ-20260903-0049 | Python development training | Skiez Technologies India Pvt Ltd | Fresher / Python Developer | indeed | 2026-09-02 | Training offer, not an open developer job |

Recorded URLs for those rows remain in the source table. They were not treated as verified applications.

### Manual check — do not approve yet

Board or host blocked a content check, or a 200 page did not show that this application still opens that job. Do not mark them closed.

| job_id | title | company | bucket / role | source | posted | apply URL | job URL | Check | Reason |
|---|---|---|---|---|---|---|---|---|---|
| CQJ-20260909-0096 | DevOps Engineer Intern | Welldone Healthcare Pvt. Ltd | Internship / Python Developer | indeed | 2026-09-09 | http://in.indeed.com/job/devops-engineer-intern-healthtech-startup-465e39736cc42f48 | https://in.indeed.com/viewjob?jk=465e39736cc42f48 | 200 shell | DevOps title labeled Python; Indeed shell, not verified open |
| CQJ-20260909-0103 | Software Associate Intern | EN-TECHZ INNOVATIONS | Internship / Python Developer | indeed | 2026-09-08 | http://in.indeed.com/job/software-associate-intern-dab163fb17fbba84 | https://in.indeed.com/viewjob?jk=dab163fb17fbba84 | 200 shell | Summary says a free 3-month program; page not verified |
| CQJ-20260909-0097 | Devops Interns | Unikwork | Internship / Python Developer | indeed | 2026-09-08 | https://unikwork.com/career-details/… | https://in.indeed.com/viewjob?jk=83211278d115c7c7 | employer page showed title | Role text visible; apply-open state not confirmed. Labeled Python |
| CQJ-20260909-0073 | Python Developer | Zooye Info Technologies | Fresher / Python Developer | indeed | 2026-09-08 | http://in.indeed.com/job/python-developer-fac62e57f0030fa3 | https://in.indeed.com/viewjob?jk=fac62e57f0030fa3 | 200 blocked shell | Indeed challenge page |
| CQJ-20260909-0071 | Python Full Stack Developer | Young Minds Technology Solutions Pvt Ltd | Fresher / Python Developer | indeed | 2026-09-08 | http://in.indeed.com/job/python-full-stack-developer-801ddca2ad29b100 | https://in.indeed.com/viewjob?jk=801ddca2ad29b100 | 200 shell | Title in shell only |
| CQJ-20260909-0303 | Junior Data Engineer | AHL - Saaf AI | Entry (1-2 yrs) / Data Engineer | indeed | 2026-09-07 | https://jobs.ashbyhq.com/AHL-SaafAI/ed53ed8f-00aa-4fe6-b177-e1679143e32c | https://in.indeed.com/viewjob?jk=a3fac1971c7af381 | 200, little text | Ashby page did not expose the posting body |
| CQJ-20260906-0057 | Full stack intern | ASCENT E-DIGIT SOLUTIONS PVT LTD | Internship / Python Developer | indeed | 2026-09-05 | http://in.indeed.com/job/full-stack-intern-96484bab41d90856 | https://in.indeed.com/viewjob?jk=96484bab41d90856 | 200 shell | Summary mentions React and FastAPI; page not verified |
| CQJ-20260906-0064 | Full-Stack AI Developer | medindia | Fresher / Python Developer | indeed | 2026-09-03 | https://www.medindia.net/workformedindia.asp# | https://in.indeed.com/viewjob?jk=bb7610093c2cacfb | 403 | Apply URL is a fragment page and was forbidden |
| CQJ-20260903-0068 | Software Intern | Blue Ripples Technologies | Internship / Python Developer | indeed | 2026-09-02 | https://blueripples.zohorecruit.com/jobs/Careers/446326000011053008/Software-Intern | https://in.indeed.com/viewjob?jk=f0752dd4d9d7e1df | 200, title absent | Company site did not show the job title in fetched text |
| CQJ-20260903-0064 | Python (Odoo) Developer Internship | Arihant AI | Internship / Python Developer | indeed | 2026-09-02 | https://arihantai.com/jobs/python-odoo-developer-internship-42 | https://in.indeed.com/viewjob?jk=fb92d2f3a38d0b3b | 404 | Recorded apply URL did not open. Not claimed closed |
| CQJ-20260902-0065 | Python Developer Intern | Tamizha Media Pvt Ltd | Internship / Python Developer | indeed | 2026-09-02 | http://in.indeed.com/job/python-developer-intern-61320ce62b3f82e4 | https://in.indeed.com/viewjob?jk=61320ce62b3f82e4 | 200 shell | Indeed challenge/shell |
| CQJ-20260831-0119 | Software Intern | ipsr solutions ltd | Internship / Python Developer | indeed | 2026-08-29 | http://in.indeed.com/job/software-intern-e312104f2d8e7d9f | https://in.indeed.com/viewjob?jk=e312104f2d8e7d9f | 200 shell | Title in shell only |
| CQJ-20260831-0092 | Full Stack Python Developer Intern | Kyle Solutions Private Limited | Internship / Python Developer | indeed | 2026-08-29 | http://in.indeed.com/job/full-stack-python-developer-intern-368d94045f51f1e4 | https://in.indeed.com/viewjob?jk=368d94045f51f1e4 | 200 shell | Indeed chrome, not a confirmed posting |
| CQJ-20260831-0306 | Business Intelligence Analyst | Crypto Mize | Fresher / Data Analyst | indeed | 2026-08-28 | https://cryptomize.com/careers/job-openings/business-intelligence-analyst/ | https://in.indeed.com/viewjob?jk=3ea5e27560e0e0ff | 200 blocked | Employer careers URL blocked |
| CQJ-20260822-0124 | Python Intern | camerinfolks Pvt.Ltd | Internship / Python Developer | indeed | 2026-08-22 | http://in.indeed.com/job/python-intern-a3b41985a5b18672 | https://in.indeed.com/viewjob?jk=a3b41985a5b18672 | 200 shell | Title in shell only |
| CQJ-20260822-0090 | PYTHON DJANGO DEVELOPER | bluegen solutions | Fresher / Python Developer | indeed | 2026-08-22 | http://in.indeed.com/job/python-django-developer-86342340a3d3ba69 | https://in.indeed.com/viewjob?jk=86342340a3d3ba69 | 200 shell | Indeed chrome |
| CQJ-20260822-0095 | Python Developer Internship | Drugwrite | Internship / Python Developer | indeed | 2026-08-21 | http://in.indeed.com/job/python-developer-internship-part-time-opportunity-5601124de2eff225 | https://in.indeed.com/viewjob?jk=5601124de2eff225 | 200 shell | Title in shell only |
| CQJ-20260822-0093 | Python Full Stack Developer Intern | CLUSTOR COMPUTING | Internship / Python Developer | indeed | 2026-08-21 | http://in.indeed.com/job/python-full-stack-developer-intern-d1d57530d9d11067 | https://in.indeed.com/viewjob?jk=d1d57530d9d11067 | 200 shell | Title in shell only |
| CQJ-20260712-0857 | Junior Power BI Developer | SRM Technologies | Entry (1-2 yrs) / Power BI Analyst | naukri | 2026-07-10 | https://www.naukri.com/job-listings-junior-power-bi-developer-srm-technologies-chennai-2-to-7-years-100726507114 | same | 403 | Board blocked. URL text says 2 to 7 years, catalog says entry |
| CQJ-20260712-0821 | Python Developer | Ocean Software Technologies | Fresher / Python Developer | naukri | 2026-07-09 | https://www.naukri.com/job-listings-python-developer-ocean-software-technologies-bengaluru-0-to-1-years-090726500369 | same | 403 | Board blocked |
| CQJ-20260709-0143 | Data Analyst Project Intern | ByteDance | Internship / Data Analyst | indeed | 2026-07-06 | https://joinbytedance.com/search/7654066732550785333 | https://in.indeed.com/viewjob?jk=eb1095f4d42d82ca | 200 careers chrome | Host matched; specific requisition body not confirmed. Summary says training and quality, 2026 start |
| CQJ-20260704-0122 | Walk IN Drive - Python Developer - 7th July | Rentokil Initial | Fresher / Python Developer | indeed | 2026-07-04 | https://apply.workable.com/j/6CE4F934A5 | https://in.indeed.com/viewjob?jk=13f2e2f8ec644a7d | not opened as an open posting | Dated walk-in. Do not assume closed or still open |
| CQJ-20260630-0023 | Intermediate Applications Developer - Java, SQL Server | UPS | Entry (1-2 yrs) / Java Backend Developer | indeed | 2026-06-30 | https://www.jobs-ups.com/global/en/job/UPBUPSGLOBALR26013231EXTERNALENGLOBAL/Intermediate-Applications-Developer-Java-Spring-Boot-AMQ-WMQ-SQL-Server | https://in.indeed.com/viewjob?jk=f1007476547ecb18 | 200 blocked | SQL-relevant; employer page blocked |
| CQJ-20260909-0089 | Intern - Application Support (SQL, Python) | Ventura | Internship / Python Developer | naukri | unknown | https://www.naukri.com/job-listings-intern-application-support-sql-python-ventura-thane-0-to-1-years-070926500865 | same | 403 | Relevant title; board blocked. Posting date missing |
| CQJ-20260831-0104 | Python Django Intern | Techciti Software Consulting | Internship / Python Developer | naukri | unknown | https://www.naukri.com/job-listings-python-django-intern-online-virtual-offline-techciti-software-consulting-bengaluru-0-to-3-years-240826504824 | same | 403 | Board blocked. URL text says 0 to 3 years |
| CQJ-20260831-0075 | Immediate Hiring: Python Developer Trainee | Arcraft Infotech | Entry (1-2 yrs) / Python Developer | naukri | unknown | https://www.naukri.com/job-listings-immediate-hiring-python-developer-trainee-arcraft-infotech-kochi-kozhikode-thiruvananthapuram-0-to-2-years-240826004276 | same | 403 | Board blocked |
| CQJ-20260816-0559 | Application Production Support (SQL) | DMart | Fresher / it-support | naukri | unknown | https://www.naukri.com/job-listings-application-production-support-sql-dmart-mumbai-mumbai-all-areas-0-to-0-years-060826011300 | same | 403 | SQL-relevant; board blocked |
| CQJ-20260719-0426 | Trainee Consultant Data & Analytics | SSR Fintech Ltd. | Entry (1-2 yrs) / Data Engineer | naukri | unknown | https://www.naukri.com/job-listings-trainee-consultant-data-analytics-ssr-fintech-ltd-bengaluru-0-to-2-years-140726503713 | same | 403 | Board blocked. Consultant title may not be a student role |
| CQJ-20260719-0487 | Data Analyst | Najuk Salar Shahabadi | Fresher / Data Analyst | naukri | unknown | https://www.naukri.com/job-listings-data-analyst-najuk-salar-shahabadi-hyderabad-pune-bengaluru-0-to-2-years-150726025528 | same | 403 | Board blocked. Company name looks like a person |
| CQJ-20260719-0414 | Backend Engineer Intern | Thyrocare | Internship / Data Engineer | naukri | unknown | https://www.naukri.com/job-listings-backend-engineer-intern-thyrocare-bengaluru-0-to-1-years-190726003853 | same | 403 | Relevant intern; labeled data engineer; board blocked |
| CQJ-20260712-1249 | Django Developer | Markytics | Internship / Python Developer | naukri | unknown | https://www.naukri.com/job-listings-django-developer-markytics-pune-0-to-1-years-090726008367 | same | 403 | Board blocked. Bucket says internship, title does not |
| CQJ-20260712-1218 | Walk-in Python Software Developer | Trios Technologies | Fresher / Python Developer | naukri | unknown | https://www.naukri.com/job-listings-python-software-developer-trios-technologies-chennai-0-to-1-years-270925004918 | same | 403 | Board blocked. URL slug contains 270925; do not assume the date |

Manufacturing QC rows, including `CQJ-20260712-1082` Walk-in Qc Inspector, were not included. They stay `NEEDS_REVIEW` and unpublished.

## After Gk confirms a subset

1. Write only those `job_id` values to `approved_status='APPROVED'` on the source, keeping `manual_review_needed=false`.
2. Do not bulk-update the other 731 pending rows.
3. Then a local disposable apply can publish that snapshot. Production apply stays disabled until that reviewed list exists.
