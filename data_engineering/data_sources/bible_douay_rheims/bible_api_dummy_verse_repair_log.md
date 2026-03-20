# Bible API Dummy Verse Repair Log

## Summary
The Douay-Rheims extractor uses `bible-api.com` (`Douay-Rheims 1899 American Edition`, translation id `dra`) as the primary structured source.

At runtime, `bible-api.com` sometimes returns **placeholder text** such as `dummy verses inserted by amos` and/or **verse-numbering gaps** inside individual chapters. When those payloads are written verbatim into Markdown, the resulting chapter text can contain:
- dummy placeholder verses, and/or
- missing verse numbers (e.g., verse `16` followed by verse `18`).

This repair log documents the issue, its measured occurrences in the current repository snapshot, the repair approach (full chapter replacement), and the QC plan.

## Baseline Occurrence (measured on existing `data_final` Markdown)
The following numbers come from scanning `data_final/bible_douay_rheims/Bible_Book_*.md` for:
- dummy placeholder text: `dummy verses inserted by amos`
- verse-numbering gaps: within a chapter, any gap where adjacent verse numbers differ by more than 1

- Markdown book files scanned: `73`
- Chapters parsed: `1321`
- Chapters containing at least one dummy placeholder line: `35`
- Total dummy placeholder lines: `102`
- Chapters with verse-numbering gaps: `25`
- Total missing verse numbers implied by gaps: `35`
- Overlap (dummy chapters that also have gaps): `14`
- Chapters replaced during repair (from JSON alternate source): `46 / 1321` (3.48%)

## Repair Approach (post-processing)
We add a post-processing step that repairs at the chapter level:

1. **Detect** damaged chapters in the extracted Markdown:
   - any chapter containing the dummy placeholder text, or
   - any chapter with verse-numbering gaps
2. **Repair** by **full chapter replacement**:
   - replace the entire Markdown `## Chapter N` block using the verse list from the alternate source:
     `xxruyle/Bible-DouayRheims` consolidated `EntireBible-DR.json`
3. **Track** every repaired chapter:
   - log book id/title + chapter number + detection reasons
4. **Validate** immediately after repair:
   - re-scan for remaining dummy placeholders

## Repair Implementation Notes
- The repair script replaces the entire chapter (not only dummy lines). This avoids verse alignment issues when the API payload is missing verse entries or has inconsistent numbering.
- The repair script is configured via `data_engineering/config/pipeline_config.yaml` and runs against `data_final/bible_douay_rheims/` by default.
- Each repair run appends a timestamped section under “Repair Runs” below.

## Repair Runs
<!-- REPAIR_RUNS_START -->

## Repair Run (QC mismatches): 2026-03-19 22:45:33

- Repaired chapters: 2/2

### Repaired Chapters

- `Bible_Book_02_Exodus.md` / *Exodus* / Chapter 28
- `Bible_Book_14_2_Chronicles.md` / *2 Chronicles* / Chapter 4

## Repair Run: 2026-03-19 22:34:58

- Repaired chapters: 42
- Failed chapters: 4

### Repaired Chapters

