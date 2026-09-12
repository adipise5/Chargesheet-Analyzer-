import fitz

from app.ingestion.native_text import extract_native_page, useful_native_text


def test_detects_useful_embedded_text(tmp_path):
    path = tmp_path / "native.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Synthetic native PDF source text with enough characters for direct extraction.")
    doc.save(path)
    doc.close()
    loaded = fitz.open(path)
    text, blocks = extract_native_page(loaded[0])
    assert useful_native_text(text)
    assert blocks and blocks[0]["confidence"] == 100.0
    loaded.close()


def test_rejects_tiny_native_layer():
    assert not useful_native_text("1")

