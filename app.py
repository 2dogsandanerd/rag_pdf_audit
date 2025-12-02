import streamlit as st
import time
import tempfile
import uuid
from pathlib import Path
from pypdf import PdfReader
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions
from docling.datamodel.base_models import InputFormat

# Seite konfigurieren
st.set_page_config(layout="wide", page_title="RAG Ingest X-Ray")

# CSS für den "Schock-Effekt" (Rot vs Grün) + Scrollbare Boxen
st.markdown("""
<style>
    .bad-box {
        border: 2px solid #ff4b4b;
        padding: 10px;
        border-radius: 5px;
        background-color: #ffebeb;
        color: black;
        max-height: 400px;
        overflow-y: auto;
    }
    .good-box {
        border: 2px solid #4caf50;
        padding: 10px;
        border-radius: 5px;
        background-color: #e8f5e9;
        color: black;
        max-height: 400px;
        overflow-y: auto;
    }
    .stCode { font-family: 'Courier New', monospace; }
</style>
""", unsafe_allow_html=True)

st.title("🔍 RAG Ingest X-Ray")
st.markdown("### Sieh dein Dokument durch die Augen einer KI")
st.info("Lade ein PDF hoch um zu prüfen, ob deine RAG-Pipeline daran ersticken wird.")

uploaded_file = st.file_uploader("Wähle ein PDF (z.B. gescannt oder mit Tabellen)", type="pdf")

if uploaded_file is not None:
    # Datei temporär speichern mit unique Namen (HN-safe)
    temp_dir = Path(tempfile.gettempdir())
    temp_path = temp_dir / f"rag_audit_{uuid.uuid4().hex[:8]}.pdf"

    try:
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
    except Exception as e:
        st.error(f"❌ Fehler beim Speichern: {e}")
        st.stop()

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.header("💀 Der 'Naive' Ansatz")
        st.caption("Standard Python-Bibliotheken (pypdf, LangChain default)")

        with st.spinner("Extrahiere Text (Naiv)..."):
            try:
                # Naive Analyse
                start_naive = time.time()
                reader = PdfReader(temp_path)
                naive_text = ""
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        naive_text += extracted
                time_naive = time.time() - start_naive

                # Verbesserte Scan-Detection
                text_length = len(naive_text.strip())
                is_scan = text_length < 50 or (text_length < 200 and len(reader.pages) > 1)

                if is_scan:
                    st.error("🚨 SCAN ERKANNT! Keine Text-Ebene gefunden.")
                    st.markdown('<div class="bad-box"><i>[LEERES DOKUMENT / BILDDATEN]</i><br><br>Die Standard-RAG sieht hier NICHTS.</div>', unsafe_allow_html=True)
                else:
                    st.warning(f"Text gefunden (Chaos möglich). Dauer: {time_naive:.2f}s")
                    # Zeige rohen Textbrei (scrollbar macht's handhabbar)
                    preview_text = naive_text.replace('<', '&lt;').replace('>', '&gt;')  # HTML escape
                    st.markdown(f'<div class="bad-box">{preview_text}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ Fehler bei naiver Analyse: {e}")
                is_scan = True

    with col2:
        st.header("🧠 Der 'Intelligente' Ansatz")
        st.caption("Dein Stack: Docling + Layout Vision + OCR")

        with st.status("🚀 Deep Document Analysis läuft...", expanded=True) as status:
            try:
                start_smart = time.time()

                st.write("⚙️ Initialisiere Vision-Modelle...")
                # Pipeline Optionen (OCR an)
                pipeline_options = PdfPipelineOptions(do_ocr=True, do_table_structure=True)
                converter = DocumentConverter(
                    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
                )

                st.write("👁️ Scanne Dokument-Layout (Pixel-Ebene)...")
                st.write("📊 Erkenne Tabellen-Strukturen...")
                result = converter.convert(temp_path)

                st.write("🔤 OCR-Analyse läuft...")
                doc = result.document

                st.write("📐 Rekonstruiere semantische Hierarchie...")
                md_output = doc.export_to_markdown()

                time_smart = time.time() - start_smart
                status.update(label=f"✅ Analyse abgeschlossen! ({time_smart:.1f}s)", state="complete", expanded=False)

                # Metriken anzeigen
                m1, m2, m3 = st.columns(3)
                m1.metric("Tabellen", len(doc.tables))
                m2.metric("Bilder/Grafiken", len(doc.pictures))
                m3.metric("Zeichen", len(md_output))

                # Markdown rendern (scrollbar macht's handhabbar!)
                st.markdown("#### KI-Sicht (Markdown):")
                md_preview = md_output.replace('<', '&lt;').replace('>', '&gt;')
                st.markdown(f'<div class="good-box">{md_preview}</div>', unsafe_allow_html=True)

                # Echter Markdown Render-Test
                with st.expander("📄 Vorschau: Wie das LLM die Struktur 'versteht' (Rendered)"):
                    st.markdown(md_output)

            except Exception as e:
                status.update(label="❌ Fehler aufgetreten", state="error", expanded=True)
                st.error(f"❌ Docling-Fehler: {e}")
                st.warning("Tipp: Docling braucht `tesseract-ocr` installiert. Prüfe Dependencies!")
                # Fallback-Werte für das Urteil
                doc = type('obj', (object,), {'tables': [], 'pictures': []})()

    st.divider()

    # Das Urteil
    st.subheader("⚖️ Das Urteil")

    if len(doc.tables) > 0 or is_scan:
        st.error("❌ DIESES DOKUMENT IST TOXISCH FÜR STANDARD-RAGs.")
        st.write(f"Grund: {'Es ist ein Scan.' if is_scan else 'Es enthält komplexe Tabellen.'}")
        st.markdown("**Empfehlung:** Nutze einen Ingest-Stack mit Layout-Aware Parsing (z.B. Docling).")
        st.info("💡 Docling ist Open Source: `pip install docling`")
    else:
        st.success("✅ Dokument ist relativ einfach. Standard-RAG könnte funktionieren (aber pass auf Layouts auf).")

    # Cleanup: Temp-Datei löschen
    try:
        temp_path.unlink(missing_ok=True)
    except:
        pass  # Ignoriere Cleanup-Fehler