- `Bible_Book_01_Genesis.md`: `GEN` / *Genesis* / Chapter 49 — Contains dummy placeholder text; Verse numbering gaps detected (2 gap event(s))
- `Bible_Book_01_Genesis.md`: `GEN` / *Genesis* / Chapter 41 — Contains dummy placeholder text; Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_01_Genesis.md`: `GEN` / *Genesis* / Chapter 40 — Contains dummy placeholder text; Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_01_Genesis.md`: `GEN` / *Genesis* / Chapter 39 — Contains dummy placeholder text; Verse numbering gaps detected (2 gap event(s))
- `Bible_Book_01_Genesis.md`: `GEN` / *Genesis* / Chapter 38 — Contains dummy placeholder text; Verse numbering gaps detected (2 gap event(s))
- `Bible_Book_01_Genesis.md`: `GEN` / *Genesis* / Chapter 27 — Contains dummy placeholder text
- `Bible_Book_01_Genesis.md`: `GEN` / *Genesis* / Chapter 20 — Contains dummy placeholder text; Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_01_Genesis.md`: `GEN` / *Genesis* / Chapter 18 — Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_01_Genesis.md`: `GEN` / *Genesis* / Chapter 17 — Contains dummy placeholder text
- `Bible_Book_02_Exodus.md`: `EXO` / *Exodus* / Chapter 28 — Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_02_Exodus.md`: `EXO` / *Exodus* / Chapter 9 — Contains dummy placeholder text
- `Bible_Book_04_Numbers.md`: `NUM` / *Numbers* / Chapter 7 — Contains dummy placeholder text; Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_05_Deuteronomy.md`: `DEU` / *Deuteronomy* / Chapter 26 — Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_05_Deuteronomy.md`: `DEU` / *Deuteronomy* / Chapter 11 — Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_05_Deuteronomy.md`: `DEU` / *Deuteronomy* / Chapter 1 — Contains dummy placeholder text; Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_06_Joshua.md`: `JOS` / *Joshua* / Chapter 18 — Contains dummy placeholder text; Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_06_Joshua.md`: `JOS` / *Joshua* / Chapter 2 — Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_07_Judges.md`: `JDG` / *Judges* / Chapter 6 — Contains dummy placeholder text; Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_07_Judges.md`: `JDG` / *Judges* / Chapter 2 — Contains dummy placeholder text
- `Bible_Book_11_1_Kings.md`: `1KI` / *1 Kings* / Chapter 6 — Contains dummy placeholder text; Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_14_2_Chronicles.md`: `2CH` / *2 Chronicles* / Chapter 4 — Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_23_Psalm.md`: `PSA` / *Psalm* / Chapter 149 — Contains dummy placeholder text
- `Bible_Book_23_Psalm.md`: `PSA` / *Psalm* / Chapter 116 — Contains dummy placeholder text
- `Bible_Book_23_Psalm.md`: `PSA` / *Psalm* / Chapter 73 — Contains dummy placeholder text
- `Bible_Book_23_Psalm.md`: `PSA` / *Psalm* / Chapter 55 — Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_23_Psalm.md`: `PSA` / *Psalm* / Chapter 11 — Verse numbering gaps detected (7 gap event(s))
- `Bible_Book_29_Isaiah.md`: `ISA` / *Isaiah* / Chapter 25 — Contains dummy placeholder text
- `Bible_Book_29_Isaiah.md`: `ISA` / *Isaiah* / Chapter 22 — Contains dummy placeholder text
- `Bible_Book_29_Isaiah.md`: `ISA` / *Isaiah* / Chapter 5 — Contains dummy placeholder text
- `Bible_Book_30_Jeremiah.md`: `JER` / *Jeremiah* / Chapter 31 — Contains dummy placeholder text; Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_30_Jeremiah.md`: `JER` / *Jeremiah* / Chapter 21 — Contains dummy placeholder text
- `Bible_Book_33_Ezekiel.md`: `EZK` / *Ezekiel* / Chapter 43 — Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_33_Ezekiel.md`: `EZK` / *Ezekiel* / Chapter 23 — Contains dummy placeholder text
- `Bible_Book_40_Micah.md`: `MIC` / *Micah* / Chapter 6 — Contains dummy placeholder text; Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_47_Matthew.md`: `MAT` / *Matthew* / Chapter 12 — Contains dummy placeholder text
- `Bible_Book_50_John.md`: `JHN` / *John* / Chapter 15 — Contains dummy placeholder text
- `Bible_Book_50_John.md`: `JHN` / *John* / Chapter 4 — Contains dummy placeholder text
- `Bible_Book_52_Romans.md`: `ROM` / *Romans* / Chapter 11 — Contains dummy placeholder text
- `Bible_Book_52_Romans.md`: `ROM` / *Romans* / Chapter 9 — Contains dummy placeholder text
- `Bible_Book_59_1_Thessalonians.md`: `1TH` / *1 Thessalonians* / Chapter 5 — Contains dummy placeholder text
- `Bible_Book_59_1_Thessalonians.md`: `1TH` / *1 Thessalonians* / Chapter 2 — Contains dummy placeholder text
- `Bible_Book_65_Hebrews.md`: `HEB` / *Hebrews* / Chapter 11 — Contains dummy placeholder text

