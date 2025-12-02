# 🔍 RAG Ingest X-Ray

**Sieh dein Dokument durch die Augen einer KI.**

Ein einfaches Tool um zu prüfen, ob deine RAG-Pipeline an einem PDF ersticken wird.

![RAG Ingest X-Ray Interface](./head.png)

## Quick Start

```bash
# 1. System-Dependencies (für OCR)
sudo apt-get install tesseract-ocr  # Linux
# brew install tesseract            # macOS

# 2. Python Dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

## Was macht das Tool?

Vergleicht Side-by-Side:
- **💀 Naiver Ansatz:** Standard pypdf (was die meisten Tutorials nutzen)
- **🧠 Intelligenter Ansatz:** Docling mit Layout-Awareness & OCR

![Side-by-Side Comparison](./mid.png)

## Warum?

90% aller RAG-Tutorials ignorieren:
- Gescannte PDFs (keine Text-Ebene)
- Tabellen (werden zu Datensalat)
- Mehrspaltige Layouts (falsche Lesereihenfolge)

Dieses Tool zeigt dir **sofort** ob dein Dokument "toxisch" für Standard-RAG ist.

## Output

- ✅ **Grün:** Standard-RAG könnte funktionieren
- ❌ **Rot:** Du brauchst Layout-Aware Parsing (z.B. Docling)

## License

MIT (do whatever you want)
