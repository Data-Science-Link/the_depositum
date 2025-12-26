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
print("SEARCHING FOR EXODUS INTRODUCTION")
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

# Examine each found item
for idx, (item_num, keyword, item, soup) in enumerate(found_items):
    print("=" * 80)
    print(f"ITEM {item_num} (matched keyword: {keyword})")
    print("=" * 80)

    # Get all resourcetext divs
    all_divs = soup.find_all('div', class_='resourcetext')
    print(f"Total resourcetext divs: {len(all_divs)}\n")

    # Find divs with Exodus content
    for div_idx, div in enumerate(all_divs):
        div_text = div.get_text()
        has_exodus = any(kw.lower() in div_text.lower() for kw in exodus_keywords)

        if has_exodus:
            print(f"\n--- DIV {div_idx} (contains Exodus content) ---")
            paragraphs = div.find_all('p')
            print(f"Paragraphs in this div: {len(paragraphs)}\n")

            # Show all paragraphs in this div
            for p_idx, p in enumerate(paragraphs):
                p_class = p.get('class', [])
                p_class_str = ' '.join(p_class) if p_class else 'no-class'
                text = p.get_text().strip()

                # Highlight important paragraphs
                is_book_name = 'lang-en13' in p_class_str or 'lang-en14' in p_class_str
                is_intro_header = 'lang-en15' in p_class_str or 'INTRODUCTION' in text.upper()
                is_chapter = 'lang-en17' in p_class_str
                is_intro_text = ('The second Book of Moses' in text or
                                'called Exodus' in text or
                                'signifies going out' in text)

                marker = ""
                if is_book_name:
                    marker = " [BOOK NAME]"
                elif is_intro_header:
                    marker = " [INTRO HEADER]"
                elif is_chapter:
                    marker = " [CHAPTER]"
                elif is_intro_text:
                    marker = " [INTRO TEXT]"

                print(f"  P{p_idx}: class={p_class_str}{marker}")
                print(f"    Text: {text[:150]}")
                if len(text) > 150:
                    print(f"    ... (truncated, total length: {len(text)})")
                print()

            # Show context: previous and next divs
            if div_idx > 0:
                print(f"\n--- PREVIOUS DIV {div_idx - 1} (context) ---")
                prev_div = all_divs[div_idx - 1]
                prev_ps = prev_div.find_all('p')[:3]
                for prev_p in prev_ps:
                    prev_class = ' '.join(prev_p.get('class', []))
                    prev_text = prev_p.get_text().strip()[:100]
                    print(f"  Class: {prev_class}, Text: {prev_text}")

            if div_idx < len(all_divs) - 1:
                print(f"\n--- NEXT DIV {div_idx + 1} (context) ---")
                next_div = all_divs[div_idx + 1]
                next_ps = next_div.find_all('p')[:3]
                for next_p in next_ps:
                    next_class = ' '.join(next_p.get('class', []))
                    next_text = next_p.get_text().strip()[:100]
                    print(f"  Class: {next_class}, Text: {next_text}")

            print("\n" + "=" * 80 + "\n")