### Repair Failures

- `Bible_Book_10_2_Samuel.md`: `2SA` / *2 Samuel* / Chapter 5 — Contains dummy placeholder text; Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_13_1_Chronicles.md`: `1CH` / *1 Chronicles* / Chapter 21 — Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_14_2_Chronicles.md`: `2CH` / *2 Chronicles* / Chapter 30 — Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_22_Job.md`: `JOB` / *Job* / Chapter 32 — Contains dummy placeholder text

### QC Status

- Pending: run a chapter-by-chapter comparison against an internet Douay-Rheims source.
- When completed, update the shared QC section in this document.

## Repair Run: 2026-03-19 22:36:04

- Repaired chapters: 0
- Failed chapters: 4

### Repaired Chapters

- None

### Repair Failures

- `Bible_Book_10_2_Samuel.md`: `2SA` / *2 Samuel* / Chapter 5 — Contains dummy placeholder text; Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_13_1_Chronicles.md`: `1CH` / *1 Chronicles* / Chapter 21 — Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_14_2_Chronicles.md`: `2CH` / *2 Chronicles* / Chapter 30 — Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_22_Job.md`: `JOB` / *Job* / Chapter 32 — Contains dummy placeholder text

### QC Status

- Pending: run a chapter-by-chapter comparison against an internet Douay-Rheims source.
- When completed, update the shared QC section in this document.

## Repair Run: 2026-03-19 22:40:34

- Repaired chapters: 4
- Failed chapters: 0

### Repaired Chapters

- `Bible_Book_10_2_Samuel.md`: `2SA` / *2 Samuel* / Chapter 5 — Contains dummy placeholder text; Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_13_1_Chronicles.md`: `1CH` / *1 Chronicles* / Chapter 21 — Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_14_2_Chronicles.md`: `2CH` / *2 Chronicles* / Chapter 30 — Verse numbering gaps detected (1 gap event(s))
- `Bible_Book_22_Job.md`: `JOB` / *Job* / Chapter 32 — Contains dummy placeholder text

### QC Status

- Pending: run a chapter-by-chapter comparison against an internet Douay-Rheims source.
- When completed, update the shared QC section in this document.

## Repair Run: 2026-03-19 23:01:35

- Repaired chapters: 0
- Failed chapters: 0

### Repaired Chapters

- None

### QC Status

- Pending: run a chapter-by-chapter comparison against an internet Douay-Rheims source.
- When completed, update the shared QC section in this document.

<!-- QC_SECTION_START -->

# Douay-Rheims Dummy Verse Repair - QC Results

- Repaired chapters checked: 46
- Exact matches to EntireBible-DR: 46/46

## Summary Table

