# OCR pipeline

Each PDF page is first inspected for a useful embedded text layer. Useful pages are extracted with PyMuPDF at confidence 100 and never OCRed. Other pages are rendered at 275 DPI and a non-destructive grayscale/contrast/median-filter/limited-deskew derivative is passed to Tesseract `guj+eng` using `image_to_data`.

Average recognized-word confidence, low-confidence word ratio, every word box, engine, source page, original text, normalized text, and review state are persisted. Low-confidence or mixed/handwriting-suspected pages may be sent only to local Qwen vision with the literal-transcription prompt. Its result is stored as a candidate. A correction preserves the original transcript and rebuilds affected chunks, graph, and findings.

