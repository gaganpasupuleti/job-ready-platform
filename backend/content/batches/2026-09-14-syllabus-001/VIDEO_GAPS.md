# Video verification gaps (2026-09-14)

Optional YouTube recommendations were omitted for every published lesson in this batch.

Attempted candidate for percentages:
- URL: https://www.youtube.com/watch?v=Lvr2YsxG10o
- Channel claim from search: Khan Academy
- Topic claim from search: meaning of percent
- Verification date: 2026-09-14

Evidence result:
- Direct timedtext fetch for `lang=en` returned HTTP 200 with an empty body.
- Watch-page probe did not expose `captionTracks` / `timedtext` fields in the downloaded slice.
- Spoken-language transcript evidence was therefore unavailable in this environment.

Policy followed: do not invent a link and do not treat HTTP 200 alone as proof of relevance or English speech. Articles remain complete without a video.