| File | Book | Chapter | Dummy present? | Gap events | Verse count (current) | Verse count (expected) | Exact match |
|---|---|---:|---|---:|---:|---:|---|
| `Bible_Book_01_Genesis.md` | Genesis | 17 | ❌ | 0 | 27 | 27 | ✅ |
| `Bible_Book_01_Genesis.md` | Genesis | 18 | ❌ | 0 | 33 | 33 | ✅ |
| `Bible_Book_01_Genesis.md` | Genesis | 20 | ❌ | 0 | 18 | 18 | ✅ |
| `Bible_Book_01_Genesis.md` | Genesis | 27 | ❌ | 0 | 46 | 46 | ✅ |
| `Bible_Book_01_Genesis.md` | Genesis | 38 | ❌ | 0 | 30 | 30 | ✅ |
| `Bible_Book_01_Genesis.md` | Genesis | 39 | ❌ | 0 | 23 | 23 | ✅ |
| `Bible_Book_01_Genesis.md` | Genesis | 40 | ❌ | 0 | 22 | 22 | ✅ |
| `Bible_Book_01_Genesis.md` | Genesis | 41 | ❌ | 0 | 57 | 57 | ✅ |
| `Bible_Book_01_Genesis.md` | Genesis | 49 | ❌ | 0 | 32 | 32 | ✅ |
| `Bible_Book_02_Exodus.md` | Exodus | 9 | ❌ | 0 | 35 | 35 | ✅ |
| `Bible_Book_02_Exodus.md` | Exodus | 28 | ❌ | 0 | 43 | 43 | ✅ |
| `Bible_Book_04_Numbers.md` | Numbers | 7 | ❌ | 0 | 89 | 89 | ✅ |
| `Bible_Book_05_Deuteronomy.md` | Deuteronomy | 1 | ❌ | 0 | 46 | 46 | ✅ |
| `Bible_Book_05_Deuteronomy.md` | Deuteronomy | 11 | ❌ | 0 | 32 | 32 | ✅ |
| `Bible_Book_05_Deuteronomy.md` | Deuteronomy | 26 | ❌ | 0 | 19 | 19 | ✅ |
| `Bible_Book_06_Joshua.md` | Joshua | 2 | ❌ | 0 | 24 | 24 | ✅ |
| `Bible_Book_06_Joshua.md` | Joshua | 18 | ❌ | 0 | 9 | 9 | ✅ |
| `Bible_Book_07_Judges.md` | Judges | 2 | ❌ | 0 | 23 | 23 | ✅ |
| `Bible_Book_07_Judges.md` | Judges | 6 | ❌ | 0 | 25 | 25 | ✅ |
| `Bible_Book_10_2_Samuel.md` | 2 Samuel | 5 | ❌ | 0 | 25 | 25 | ✅ |
| `Bible_Book_11_1_Kings.md` | 1 Kings | 6 | ❌ | 0 | 21 | 21 | ✅ |
| `Bible_Book_13_1_Chronicles.md` | 1 Chronicles | 21 | ❌ | 0 | 30 | 30 | ✅ |
| `Bible_Book_14_2_Chronicles.md` | 2 Chronicles | 4 | ❌ | 0 | 22 | 22 | ✅ |
| `Bible_Book_14_2_Chronicles.md` | 2 Chronicles | 30 | ❌ | 0 | 27 | 27 | ✅ |
| `Bible_Book_22_Job.md` | Job | 32 | ❌ | 0 | 22 | 22 | ✅ |
| `Bible_Book_23_Psalm.md` | Psalm | 11 | ❌ | 0 | 9 | 9 | ✅ |
| `Bible_Book_23_Psalm.md` | Psalm | 55 | ❌ | 0 | 13 | 13 | ✅ |
| `Bible_Book_23_Psalm.md` | Psalm | 73 | ❌ | 0 | 23 | 23 | ✅ |
| `Bible_Book_23_Psalm.md` | Psalm | 116 | ❌ | 0 | 2 | 2 | ✅ |
| `Bible_Book_23_Psalm.md` | Psalm | 149 | ❌ | 0 | 9 | 9 | ✅ |
| `Bible_Book_29_Isaiah.md` | Isaiah | 5 | ❌ | 0 | 29 | 29 | ✅ |
| `Bible_Book_29_Isaiah.md` | Isaiah | 22 | ❌ | 0 | 25 | 25 | ✅ |
| `Bible_Book_29_Isaiah.md` | Isaiah | 25 | ❌ | 0 | 12 | 12 | ✅ |
| `Bible_Book_30_Jeremiah.md` | Jeremiah | 21 | ❌ | 0 | 14 | 14 | ✅ |
| `Bible_Book_30_Jeremiah.md` | Jeremiah | 31 | ❌ | 0 | 40 | 40 | ✅ |
| `Bible_Book_33_Ezekiel.md` | Ezekiel | 23 | ❌ | 0 | 48 | 48 | ✅ |
| `Bible_Book_33_Ezekiel.md` | Ezekiel | 43 | ❌ | 0 | 23 | 23 | ✅ |
| `Bible_Book_40_Micah.md` | Micah | 6 | ❌ | 0 | 20 | 20 | ✅ |
| `Bible_Book_47_Matthew.md` | Matthew | 12 | ❌ | 0 | 50 | 50 | ✅ |
| `Bible_Book_50_John.md` | John | 4 | ❌ | 0 | 54 | 54 | ✅ |
| `Bible_Book_50_John.md` | John | 15 | ❌ | 0 | 27 | 27 | ✅ |
| `Bible_Book_52_Romans.md` | Romans | 9 | ❌ | 0 | 33 | 33 | ✅ |
| `Bible_Book_52_Romans.md` | Romans | 11 | ❌ | 0 | 36 | 36 | ✅ |
| `Bible_Book_59_1_Thessalonians.md` | 1 Thessalonians | 2 | ❌ | 0 | 20 | 20 | ✅ |
| `Bible_Book_59_1_Thessalonians.md` | 1 Thessalonians | 5 | ❌ | 0 | 28 | 28 | ✅ |
| `Bible_Book_65_Hebrews.md` | Hebrews | 11 | ❌ | 0 | 40 | 40 | ✅ |

