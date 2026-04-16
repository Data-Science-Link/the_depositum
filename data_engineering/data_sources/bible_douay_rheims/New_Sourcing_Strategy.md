# **DATA SOURCING STRATEGY: PILLAR A (SCRIPTURE)**

**Project:** The Depositum

**Component:** Pillar A (The Douay-Rheims Bible)

**Status:** Source Locked & Approved

## **1\. Executive Summary**

To maintain strict adherence to the "Heresy Guard" protocol, ensure 100% auditable public domain compliance, and guarantee pipeline stability, the project has abandoned third-party APIs (e.g., bible-api.com) and commercial eBooks. All Scriptural data will be programmatically extracted from a static, offline UTF-8 text file.

## **2\. The Approved Source: Project Gutenberg \#8300**

* **Source URL:** https://www.gutenberg.org/ebooks/8300  
* **Format:** Plain Text UTF-8  
* **Why \#8300 (and not \#1581):** eBook \#8300 contains exactly the 73-book Catholic canon defined by the Council of Trent. eBook \#1581 includes apocryphal texts (e.g., 3 & 4 Esdras). Using \#8300 inherently prevents the Producer Gem from accidentally generating episodes based on non-canonical texts.

## **3\. Historical & Theological Validation**

* **The Text:** The Gutenberg file is the **Challoner Revision** (1749–1752) of the original 1582 Douay-Rheims translation.  
* **Audio-First Compatibility:** Bishop Challoner smoothed out the highly Latinized, clunky syntax of the original 16th-century text. This revision provides the exact same orthodox theology and Vulgate fidelity as the 1899 American Edition, but ensures the AI TTS engine (Host 1 / The Lector) can read the text with a natural, dramatic cadence without hurting listener retention.

## **4\. Python Extraction Architecture (Next Steps)**

A dedicated Python script must be written to parse the Gutenberg .txt file into the required Markdown files. The script must execute the following four steps:

1. **The Gutenberg Guillotine:** Use Regex to delete everything before \*\*\* START OF THE PROJECT GUTENBERG EBOOK and after \*\*\* END OF...  
2. **Book Recognition:** Use Regex to identify the 73 standardized book headers and split the document accordingly.  
3. **SOP Naming Convention (CRITICAL):** The script must programmatically save each book using the exact required nomenclature: Bible\_Book\_XX\_Name.md (e.g., Bible\_Book\_01\_Genesis.md). If this fails, the Producer Gem will not recognize the file as Scripture.  
4. **Audio-First Sanitization:** The script must strip all bracketed text (e.g., \[See footnote 1\]) and archaic formatting asterisks to prevent the AI Lector from reading them aloud and ruining the audio immersion.

## **5\. Pipeline Safety Reminders**

* **No Modern Translations:** Never introduce text from the NIV, NABRE, or RSV-CE into this parsing pipeline.