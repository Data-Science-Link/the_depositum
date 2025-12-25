#!/usr/bin/env python3
"""
Compare extracted Markdown headers to the official table of contents.

This script:
1. Loads the cleaned table of contents CSV
2. Extracts headers from the generated Markdown file
3. Compares header levels and matches
4. Generates a detailed analysis report
"""

import re
import csv
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
TOC_CSV = Path(__file__).parent / "cleaned_table_of_contents.csv"
MARKDOWN_FILE = PROJECT_ROOT / "data_final" / "catholic_catechism_trent" / "Catholic_Catechism_Trent_McHugh_Callan.md"
ANALYSIS_FILE = Path(__file__).parent / "EXTRACTION_ANALYSIS.md"


def clean_toc_text(text: str) -> str:
    """Clean TOC text by removing page numbers and formatting."""
    if not text:
        return ""
    # Remove leading numbers (like "11Proof", "21That")
    text = re.sub(r'^\d+', '', text)
    # Remove page number references (dots and numbers at end)
    text = re.sub(r'\.{3,}\s*\d+\s*$', '', text)
    # Remove trailing dots
    text = re.sub(r'\.+$', '', text)
    # Normalize quotes
    text = text.replace('""', '"').replace('"', '"')
    # Strip whitespace
    return text.strip()


