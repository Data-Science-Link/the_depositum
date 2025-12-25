# Catechism Extraction Analysis & Improvement Log

## Goal
Achieve 95% accuracy in matching header levels between the extracted Markdown and the official table of contents (CSV).

## Reference Document
- **Source**: `cleaned_table_of_contents.csv`
- **Structure**:
  - First Level → `#` (Level 1 headers)
  - Second Level → `##` (Level 2 headers)
  - Third Level → `###` or `####` (Level 3 headers)

## Analysis Process

### Iteration Workflow
1. **Extract**: Run `extract_catechism.py` on full PDF
2. **Compare**: Run `compare_to_toc.py` to analyze differences
3. **Record**: Document findings in this file
4. **Improve**: Make programmatic changes to extraction script
5. **Repeat**: Until 95% accuracy is achieved

---

## Iteration History

### Iteration 1 - Initial Baseline
**Date**: 2025-12-20
**Status**: Baseline measurement

**Results**:
- Total headers in CSV: 1,128
- Filtered TOC entries (excluding copyright/intro): 1,124
- Total Markdown headers: 1,185
- Matches (correct level): 22
- Mismatches (wrong level): 976
- Not found: 126
- **Accuracy: 1.96%** ❌

**Key Findings**:
1. **INTRODUCTORY** is Level 1 in TOC but extracted as Level 2 (`##`)
2. **Many Level 2 items** are being extracted as Level 4 (`####`) - these are italicized subsection headers
   - Examples: "The Necessity Of Religious Instruction", "Knowledge Of Christ", "Love Of God"
   - These should be Level 2 (`##`) or Level 3 (`###`), not Level 4
3. **Pattern**: Italicized headers are all being formatted as `####` regardless of their actual hierarchy level

**Root Cause Analysis**:
- The extraction script formats ALL italicized lines as `####` headers
- But italicized text can be at different hierarchy levels (Level 2 or Level 3)
- Need to distinguish between:
  - Level 2 italicized headers (subsections under INTRODUCTORY, PART sections)
  - Level 3 italicized headers (sub-subsections under ARTICLES)

**Changes Made**:
- None (baseline measurement)

---

## Current Status

**Last Updated**: 2025-12-20
**Current Accuracy**: 19.84%
**Target Accuracy**: 95%
**Gap**: 75.16% improvement needed
**Progress**: 18.88% improvement achieved (from 1.96%)

### Next Steps
1. Fix INTRODUCTORY to be Level 1 (`#`) instead of Level 2
2. Implement hierarchy-aware italic header formatting:
   - Italicized headers under INTRODUCTORY/PART sections → Level 2 (`##`)
   - Italicized headers under ARTICLES → Level 3 (`###`)
   - Only use Level 4 (`####`) for deeper subsections
3. Re-run extraction and comparison

---

### Iteration 2 - Hierarchy-Aware Italic Headers
**Date**: 2025-12-20
**Status**: ✅ Completed

### Iteration 3 - Improved Context Detection
**Date**: 2025-12-20
**Status**: ✅ Completed

**Changes Made**:
1. Enhanced context detection to recognize "THE SACRAMENTS", "THE DECALOGUE", and "PRAYER" as Level 2 sections
2. Improved hierarchy detection to handle merged headers (e.g., "THE SACRAMENTS Importance Of Instruction On The Sacraments")
3. Added logic to detect items directly under INTRODUCTORY vs. items under Level 2 sections

**Results**:
- Total headers in CSV: 1,128
- Filtered TOC entries: 1,124
- Total Markdown headers: 1,190
- Matches (correct level): 1,000
- Mismatches (wrong level): 12
- Not found: 112
- **Accuracy: 88.97%** ✅ (up from 19.84% - significant improvement!)

**Key Improvements**:
1. ✅ Items under "THE SACRAMENTS" and "THE DECALOGUE" are now correctly Level 3
2. ✅ "PRAYER" is now recognized as a Level 2 section
3. ⚠️ Some items directly under INTRODUCTORY are still Level 3 instead of Level 2
   - Examples: "Love Of God", "The Means Required for Religious Instruction", "Faith"
4. ⚠️ Some merged headers like "Importance Of Instruction On The Sacraments" are Level 2 but should be Level 3

**Remaining Issues**:
- 12 mismatches (mostly items directly under INTRODUCTORY being Level 3 instead of Level 2)
- 112 items not found (likely due to text extraction differences or merged headers)

**Changes Made**:
1. Made `_format_italicized_headers()` context-aware with `_get_section_context()`:
   - Tracks current section by looking backwards for structural headers
   - Assigns header levels based on context:
     - Under INTRODUCTORY or PART → `##` (Level 2)
     - Under ARTICLE → `###` (Level 3)
     - Default/unknown → `####` (Level 4)
2. Fixed INTRODUCTORY to be Level 1 (`#`) instead of Level 2

**Results**:
- Total headers in CSV: 1,128
- Filtered TOC entries: 1,124
- Total Markdown headers: 1,148
- Matches (correct level): 223
- Mismatches (wrong level): 769
- Not found: 132
- **Accuracy: 19.84%** ✅ (up from 1.96% - 10x improvement!)

**Header Distribution**:
- Level 2 (`##`): 913 headers
- Level 3 (`###`): 208 headers
- Level 4 (`####`): 2 headers

**Key Findings**:
1. ✅ INTRODUCTORY is now correctly Level 1
2. ⚠️ Many Level 3 items under ARTICLES are being detected as Level 2
   - Examples: "The Just", "The Word 'Sacrament'", "Definition of a Sacrament"
   - These are under ARTICLE sections but being formatted as Level 2
3. ⚠️ Some items under "THE SACRAMENTS" (Level 2 section) are Level 2, but should be Level 3
   - These are subsections under PART II, so they should be Level 3

**Root Cause**:
- Context detection looks for ARTICLE headers, but items under "THE SACRAMENTS" section (which is Level 2) are not being recognized as being under an ARTICLE
- Need to also check for "THE SACRAMENTS" and other Level 2 section markers

**Next Steps**:
1. Improve context detection to recognize "THE SACRAMENTS" and other major Level 2 sections
2. Items under Level 2 sections (like "THE SACRAMENTS") should be Level 3, not Level 2

## Notes
- Copyright and introduction sections are excluded from comparison
- Focus on structural headers (PART, ARTICLE, subsections)
- Italicized subsection headers should map to Level 3