## Sample Verse Comparisons

### Sample: `Bible_Book_01_Genesis.md` Chapter 17 Verse 26
- Current matches expected: ✅

Current:
> The self-same day was Abraham circumcised and Ismael his son.

Expected (EntireBible-DR):
> The self-same day was Abraham circumcised and Ismael his son.
### Sample: `Bible_Book_01_Genesis.md` Chapter 20 Verse 15
- Current matches expected: ✅

Current:
> And said: The land is before you, dwell wheresoever it shall please thee.

Expected (EntireBible-DR):
> And said: The land is before you, dwell wheresoever it shall please thee.
### Sample: `Bible_Book_22_Job.md` Chapter 32 Verse 19
- Current matches expected: ✅

Current:
> Behold, my belly is as new wine which wanteth vent, which bursteth the new vessels.

Expected (EntireBible-DR):
> Behold, my belly is as new wine which wanteth vent, which bursteth the new vessels.
### Sample: `Bible_Book_10_2_Samuel.md` Chapter 5 Verse 11
- Current matches expected: ✅

Current:
> *And Hiram, the king of Tyre, sent messengers to David, and cedar trees, and carpenters, and masons for walls: and they built a house for David.

Expected (EntireBible-DR):
> *And Hiram, the king of Tyre, sent messengers to David, and cedar trees, and carpenters, and masons for walls: and they built a house for David.
### Sample: `Bible_Book_23_Psalm.md` Chapter 11 Verse 6
- Current matches expected: ✅

Current:
> By reason of the misery of the needy, and the groans of the poor, now will I arise, saith the Lord. I will set him in safety: I will deal confidently in his regard.

Expected (EntireBible-DR):
> By reason of the misery of the needy, and the groans of the poor, now will I arise, saith the Lord. I will set him in safety: I will deal confidently in his regard.


## QC Plan (to fill in after repair)
After the repair step completes, we should do a manual or automated QC comparison for at least a representative subset of repaired chapters:
- Compare the repaired chapter text/verse numbering against an internet Douay-Rheims version (e.g., a DRB site or another public source).
- Focus on chapters previously flagged as having:
  - dummy placeholder verses, and
  - verse-numbering gaps

When you complete QC, append your findings under this QC Plan section (or add a new subsection per source).

