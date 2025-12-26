#!/usr/bin/env python3
"""Debug script to find Exodus introduction in EPUB"""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import sys

epub_path = 'Haydock Catholic Bible Comment - Haydock, George Leo_3948.epub'
book = epub.read_epub(epub_path)

search_texts = [
    'The second Book of Moses',
    'called Exodus from the Greek',
    'signifies going out',
    'Veelle Shemoth',
    '143 years',
    'prefigure the Christian'
]

found_items = []

for item in book.get_items():
    if item.get_type() != ebooklib.ITEM_DOCUMENT:
        continue
    
    html_content = item.get_content()
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check all paragraphs for any of our search texts
    for p in soup.find_all('p'):
        text = p.get_text()
        for search_text in search_texts:
            if search_text.lower() in text.lower():
                # This is likely the introduction
                found_items.append((search_text, p, text))
                break

# Process the first match
if found_items:
    search_text, p, text = found_items[0]
    print('=' * 80)
    print('FOUND THE TEXT!')
    print('=' * 80)
    print(f'Search text matched: {search_text}')
    print(f'Paragraph classes: {p.get("class")}')
    print(f'Paragraph text (first 400 chars): {text[:400]}')
    print()
    
    # Get parent structure
    parent = p.parent
    print(f'Parent tag: {parent.name if parent else None}')
    print(f'Parent classes: {parent.get("class") if parent and hasattr(parent, "get") else None}')
    print()
    
    # Get surrounding paragraphs
    print('Previous 5 paragraphs:')
    prev_siblings = list(p.find_previous_siblings('p'))[:5]
    for prev_p in reversed(prev_siblings):
        classes = prev_p.get("class", [])
        text_preview = prev_p.get_text()[:100].replace('\n', ' ')
        print(f'  Class: {classes}, Text: {text_preview}')
    print()
    
    print('Next 5 paragraphs:')
    next_siblings = list(p.find_next_siblings('p'))[:5]
    for next_p in next_siblings[:5]:
        classes = next_p.get("class", [])
        text_preview = next_p.get_text()[:100].replace('\n', ' ')
        print(f'  Class: {classes}, Text: {text_preview}')
    print()
    
    # Get the div structure
    div = p.find_parent('div')
    if div:
        print(f'Div classes: {div.get("class")}')
        all_ps_in_div = div.find_all('p')
        print(f'Total paragraphs in this div: {len(all_ps_in_div)}')
        print('All paragraph classes in this div (first 20):')
        for idx, div_p in enumerate(all_ps_in_div[:20]):
            classes = div_p.get('class', [])
            text_preview = div_p.get_text()[:80].replace('\n', ' ')
            print(f'  {idx}: {classes} - {text_preview}')
    
    # Also check for INTRODUCTION header nearby
    print()
    print('Looking for INTRODUCTION header in this div:')
    for div_p in all_ps_in_div:
        classes = div_p.get('class', [])
        text = div_p.get_text().strip()
        if 'lang-en15' in classes or 'INTRODUCTION' in text.upper():
            print(f'  FOUND: Class={classes}, Text={text[:100]}')
    
    # Check what comes before this div - look for book name
    print()
    print('Checking previous divs in this item for book name:')
    all_divs = soup.find_all('div', class_='resourcetext')
    current_div_idx = -1
    for idx, d in enumerate(all_divs):
        if d == div:
            current_div_idx = idx
            break
    
    if current_div_idx > 0:
        print(f'Previous div (index {current_div_idx - 1}):')
        prev_div = all_divs[current_div_idx - 1]
        prev_ps = prev_div.find_all('p')[:5]
        for prev_p in prev_ps:
            classes = prev_p.get('class', [])
            text = prev_p.get_text().strip()[:80]
            print(f'  Class={classes}, Text={text}')
    
    if current_div_idx < len(all_divs) - 1:
        print(f'\nNext div (index {current_div_idx + 1}):')
        next_div = all_divs[current_div_idx + 1]
        next_ps = next_div.find_all('p')[:5]
        for next_p in next_ps:
            classes = next_p.get('class', [])
            text = next_p.get_text().strip()[:80]
            print(f'  Class={classes}, Text={text}')
else:
    print('Text not found in EPUB')
