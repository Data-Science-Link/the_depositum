#!/usr/bin/env python3
"""Find the complete structure around Exodus introduction"""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

epub_path = 'Haydock Catholic Bible Comment - Haydock, George Leo_3948.epub'
book = epub.read_epub(epub_path)

# Find the item containing the Exodus introduction
intro_found = False
for item in book.get_items():
    if item.get_type() != ebooklib.ITEM_DOCUMENT:
        continue

    html_content = item.get_content()
    soup = BeautifulSoup(html_content, 'html.parser')

    # Check if this item contains the Exodus introduction
    all_text = soup.get_text()
    if 'The second Book of Moses is called Exodus' in all_text:
        print('=' * 80)
        print(f'FOUND EXODUS INTRODUCTION IN ITEM')
        print('=' * 80)

        all_divs = soup.find_all('div', class_='resourcetext')
        print(f'Total resourcetext divs in this item: {len(all_divs)}\n')

        # Find the div with the introduction
        intro_div_idx = -1
        for idx, div in enumerate(all_divs):
            div_text = div.get_text()
            if 'The second Book of Moses is called Exodus' in div_text:
                intro_div_idx = idx
                break

        if intro_div_idx >= 0:
            print(f'Introduction is in div index {intro_div_idx}\n')

            # Show divs before (looking for book name)
            print('DIVS BEFORE INTRODUCTION (looking for book name):')
            for i in range(max(0, intro_div_idx - 5), intro_div_idx):
                div = all_divs[i]
                ps = div.find_all('p')[:3]
                print(f'\n  Div {i}:')
                for p in ps:
                    classes = p.get('class', [])
                    text = p.get_text().strip()[:100]
                    print(f'    {classes} - {text}')

            # Show the introduction div
            print(f'\n\nINTRODUCTION DIV (index {intro_div_idx}):')
            div = all_divs[intro_div_idx]
            ps = div.find_all('p')
            for p in ps:
                classes = p.get('class', [])
                text = p.get_text().strip()[:200]
                print(f'  {classes} - {text}')

            # Show divs after (looking for chapter 1)
            print('\n\nDIVS AFTER INTRODUCTION (looking for chapter 1):')
            for i in range(intro_div_idx + 1, min(len(all_divs), intro_div_idx + 6)):
                div = all_divs[i]
                ps = div.find_all('p')[:3]
                print(f'\n  Div {i}:')
                for p in ps:
                    classes = p.get('class', [])
                    text = p.get_text().strip()[:100]
                    print(f'    {classes} - {text}')

        intro_found = True
        break

if not intro_found:
    print('Exodus introduction not found')