## Third-party Sanity Checks (DRBO)

Spot checks were taken against DRBO chapter/verse pages to sanity-check that the repaired Markdown matches a third-party Douay-Rheims rendering.

### Results (10 verses)

| Reference | Repo (current) | DRBO | Result |
|---|---|---|---|
| Genesis 17:26 | `The self-same day was Abraham circumcised and Ismael his son.` | `The selfsame day was Abraham circumcised and Ismael his son` | ⚠️ minor hyphenation |
| Genesis 20:15 | `And said: The land is before you, dwell wheresoever it shall please thee.` | `And said: The land is before you, dwell wheresoever it shall please thee` | ✅ match (ignoring trailing punctuation) |
| Job 32:19 | `Behold, my belly is as new wine which wanteth vent, which bursteth the new vessels.` | `Behold, my belly is as new wine which wanteth vent, which bursteth the new vessels` | ✅ match (ignoring trailing punctuation) |
| 2 Samuel 5:11 | `*And Hiram, the king of Tyre, sent messengers to David, and cedar trees, and carpenters, and masons for walls: and they built a house for David.` | `And Hiram the king of Tyre sent messengers to David, and cedar trees, and carpenters, and masons for walls: and they built a house for David` | ⚠️ punctuation/italics formatting differences |
| Psalm 11:6 | `By reason of the misery of the needy, and the groans of the poor, now will I arise, saith the Lord. I will set him in safety: I will deal confidently in his regard.` | `By reason of the misery of the needy, and the groans of the poor, now will I arise, saith the Lord. I will set him in safety; I will deal confidently in his regard` | ✅ match (semicolon/comma + trailing punctuation differences) |
| Exodus 28:1 | `Take unto thee also Aaron thy brother with his sons, from among the children of Israel, that they may minister to me in the priest's office: Aaron, Nadab, and Abiu, Eleazar, and Ithamar.` | `Take unto thee also Aaron thy brother with his sons, from among the children of Israel, that they may minister to me in the priest's office: Aaron, Nadab, and Abiu, Eleazar, and Ithamar` | ✅ match (ignoring trailing punctuation) |
| Exodus 9:23 | `*And Moses stretched forth his rod towards heaven, and the Lord sent thunder and hail, and lightnings running along the ground: and the Lord rained hail upon the land of Egypt.` | `And Moses stretched forth his rod towards heaven, and the Lord sent thunder and hail, and lightning running along the ground: and the Lord rained hail upon the land of Egypt` | ❌ wording difference (`lightnings` vs `lightning`) + italics marker differences |
| Genesis 41:1 | `After two years Pharao had a dream.* He thought he stood by the river,` | `After two years Pharao had a dream. He thought he stood by the river` | ⚠️ italics/asterisk + trailing punctuation differences |
| Psalm 55:1 | `Unto the end, for a people that is removed at a distance from the sanctuary: for David, for an inscription of a title, (or pillar) when the Philistines held him in Geth.` | `Unto the end, for a people that is removed at a distance from the sanctuary for David, for an inscription of a title (or pillar) when the Philistines held him in Geth` | ⚠️ punctuation differences (`sanctuary:` vs `sanctuary`) + commas |
| Psalm 116:2 | `For his mercy is confirmed upon us: *and the truth of the Lord remaineth for ever.` | `For his mercy is confirmed upon us: and the truth of the Lord remaineth for ever` | ⚠️ italics/asterisk formatting differences |

### Notes on confidence

The repair guarantees two things:
- Exact verse-text + verse numbering matches the alternate source we used for repaired chapters: `EntireBible-DR.json` (this was checked by QC: `46/46` exact matches).
- Verse numbering gaps were re-scanned across the whole corpus and are now `0`.

But “true Douay-Rheims” includes typographic/wording variants across editions/sites. DRBO spot checks show differences are limited to formatting/punctuation in most cases, with one small wording variant at `Exodus 9:23`.