def load_toc() -> List[Dict[str, str]]:
    """Load and parse the table of contents CSV."""
    toc_entries = []

    with open(TOC_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            first = clean_toc_text(row.get('First Level', ''))
            second = clean_toc_text(row.get('Second Level', ''))
            third = clean_toc_text(row.get('Third Level', ''))

            # Determine level and text
            if first:
                toc_entries.append({
                    'level': 1,
                    'text': first,
                    'full_text': first
                })
            if second:
                toc_entries.append({
                    'level': 2,
                    'text': second,
                    'full_text': f"{first} > {second}" if first else second
                })
            if third:
                toc_entries.append({
                    'level': 3,
                    'text': third,
                    'full_text': f"{first} > {second} > {third}" if first and second else third
                })

    return toc_entries


def extract_markdown_headers(markdown_path: Path) -> List[Dict[str, any]]:
    """Extract all headers from the Markdown file."""
    headers = []

    with open(markdown_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Skip frontmatter
    in_frontmatter = False
    for i, line in enumerate(lines):
        if line.strip() == '---':
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue

        # Match markdown headers
        match = re.match(r'^(#{1,4})\s+(.+)$', line.strip())
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            # Remove page numbers from headers
            text = re.sub(r'\d{1,3}\s*$', '', text).strip()

            headers.append({
                'level': level,
                'text': text,
                'line_number': i + 1
            })

        # Also check for plain text lines that might be headers (standalone lines, title case)
        # This handles cases where headers weren't properly formatted
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and not stripped.startswith('-') and not stripped.startswith('*'):
            # Check if it's a command header (starts with "THE ... COMMANDMENT" or "THIRD COMMANDMENT")
            # These can span multiple lines, so we need to collect the full text
            is_command_header = re.match(r'^(THE\s+)?(FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|NINTH AND TENTH)\s+COMMANDMENT', stripped, re.IGNORECASE)

            if is_command_header:
                # Collect the full command header text (may span multiple lines)
                command_text = [stripped]
                j = i + 1
                # Continue collecting lines until we hit a blank line or page number
                while j < len(lines):
                    next_line = lines[j].strip()
                    if not next_line:
                        break
                    # Check if it ends with page number (dots followed by number)
                    if re.search(r'\.{3,}\s*\d+\s*$', next_line):
                        # Remove page number and add to command text
                        next_line = re.sub(r'\.{3,}\s*\d+\s*$', '', next_line).strip()
                        command_text.append(next_line)
                        break
                    command_text.append(next_line)
                    j += 1
                    # Limit to reasonable length (command headers shouldn't be more than 10 lines)
                    if j - i > 10:
                        break

                full_command_text = ' '.join(command_text)
                # Command headers are Level 2
                headers.append({
                    'level': 2,
                    'text': full_command_text,
                    'line_number': i + 1,
                    'is_plain_text': True
                })
                continue

            # Check if it looks like a regular header: title case, short, followed by blank line
            is_likely_header = (
                (i + 1 < len(lines) and not lines[i + 1].strip()) and  # Followed by blank line
                stripped[0].isupper() and  # Starts with capital
                not stripped.endswith('.') and not stripped.endswith(',') and  # Not ending with punctuation
                not any(c.isdigit() for c in stripped[-5:])  # Not ending with page number
            )

            if is_likely_header:
                # Check if it's likely a header by checking surrounding context
                # It's a header if:
                # 1. Previous line is blank (standalone header)
                # 2. Previous line is a header (subheader)
                # 3. Previous line is content but this looks like a section header
                prev_line_blank = i > 0 and not lines[i - 1].strip()
                prev_line_header = i > 0 and lines[i - 1].strip().startswith('#')
                prev_line_content = i > 0 and lines[i - 1].strip() and not lines[i - 1].strip().startswith('#')

                if prev_line_blank or prev_line_header or (prev_line_content and len(stripped) < 100):
                    # Other headers are Level 3 (most common for subsections)
                    headers.append({
                        'level': 3,
                        'text': stripped,
                        'line_number': i + 1,
                        'is_plain_text': True
                    })

    return headers


def normalize_text(text: str) -> str:
    """Normalize text for comparison (case-insensitive, remove extra spaces)."""
    if not text:
        return ""
    # Remove quotes for comparison
    text = text.replace('"', '').replace("'", '').replace('"', '').replace("'", '')
    # Remove colons and other punctuation that might differ
    text = text.replace(':', '').replace(';', '')
    # Normalize whitespace
    text = ' '.join(text.split())
    # Case insensitive
    return text.lower().strip()


def extract_significant_words(text: str) -> set:
    """Extract significant words (skip common words, short words)."""
    # Common words to skip
    skip_words = {'the', 'of', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by'}
    words = text.split()
    # Filter: keep words of 3+ chars that aren't common words
    significant = {w for w in words if len(w) >= 3 and w not in skip_words}
    return significant


def find_best_match(toc_text: str, markdown_headers: List[Dict]) -> Optional[Tuple[Dict, float]]:
    """Find the best matching markdown header for a TOC entry."""
    normalized_toc = normalize_text(toc_text)
    if not normalized_toc:
        return None

    # Extract significant words from TOC text
    toc_words = extract_significant_words(normalized_toc)
    if not toc_words:
        # If no significant words, use all words
        toc_words = set(normalized_toc.split())

    best_match = None
    best_score = 0.0

    for md_header in markdown_headers:
        normalized_md = normalize_text(md_header['text'])
        if not normalized_md:
            continue

        # Exact match
        if normalized_toc == normalized_md:
            return (md_header, 1.0)

        # Check if TOC text is contained in markdown header (handles merged headers)
        if normalized_toc in normalized_md:
            # Calculate score based on how much of TOC is in MD
            score = len(normalized_toc) / len(normalized_md) if normalized_md else 0.0
            if score > best_score and score >= 0.3:  # At least 30% of MD is TOC
                best_match = md_header
                best_score = score
            continue

        # Check if markdown header contains TOC text (handles cases like "Zeal" in "Zeal In The Service Of God")
        # Also check if TOC text is a complete word/phrase at the start of MD
        if normalized_md.startswith(normalized_toc + ' ') or normalized_md.endswith(' ' + normalized_toc):
            score = len(normalized_toc) / len(normalized_md) if normalized_md else 0.0
            if score > best_score and score >= 0.3:
                best_match = md_header
                best_score = score
            continue

        # Check if TOC text matches the beginning of MD (word boundary match)
        # This handles "Zeal" matching "Zeal In The Service Of God"
        if normalized_md.startswith(normalized_toc):
            # Make sure it's a word boundary (followed by space or end of string)
            if len(normalized_md) == len(normalized_toc) or normalized_md[len(normalized_toc)] == ' ':
                score = len(normalized_toc) / len(normalized_md) if normalized_md else 0.0
                if score > best_score and score >= 0.3:
                    best_match = md_header
                    best_score = score
                continue

        # Word-based matching: check if significant words from TOC appear in MD
        md_words = extract_significant_words(normalized_md)
        if not md_words:
            md_words = set(normalized_md.split())

        # Count matching significant words
        matching_words = toc_words.intersection(md_words)
        if matching_words:
            # Calculate score based on word overlap
            # If most/all TOC words are in MD, it's a good match (even if MD has more words)
            word_score = len(matching_words) / len(toc_words) if toc_words else 0.0
            # Also consider how much of MD is covered by TOC words
            coverage_score = len(matching_words) / len(md_words) if md_words else 0.0
            # Combined score (weighted towards TOC word coverage)
            score = (word_score * 0.8) + (coverage_score * 0.2)

            if score > best_score and score >= 0.6:  # At least 60% of TOC words must match
                best_match = md_header
                best_score = score

        # Fallback: substring match (TOC text in MD or vice versa)
        if normalized_toc in normalized_md or normalized_md in normalized_toc:
            shorter = min(len(normalized_toc), len(normalized_md))
            longer = max(len(normalized_toc), len(normalized_md))
            score = shorter / longer if longer > 0 else 0.0

            if score > best_score and score >= 0.6:  # At least 60% match
                best_match = md_header
                best_score = score

    return (best_match, best_score) if best_match else None


def compare_headers() -> Dict:
    """Compare TOC headers to extracted Markdown headers."""
    print("Loading table of contents...")
    toc_entries = load_toc()
    print(f"Loaded {len(toc_entries)} TOC entries")

    print("Extracting Markdown headers...")
    md_headers = extract_markdown_headers(MARKDOWN_FILE)
    print(f"Found {len(md_headers)} Markdown headers")

    # Filter out copyright/intro sections (first ~50 lines typically)
    # Skip entries that are clearly copyright/intro
    skip_patterns = [
        'copyright', 'catholic primer', 'adobe', 'acrobat',
        'preface', 'origin of the roman', 'authority and excellence',
        'catechism of the council of trent for parish priests'
    ]

    filtered_toc = []
    for entry in toc_entries:
        text_lower = normalize_text(entry['text'])
        if not any(pattern in text_lower for pattern in skip_patterns):
            filtered_toc.append(entry)

    print(f"After filtering copyright/intro: {len(filtered_toc)} TOC entries")

    # Compare
    matches = []
    mismatches = []
    not_found = []

    for toc_entry in filtered_toc:
        match_result = find_best_match(toc_entry['text'], md_headers)

        if match_result:
            md_header, score = match_result
            if md_header['level'] == toc_entry['level']:
                matches.append({
                    'toc': toc_entry,
                    'md': md_header,
                    'score': score
                })
            else:
                mismatches.append({
                    'toc': toc_entry,
                    'md': md_header,
                    'expected_level': toc_entry['level'],
                    'actual_level': md_header['level'],
                    'score': score
                })
        else:
            not_found.append(toc_entry)

    total_compared = len(filtered_toc)
    accuracy = (len(matches) / total_compared * 100) if total_compared > 0 else 0

    return {
        'total_toc': len(toc_entries),
        'filtered_toc': len(filtered_toc),
        'total_md': len(md_headers),
        'matches': matches,
        'mismatches': mismatches,
        'not_found': not_found,
        'accuracy': accuracy,
        'total_compared': total_compared
    }


def generate_report(results: Dict) -> str:
    """Generate a detailed analysis report."""
    report = []
    report.append("# Header Comparison Analysis\n")
    report.append(f"**Date**: {Path(__file__).stat().st_mtime}\n")
    report.append(f"**Accuracy**: {results['accuracy']:.2f}%\n")
    report.append(f"**Target**: 95%\n\n")

    report.append("## Summary\n")
    report.append(f"- Total TOC entries: {results['total_toc']}\n")
    report.append(f"- Filtered TOC entries (excluding copyright/intro): {results['filtered_toc']}\n")
    report.append(f"- Total Markdown headers: {results['total_md']}\n")
    report.append(f"- Matches (correct level): {len(results['matches'])}\n")
    report.append(f"- Mismatches (wrong level): {len(results['mismatches'])}\n")
    report.append(f"- Not found: {len(results['not_found'])}\n\n")

    if results['mismatches']:
        report.append("## Level Mismatches\n")
        report.append("| TOC Text | Expected Level | Actual Level | MD Text |\n")
        report.append("|----------|---------------|--------------|----------|\n")

        for mm in results['mismatches'][:50]:  # Show first 50
            toc_text = mm['toc']['text'][:60]
            md_text = mm['md']['text'][:60]
            report.append(f"| {toc_text} | {mm['expected_level']} | {mm['actual_level']} | {md_text} |\n")

        if len(results['mismatches']) > 50:
            report.append(f"\n*... and {len(results['mismatches']) - 50} more mismatches*\n")

    if results['not_found']:
        report.append("\n## Not Found in Markdown\n")
        report.append("| Level | TOC Text |\n")
        report.append("|-------|----------|\n")

        for nf in results['not_found'][:50]:  # Show first 50
            report.append(f"| {nf['level']} | {nf['text'][:80]} |\n")

        if len(results['not_found']) > 50:
            report.append(f"\n*... and {len(results['not_found']) - 50} more not found*\n")

    # Level distribution analysis
    report.append("\n## Level Distribution\n")
    report.append("### TOC Levels\n")
    toc_levels = defaultdict(int)
    for entry in results.get('filtered_entries', []):
        toc_levels[entry['level']] += 1

    md_levels = defaultdict(int)
    for header in results.get('md_headers', []):
        md_levels[header['level']] += 1

    report.append("| Level | Count |\n")
    report.append("|-------|-------|\n")
    for level in sorted(toc_levels.keys()):
        report.append(f"| {level} | {toc_levels[level]} |\n")

    report.append("\n### Markdown Levels\n")
    report.append("| Level | Count |\n")
    report.append("|-------|-------|\n")
    for level in sorted(md_levels.keys()):
        report.append(f"| {level} | {md_levels[level]} |\n")

    return ''.join(report)


def main():
    """Main comparison function."""
    print("=" * 80)
    print("Catechism Header Comparison Analysis")
    print("=" * 80)
    print()

    results = compare_headers()

    print(f"\nResults:")
    print(f"  Accuracy: {results['accuracy']:.2f}%")
    print(f"  Matches: {len(results['matches'])}")
    print(f"  Mismatches: {len(results['mismatches'])}")
    print(f"  Not found: {len(results['not_found'])}")

    # Generate detailed report
    report = generate_report(results)

    # Save report
    report_file = Path(__file__).parent / "comparison_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nDetailed report saved to: {report_file}")

    # Also print summary of mismatches
    if results['mismatches']:
        print("\nTop 10 Level Mismatches:")
        for i, mm in enumerate(results['mismatches'][:10], 1):
            print(f"  {i}. Expected Level {mm['expected_level']}, Got Level {mm['actual_level']}")
            print(f"     TOC: {mm['toc']['text'][:70]}")
            print(f"     MD:  {mm['md']['text'][:70]}")
            print()


if __name__ == "__main__":
    main()

