# JobReady typing practice V1

Branch: `feature/jobready-typing-practice-v1`
Base: `57ddac09eb5dd4061ace9df89107b172f5aaad9a` (GitHub master verified on 2026-09-15).
Route: `/practice/typing` behind the existing authenticated AppLayout.

## Reference audit and reuse decisions

| Reference | Inspected locations | Decision |
| --- | --- | --- |
| TypeView, `e2ca2586e0ff74b96fb4e3ee972ae858c26c5fac` | `src/pages/Practice.tsx`, `src/styles/tokens.css`, `src/store/useTypingStore.ts`, `src/components/ui/Keyboard.tsx`, README and light preview | Adapt its central passage, restrained green accent, compact mode selector, live metrics, progress indicator, and next-key guide to the existing JobReady shell. |
| CodeSprint, `54851cb4e1e4d91450f75218c840d1a6a6648de7` | `hooks/useTypingEngine.ts`, `lib/scoring.ts`, `lib/code-panel.ts`, package manifest and LICENSE | Adapt language selection, multiline indentation behavior, frozen completion snapshots, and separation of raw speed from correct progress. Use an independent small reducer rather than importing the Next.js/Chakra/Monaco runtime. |

Both repositories were inspected via the GitHub connector and cloned read-only outside JobReady. Their histories were not merged. TypeView's README declares MIT but the inspected tree contains no LICENSE file. CodeSprint has an MIT license, copyright 2025 cwklurks. This implementation independently recreates selected behavior and layout concepts; it does not vendor their components, assets, prose, snippets, or dependencies. All bundled practice material is newly authored for JobReady.

Rejected: TypeView's global key handler (it interferes with custom-text editing and ignores Enter), unscoped localStorage, global theme changes, confetti and reward system; CodeSprint's Next.js runtime, AI providers/API keys, third-party LeetCode/algorithm corpus, percentile claims, and separate leaderboard. No additional packages or external APIs were introduced.

## Delivered

- Text, code, and custom passage practice, exposed in Practice Hub, practice destinations, and More.
- Foundation, intermediate and advanced drills; 15 original code snippets across Python, SQL, JavaScript, Java and C++.
- 30/60/120-second limits or a full passage. Runs end when the passage finishes or the deadline is reached, whichever occurs first.
- First insertion starts the clock; idle time does not count. Once started, the clock continues when focus leaves or the tab is hidden. Deadline checks also run on input and visibility changes.
- Correct/error character styling, caret following, progress, WPM, raw WPM, accuracy, elapsed/remaining time, current-session error characters, same-mode/level/duration personal best.
- Enter inserts a newline. Tab inserts up to four expected indentation spaces or an expected literal tab only within indentation. Otherwise Tab moves focus; Shift+Tab always moves focus. Escape leaves the typing field.
- Input is scoped to an accessible textarea, with paste/drop blocked for measured input. Custom content may be pasted into the separate editor. English ASCII input, punctuation, tabs and newlines only; custom passages are capped at 2,000 characters.
- Session-local light/dark practice themes and show/hide keyboard. No application-wide theme mutations.
- A bounded 50-result history per authenticated user in the current browser; eight recent rows displayed. Reads validate stored data; saves are idempotent by run UUID. Storage failure shows a message and preserves the in-memory result. Custom passage text is not persisted.

## Metric policy

- WPM = currently correct character positions / 5 / elapsed minutes, rounded.
- Raw WPM = all inserted characters / 5 / elapsed minutes, rounded. Backspace is not an insertion.
- Accuracy = correct insertion attempts / all insertion attempts. Correcting an error does not erase its historical contribution.
- An indentation Tab expands the expected spaces and counts those inserted characters; auto-indent is never applied invisibly.
- Finished state cannot be reopened or modified. The last character is included in the saved snapshot.
- Scores measure self-practice. They are client-calculated, editable via browser storage, and never treated as verified skills, assessment evidence, or hiring readiness.

## Compatibility and limitations

Existing authentication, backend, jobs, roadmap work, SQL sandbox, MCQ, coding execution and readiness are unchanged. Code snippets are never executed; no Judge0 dependency or successful-execution claim is introduced. Frontend dependencies and lockfile are unchanged.

V1 history has no server or cross-device sync. Concurrent tabs can overwrite each other's history list, although repeated saves of one run are deduplicated. History is browser storage, not a security boundary against someone controlling the browser. Custom passages are transient. No multiplayer, speech, IME/non-English input, adaptive curriculum, or runtime language grading. An abandoned run is not saved. Practice material is a starter set, not a full typing curriculum.

## Verification

- Production TypeScript/Vite build: passed.
- Repository lint command: exit 0 with existing warnings. Feature files checked separately.
- Pure session-engine and storage contract tests: 2 passed (2026-09-15).
- Feature-only lint: passed without warnings.
- `git diff --check`: passed.
- Seven authored browser scenarios cover completion/correction/persistence, language/Enter/Tab/retry/no execution, deadline expiry, paste/focus/mobile layout, account isolation/corruption, storage failure/light-dark layouts, and authentication guard.
- Browser execution was blocked by missing Chromium; the official Playwright download timed out and ultimately returned 502. Browser scenarios failed at launch, not on feature assertions. The separate browser connection also could not reach the local app. No responsive visual acceptance or browser pass is claimed.

Run locally after `npm ci` and `npx playwright install chromium`:

```bash
cd frontend
npm run build
npm run lint
npx playwright test e2e/typing.spec.ts --project=desktop
```

These tests mock only the auth response, then exercise the actual frontend. They do not prove real backend authentication integration. The engine/storage cases run without a browser:

```bash
npx playwright test e2e/typing.spec.ts --project=desktop --grep 'engine:|history storage:'
```

## Applying the delivered patch

The GitHub connector reported pull-only permissions. This feature was committed in a separate local worktree, not pushed, merged or deployed. The downloadable `jobready-typing-practice-v1.patch` is a `git format-patch` export of the feature commit.

From an existing JobReady repository, create a new isolated worktree using the exact base (do not switch or reset unfinished work):

```bash
git fetch origin
git worktree add -b feature/jobready-typing-practice-v1 ../jobready-typing 57ddac09eb5dd4061ace9df89107b172f5aaad9a
cd ../jobready-typing
git am /path/to/jobready-typing-practice-v1.patch
```

If the branch already exists, inspect and use the appropriate existing worktree instead of overwriting it. Run the browser checks above before merging. Full source, reference audit, limitations and tests are all included in the patch.
