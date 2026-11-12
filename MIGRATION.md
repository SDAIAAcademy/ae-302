# Migration of agentic-ai

This course was moved from the previous slide system by `academy migrate`. The inner markup of every slide is unchanged; each `<section>` tag got an `id`, section slides a session number, lab slides their lab id, and a slide drawn with coordinates or holding a layout of the course's own stylesheet that cannot reflow `data-read="scaled"`. Each deck keeps its old file name as its unit id, so its published address keeps answering. `labs/` and `assets/` are copied as they were.

Run the engine from this folder with `node academy.mjs <command>` (`check`, `build`, `check --layout --shots`); it finds the engine in `$ACADEMY_ENGINE`, then the folder named in `.academy-engine`, then `../engine`. Or run `node <engine>/bin/academy.mjs <command> --root <this folder>`.

## What is left, and how long it takes

About **1 h 5 min** of a person's work before `academy check` passes, and about **5 h 59 min** more to clear its warnings, which the house standard also asks for. The estimate counts each task below and each finding of `academy check` as this migration found them; a coding agent does the same work faster, but a person still decides the outcomes of each session and reviews the checkpoints.

| Work | Minutes |
|---|---|
| The tasks under "Needs a person" (3) | 57 |
| 4 × `a11y/svg` (error) | 8 |
| 37 × `slide/dense` (warning) | 185 |
| 4 × `notes/ratio` (warning) | 99 |
| 15 × `quiz/why` (warning) | 75 |

Then `node academy.mjs check --layout --shots` opens every slide in Chrome (a few minutes for a course of five decks). It reports what the static check cannot see: a slide whose content is cut off or wider than the slide (`layout/overflow`, about 5 minutes each; long lines of code are the usual case, and the old system's own `?check` reported most of them too) and slides that do not reflow in the reading view on a phone (`layout/phone-wide`, `layout/phone-text`). Compare its contact sheets (`.shots/<lang>/<deck>/sheet-<n>.png`) with the old decks.

## Slides

Counted in the old deck and in the new source; "a → b" where they differ.

| Old deck | New deck | Slides | Speaker notes | Checkpoints | Lab slides | Pictures | Fragments | Break slides dropped |
|---|---|---|---|---|---|---|---|---|
| slides/day1.html | slides/day1.html | 63 | 21 | 4 | 4 | 1 | 3 | 0 |
| slides/day2.html | slides/day2.html | 44 | 5 | 4 | 4 | 1 | 0 | 0 |
| slides/day3.html | slides/day3.html | 38 | 2 | 4 | 4 | 1 | 0 | 0 |
| slides/day4.html | slides/day4.html | 33 | 2 | 3 | 4 | 1 | 0 | 0 |
| slides/day5.html | slides/day5.html | 14 | 2 | 0 | 0 | 0 | 0 | 0 |
| All | | 192 | 32 | 15 | 16 | 4 | 3 | 0 |

## Rebuilt from the old files

- slides/day1.html → slides/day1.html: "From a Language Model to an Agent", 4 sessions, 4 labs.
- slides/day2.html → slides/day2.html: "Context Engineering", 4 sessions, 4 labs.
- slides/day3.html → slides/day3.html: "Harness & Loop Engineering", 4 sessions, 4 labs.
- slides/day4.html → slides/day4.html: "Graph Engineering & Production", 4 sessions, 4 labs.
- slides/day5.html is the capstone day (no lab slides; presentation slides or a capstone title): its sessions are not sessions in the new engine, so data-session was removed from its section slides.
- 6 course outcomes from the list of outcomes on index.html (LO1 to LO6).
- The audience, from the "Audience" paragraph of index.html.
- 1 prerequisite from the "Environment" paragraph of index.html.
- The capstone summary, from the "Capstone" section of index.html (its paragraphs and its list of options).
- The capstone rubric: Working system (code + saved run evidence) 25, Context and harness engineering decisions 25, Evaluation and error analysis 20, Security, governance and operability 20, Presentation and reproducibility (README.md) 10.
- Title "Agentic AI Systems Engineering", track ai-engineering, language en; the id "agentic-ai" comes from the folder name.
- README.md, and nuggets.md, which it links to.

## Needs a person

- Which outcomes each session serves: write "lo" for each of the 16 sessions in course.json (["LO1"], or more than one), from the session titles and the slides; the old decks do not say, so until then "academy check" reports every outcome as not covered (lo/uncovered). (about 32 min)
- The capstone in course.json: add "submission" (what is handed in, and when) and "talk_minutes" and "qa_minutes" (the length of a presentation and of its questions; leave both out when nobody presents, as in a capstone whose README is the presentation); the old course page and capstone deck do not state them in a form the migration can read. (about 5 min)
- 2 parts of index.html that the migration does not read (listed under "Left out of index.html"): keep or drop each. (about 20 min)

## What `academy check` reports

On the course as migrated, apart from the codes a task above clears (`lo/uncovered`). `node academy.mjs check` prints each place with what to do.

| Code | Level | Findings | Minutes | First places |
|---|---|---|---|---|
| `a11y/svg` | error | 4 | 8 | slides/day1.html:203, slides/day2.html:565, slides/day3.html:63 … |
| `slide/dense` | warning | 37 | 185 | slides/day1.html:15, slides/day1.html:27, slides/day1.html:139 … |
| `notes/ratio` | warning | 4 | 99 | slides/day2.html, slides/day3.html, slides/day4.html … |
| `quiz/why` | warning | 15 | 75 | slides/day1.html:422, slides/day1.html:704, slides/day1.html:1000 … |

## Left out of index.html

- index.html line 134: "Setup", the paragraph "Stack" (1 paragraph) is not on the new course page, which is generated from course.json. Move what is still true into course.json (a "sources" group for a list of links, "prerequisites" for what to prepare), README.md or a lab page, or drop it.
- index.html line 135: "Setup", the paragraph "Choosing models" (1 paragraph, 5 links) is not on the new course page, which is generated from course.json. Move what is still true into course.json (a "sources" group for a list of links, "prerequisites" for what to prepare), README.md or a lab page, or drop it.

## Good to know

- 15 checkpoint slides written as <section class="slide quiz"> (slides/day1.html line 422, slides/day1.html line 704, slides/day1.html line 1000, slides/day1.html line 1211, slides/day2.html line 222, slides/day2.html line 380, slides/day2.html line 526, slides/day2.html line 722, slides/day3.html line 262, slides/day3.html line 399, slides/day3.html line 517, slides/day3.html line 653, slides/day4.html line 177, slides/day4.html line 294, slides/day4.html line 429) are kept as written. Each is one activity, in the build and in the browser: its lead paragraph (p.lead), or else its heading, is the question; the room answers with the number keys or a click. "academy check" asks for the misconception behind each wrong option (quiz/why).

## Break slides dropped

- None.

## Markup that does not parse strictly

The build parses slide sources strictly. Fix each place below in the slide source (close the element, quote the attribute, write `&lt;` for a "<" in text).

- None: every deck parses strictly.
