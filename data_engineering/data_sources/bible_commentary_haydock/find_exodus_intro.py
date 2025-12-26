#!/usr/bin/env python3
"""Find the exact location of Exodus introduction in the EPUB"""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from pathlib import Path

epub_path = Path(__file__).parent / 'Haydock Catholic Bible Comment - Haydock, George Leo_3948.epub'
book = epub.read_epub(str(epub_path))

# Specific text that should be in the Exodus introduction
intro_text = "The second Book of Moses is called Exodus"

print("=" * 80)
print("SEARCHING FOR EXODUS INTRODUCTION")
print("=" * 80)
print(f"Looking for: '{intro_text}'\n")

found = False
item_count = 0

for item in book.get_items():
    if item.get_type() != ebooklib.ITEM_DOCUMENT:
        continue

    item_count += 1
    html_content = item.get_content()
    soup = BeautifulSoup(html_content, 'html.parser')

    # Check if this item contains the introduction text
    all_text = soup.get_text()
    if intro_text.lower() in all_text.lower():
        found = True
        print(f"✓ FOUND in ITEM {item_count}\n")

        # Find all resourcetext divs
        all_divs = soup.find_all('div', class_='resourcetext')
        print(f"Total resourcetext divs: {len(all_divs)}\n")

        # Find the specific div and paragraph containing the intro
        for div_idx, div in enumerate(all_divs):
            div_text = div.get_text()
            if intro_text.lower() in div_text.lower():
                print(f"{'='*80}")
                print(f"DIV {div_idx} contains the introduction")
                print(f"{'='*80}\n")

                paragraphs = div.find_all('p')
                print(f"Total paragraphs in this div: {len(paragraphs)}\n")

                # Find the paragraph with the intro text
                for p_idx, p in enumerate(paragraphs):
                    p_text = p.get_text()
                    p_class = p.get('class', [])
                    p_class_str = ' '.join(p_class) if p_class else 'no-class'

                    if intro_text.lower() in p_text.lower():
                        print(f"✓ FOUND in Paragraph {p_idx}:")
                        print(f"  Classes: {p_class_str}")
                        print(f"  Text (first 300 chars): {p_text[:300]}")
                        if len(p_text) > 300:
                            print(f"  ... (total length: {len(p_text)})")
                        print()

                # Show ALL paragraphs in this div to see the structure
                print(f"\n{'='*80}")
                print(f"ALL PARAGRAPHS IN THIS DIV:")
                print(f"{'='*80}\n")
                for p_idx, p in enumerate(paragraphs):
                    p_class = p.get('class', [])
                    p_class_str = ' '.join(p_class) if p_class else 'no-class'
                    p_text = p.get_text().strip()

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
                    if intro_text.lower() in p_text.lower():
                        markers.append("***INTRO_TEXT***")

                    marker_str = f" [{', '.join(markers)}]" if markers else ""

                    print(f"Paragraph {p_idx}:")
                    print(f"  Classes: {p_class_str}{marker_str}")
                    print(f"  Text: {p_text[:200]}")
                    if len(p_text) > 200:
                        print(f"  ... (truncated, total length: {len(p_text)})")
                    print()

                # Show previous and next divs for context
                if div_idx > 0:
                    print(f"\n{'='*80}")
                    print(f"PREVIOUS DIV {div_idx - 1} (context):")
                    print(f"{'='*80}\n")
                    prev_div = all_divs[div_idx - 1]
                    prev_ps = prev_div.find_all('p')[:5]
                    for prev_p in prev_ps:
                        prev_class = ' '.join(prev_p.get('class', []))
                        prev_text = prev_p.get_text().strip()[:150]
                        print(f"  Class: {prev_class}")
                        print(f"  Text: {prev_text}")
                        print()

                if div_idx < len(all_divs) - 1:
                    print(f"\n{'='*80}")
                    print(f"NEXT DIV {div_idx + 1} (context):")
                    print(f"{'='*80}\n")
                    next_div = all_divs[div_idx + 1]
                    next_ps = next_div.find_all('p')[:5]
                    for next_p in next_ps:
                        next_class = ' '.join(next_p.get('class', []))
                        next_text = next_p.get_text().strip()[:150]
                        print(f"  Class: {next_class}")
                        print(f"  Text: {next_text}")
                        print()

                break

if not found:
    print("✗ Introduction text not found in EPUB")

