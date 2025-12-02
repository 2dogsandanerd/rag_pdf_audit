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

# CSS for "Shock Effect" (Red vs Green) + Scrollable Boxes
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
st.markdown("### See your documents through an AI's eyes")
st.info("Upload a PDF to check if it will choke your RAG pipeline.")

uploaded_file = st.file_uploader("Choose a PDF (e.g., scanned or with tables)", type="pdf")

if uploaded_file is not None:
    # Datei temporär speichern mit unique Namen (HN-safe)
    temp_dir = Path(tempfile.gettempdir())
    temp_path = temp_dir / f"rag_audit_{uuid.uuid4().hex[:8]}.pdf"

    try:
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
    except Exception as e:
        st.error(f"❌ Error saving file: {e}")
        st.stop()

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.header("💀 The 'Naive' Approach")
        st.caption("Standard Python libraries (pypdf, LangChain default)")

        with st.spinner("Extracting text (naive)..."):
            try:
                # Naive Analysis
                start_naive = time.time()
                reader = PdfReader(temp_path)
                naive_text = ""
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        naive_text += extracted
                time_naive = time.time() - start_naive

                # Improved Scan Detection
                text_length = len(naive_text.strip())
                is_scan = text_length < 50 or (text_length < 200 and len(reader.pages) > 1)

                if is_scan:
                    st.error("🚨 SCAN DETECTED! No text layer found.")
                    st.markdown('<div class="bad-box"><i>[EMPTY DOCUMENT / IMAGE DATA]</i><br><br>Standard RAG sees NOTHING here.</div>', unsafe_allow_html=True)
                else:
                    st.warning(f"Text found (chaos possible). Duration: {time_naive:.2f}s")
                    # Show raw text (scrollbar makes it manageable)
                    preview_text = naive_text.replace('<', '&lt;').replace('>', '&gt;')  # HTML escape
                    st.markdown(f'<div class="bad-box">{preview_text}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ Error in naive analysis: {e}")
                is_scan = True

    with col2:
        st.header("🧠 The 'Intelligent' Approach")
        st.caption("Your Stack: Docling + Layout Vision + OCR")

        try:
            with st.status("🚀 Deep Document Analysis running...", expanded=True) as status:
                start_smart = time.time()

                st.write("⚙️ Initializing vision models...")
                # Pipeline Options (OCR enabled)
                pipeline_options = PdfPipelineOptions(do_ocr=True, do_table_structure=True)
                converter = DocumentConverter(
                    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
                )

                st.write("👁️ Scanning document layout (pixel-level)...")
                st.write("📊 Detecting table structures...")
                result = converter.convert(temp_path)

                st.write("🔤 Running OCR analysis...")
                doc = result.document

                st.write("📐 Reconstructing semantic hierarchy...")
                md_output = doc.export_to_markdown()

                time_smart = time.time() - start_smart
                status.update(label=f"✅ Analysis complete! ({time_smart:.1f}s)", state="complete", expanded=False)

            # Display metrics (AFTER status block!)
            m1, m2, m3 = st.columns(3)
            m1.metric("Tables", len(doc.tables))
            m2.metric("Images/Graphics", len(doc.pictures))
            m3.metric("Characters", len(md_output))

            # Render markdown (scrollbar makes it manageable!)
            st.markdown("#### AI View (Markdown):")
            md_preview = md_output.replace('<', '&lt;').replace('>', '&gt;')
            st.markdown(f'<div class="good-box">{md_preview}</div>', unsafe_allow_html=True)

            # Actual Markdown Render Test
            with st.expander("📄 Preview: How the LLM 'understands' the structure (Rendered)"):
                st.markdown(md_output)

        except Exception as e:
            st.error(f"❌ Docling error: {e}")
            st.warning("Tip: Docling requires `tesseract-ocr` installed. Check dependencies!")
            # Fallback values for verdict
            doc = type('obj', (object,), {'tables': [], 'pictures': []})()

    st.divider()

    # The Verdict
    st.subheader("⚖️ The Verdict")

    if len(doc.tables) > 0 or is_scan:
        st.error("❌ THIS DOCUMENT IS TOXIC FOR STANDARD RAG.")
        st.write(f"Reason: {'It is a scan.' if is_scan else 'It contains complex tables.'}")
        st.markdown("**Recommendation:** Use an ingest stack with layout-aware parsing (e.g., Docling).")
        st.info("💡 Docling is Open Source: `pip install docling`")
    else:
        st.success("✅ Document is relatively simple. Standard RAG might work (but watch out for layouts).")

    # Cleanup: Temp-Datei löschen
    try:
        temp_path.unlink(missing_ok=True)
    except:
        pass  # Ignoriere Cleanup-Fehler
