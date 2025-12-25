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

    return headers


def normalize_text(text: str) -> str:
    """Normalize text for comparison (case-insensitive, remove extra spaces)."""
    # Remove quotes for comparison
    text = text.replace('"', '').replace("'", '')
    # Normalize whitespace
    text = ' '.join(text.split())
    # Case insensitive
    return text.lower()


def find_best_match(toc_text: str, markdown_headers: List[Dict]) -> Optional[Tuple[Dict, float]]:
    """Find the best matching markdown header for a TOC entry."""
    normalized_toc = normalize_text(toc_text)
    best_match = None
    best_score = 0.0

    for md_header in markdown_headers:
        normalized_md = normalize_text(md_header['text'])

        # Exact match
        if normalized_toc == normalized_md:
            return (md_header, 1.0)

        # Substring match (TOC text in MD or vice versa)
        if normalized_toc in normalized_md or normalized_md in normalized_toc:
            # Calculate similarity score
            shorter = min(len(normalized_toc), len(normalized_md))
            longer = max(len(normalized_toc), len(normalized_md))
            score = shorter / longer if longer > 0 else 0.0

            if score > best_score and score > 0.7:  # At least 70% match
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

