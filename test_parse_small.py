import os
from parse_docs import DocumentParser

file_path = "data/raw/CRDC Charter of Corporate Governance 2024.pdf"

try:
    parser = DocumentParser()
    print(f"Parsing {file_path}...")
    md_content = parser.parse_pdf(file_path)
    print(f"--- Parsed Content Preview ---")
    print(md_content[:500])
except Exception as e:
    print(f"Test failed: {e}")
