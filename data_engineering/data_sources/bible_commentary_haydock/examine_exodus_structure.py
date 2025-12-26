#!/usr/bin/env python3
"""Examine the EPUB structure around Exodus to find the introduction"""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from pathlib import Path

epub_path = Path(__file__).parent / 'Haydock Catholic Bible Comment - Haydock, George Leo_3948.epub'
book = epub.read_epub(str(epub_path))

# Search for Exodus-related content
exodus_keywords = [
    'EXODUS',
    'The second Book of Moses',
    'called Exodus',
    'signifies going out',
    'Veelle Shemoth'
]

print("=" * 80)
print("EXAMINING EXODUS STRUCTURE IN EPUB")
print("=" * 80)

found_items = []
item_count = 0

for item in book.get_items():
    if item.get_type() != ebooklib.ITEM_DOCUMENT:
        continue

    item_count += 1
    html_content = item.get_content()
    soup = BeautifulSoup(html_content, 'html.parser')
    all_text = soup.get_text()

    # Check if this item contains Exodus content
    for keyword in exodus_keywords:
        if keyword.lower() in all_text.lower():
            found_items.append((item_count, keyword, item, soup))
            break

print(f"\nFound {len(found_items)} items containing Exodus keywords\n")

# Examine each found item in detail
for idx, (item_num, keyword, item, soup) in enumerate(found_items):
    print("=" * 80)
    print(f"ITEM {item_num} (matched keyword: '{keyword}')")
    print("=" * 80)

    # Get all resourcetext divs
    all_divs = soup.find_all('div', class_='resourcetext')
    print(f"Total resourcetext divs: {len(all_divs)}\n")

    # Find divs with Exodus content
    for div_idx, div in enumerate(all_divs):
        div_text = div.get_text()
        has_exodus = any(kw.lower() in div_text.lower() for kw in exodus_keywords)

        if has_exodus:
            print(f"\n{'='*80}")
            print(f"DIV {div_idx} (contains Exodus content)")
            print(f"{'='*80}\n")
            paragraphs = div.find_all('p')
            print(f"Total paragraphs in this div: {len(paragraphs)}\n")

            # Show all paragraphs in this div with their classes
            for p_idx, p in enumerate(paragraphs):
                p_class = p.get('class', [])
                p_class_str = ' '.join(p_class) if p_class else 'no-class'
                text = p.get_text().strip()

                # Identify paragraph types
                markers = []
                if 'lang-en13' in p_class_str or 'lang-en14' in p_class_str:
                    markers.append("BOOK_NAME")
                if 'lang-en15' in p_class_str:
                    markers.append("INTRO_HEADER")
                if 'lang-en17' in p_class_str:
                    markers.append("CHAPTER_HEADER")
                if 'lang-en16' in p_class_str:
                    markers.append("VERSE_COMMENTARY")
                if 'lang-en7' in p_class_str:
                    markers.append("VERSE_OR_INTRO")
                if 'The second Book of Moses' in text or 'called Exodus' in text:
                    markers.append("INTRO_TEXT")
                if 'Ver.' in text[:50]:
                    markers.append("HAS_VERSE_NUM")

                marker_str = f" [{', '.join(markers)}]" if markers else ""

                print(f"Paragraph {p_idx}:")
                print(f"  Classes: {p_class_str}")
                print(f"  Markers:{marker_str}")
                print(f"  Text (first 200 chars): {text[:200]}")
                if len(text) > 200:
                    print(f"  ... (truncated, total length: {len(text)})")
                print()

            # Show context: previous and next divs
            if div_idx > 0:
                print(f"\n--- PREVIOUS DIV {div_idx - 1} (context) ---")
                prev_div = all_divs[div_idx - 1]
                prev_ps = prev_div.find_all('p')[:5]
                for prev_p in prev_ps:
                    prev_class = ' '.join(prev_p.get('class', []))
                    prev_text = prev_p.get_text().strip()[:100]
                    print(f"  Class: {prev_class}")
                    print(f"  Text: {prev_text}")
                    print()

            if div_idx < len(all_divs) - 1:
                print(f"\n--- NEXT DIV {div_idx + 1} (context) ---")
                next_div = all_divs[div_idx + 1]
                next_ps = next_div.find_all('p')[:5]
                for next_p in next_ps:
                    next_class = ' '.join(next_p.get('class', []))
                    next_text = next_p.get_text().strip()[:100]
                    print(f"  Class: {next_class}")
                    print(f"  Text: {next_text}")
                    print()

            print("\n" + "=" * 80 + "\n")

