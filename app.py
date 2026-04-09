import streamlit as st
import random
import json
import io
import zipfile
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

LABELS = ['A', 'B', 'C', 'D']

st.set_page_config(page_title="Generatore Verifiche", page_icon="📝", layout="centered")

# ── Sidebar navigation ──────────────────────────────────────────────────────
st.sidebar.title("📚 Navigazione")
page = st.sidebar.radio("Vai a:", ["🖨️ Genera Verifica", "🗃️ Crea Database"])

# ════════════════════════════════════════════════════════════════════════════
# PAGE 1 — GENERA VERIFICA
# ════════════════════════════════════════════════════════════════════════════
if page == "🖨️ Genera Verifica":
    st.title("🖨️ Genera Verifica")
    st.markdown("Carica il tuo database JSON, configura la verifica e scarica i PDF.")

    # ── Upload JSON ──────────────────────────────────────────────────────────
    uploaded = st.file_uploader("📂 Carica il database domande (JSON)", type="json")

    if uploaded is None:
        st.info("Carica un file JSON per iniziare. Puoi crearne uno nella sezione **Crea Database**.")
        st.stop()

    try:
        data = json.load(uploaded)
        all_questions = data.get("quiz", data) if isinstance(data, dict) else data
        if not isinstance(all_questions, list) or len(all_questions) == 0:
            st.error("Il file JSON non contiene domande valide.")
            st.stop()
    except Exception as e:
        st.error(f"Errore nel leggere il file JSON: {e}")
        st.stop()

    total = len(all_questions)
    st.success(f"✅ Database caricato: **{total} domande** disponibili.")

    st.divider()

    # ── Form configurazione ──────────────────────────────────────────────────
    st.subheader("⚙️ Configura la verifica")

    col1, col2 = st.columns(2)
    with col1:
        materia = st.text_input("Materia", placeholder="es. Fisica - Magnetismo")
    with col2:
        data_verifica = st.text_input("Data verifica", placeholder="es. 15 aprile 2026")

    col3, col4 = st.columns(2)
    with col3:
        n_domande = st.slider("Numero di domande per copia", min_value=1, max_value=total, value=min(20, total))
    with col4:
        n_copie = st.number_input("Numero di copie diverse", min_value=1, max_value=50, value=1)

    st.divider()

    # ── Generate PDFs ────────────────────────────────────────────────────────
    if st.button("📄 Genera PDF", type="primary", use_container_width=True):
        if not materia.strip():
            st.warning("Inserisci il nome della materia.")
            st.stop()

        def build_pdf(questions, n_dom, mat, data_ver):
            buffer = io.BytesIO()
            selected = random.sample(questions, n_dom)

            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2.5*cm,
                bottomMargin=2.5*cm
            )

            styles = getSampleStyleSheet()

            title_style = ParagraphStyle('Title', parent=styles['Normal'],
                fontSize=18, fontName='Helvetica-Bold',
                textColor=colors.HexColor('#1a365d'),
                alignment=TA_CENTER, spaceAfter=4)
            subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                fontSize=10, fontName='Helvetica',
                textColor=colors.HexColor('#718096'),
                alignment=TA_CENTER, spaceAfter=20)
            nome_style = ParagraphStyle('Nome', parent=styles['Normal'],
                fontSize=11, fontName='Helvetica',
                textColor=colors.HexColor('#2d3748'), spaceAfter=4)
            q_num_style = ParagraphStyle('QNum', parent=styles['Normal'],
                fontSize=8, fontName='Helvetica-Bold',
                textColor=colors.HexColor('#2b6cb0'), spaceAfter=3)
            q_text_style = ParagraphStyle('QText', parent=styles['Normal'],
                fontSize=10.5, fontName='Helvetica-Bold',
                textColor=colors.HexColor('#2d3748'), spaceAfter=6, leading=15)
            ans_style = ParagraphStyle('Ans', parent=styles['Normal'],
                fontSize=10, fontName='Helvetica',
                textColor=colors.HexColor('#4a5568'),
                leftIndent=12, spaceAfter=3, leading=14)

            story = []
            story.append(Paragraph(f"Verifica di {mat}", title_style))
            story.append(Paragraph(data_ver, subtitle_style))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2b6cb0')))
            story.append(Spacer(1, 0.4*cm))
            story.append(Paragraph("Nome Cognome: _____________________________________________", nome_style))
            story.append(Spacer(1, 0.4*cm))

            for idx, q in enumerate(selected):
                answers = list(q['risposte'].items())
                random.shuffle(answers)

                block = []
                block.append(Paragraph(f"DOMANDA {idx + 1}", q_num_style))
                block.append(Paragraph(q['domanda'], q_text_style))
                for i, (_, testo) in enumerate(answers):
                    block.append(Paragraph(f"<b>{LABELS[i]}.</b>  {testo}", ans_style))
                block.append(Spacer(1, 0.5*cm))
                block.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0')))
                block.append(Spacer(1, 0.3*cm))
                story.append(KeepTogether(block))

            def add_page_number(canvas, doc):
                canvas.saveState()
                canvas.setFont('Helvetica', 9)
                canvas.setFillColor(colors.HexColor('#718096'))
                canvas.drawCentredString(A4[0] / 2, 1.2*cm, f"Pagina {canvas.getPageNumber()}")
                canvas.restoreState()

            doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
            buffer.seek(0)
            return buffer

        progress = st.progress(0, text="Generazione in corso...")
        pdf_files = []
        for i in range(n_copie):
            buf = build_pdf(all_questions, n_domande, materia.strip(), data_verifica.strip())
            pdf_files.append((f"verifica_{materia.strip().replace(' ', '_')}_copia{i+1}.pdf", buf))
            progress.progress((i + 1) / n_copie, text=f"Generata copia {i+1} di {n_copie}...")

        progress.empty()
        st.success(f"✅ {n_copie} {'copia generata' if n_copie == 1 else 'copie generate'}!")

        # Pack all PDFs into a single ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename, buf in pdf_files:
                zf.writestr(filename, buf.read())
        zip_buffer.seek(0)

        zip_name = f"verifiche_{materia.strip().replace(' ', '_')}.zip"
        st.download_button(
            label="⬇️ Scarica tutte le copie (.zip)",
            data=zip_buffer,
            file_name=zip_name,
            mime="application/zip",
            use_container_width=True,
            type="primary"
        )


# ════════════════════════════════════════════════════════════════════════════
# PAGE 2 — CREA DATABASE
# ════════════════════════════════════════════════════════════════════════════
elif page == "🗃️ Crea Database":
    st.title("🗃️ Crea Database Domande")
    st.markdown("Inserisci le domande e scarica il file JSON. Le domande **non vengono salvate** sul server.")

    # Inizializza session state
    if "domande" not in st.session_state:
        st.session_state.domande = []

    # ── Form nuova domanda ───────────────────────────────────────────────────
    st.subheader("➕ Aggiungi una domanda")

    with st.form("form_domanda", clear_on_submit=True):
        testo_domanda = st.text_area("Testo della domanda", placeholder="Scrivi qui la domanda...")

        st.markdown("**Risposte** (inserisci almeno 2)")
        col1, col2 = st.columns(2)
        with col1:
            r_a = st.text_input("Risposta A", placeholder="Risposta A")
            r_c = st.text_input("Risposta C", placeholder="Risposta C")
        with col2:
            r_b = st.text_input("Risposta B", placeholder="Risposta B")
            r_d = st.text_input("Risposta D", placeholder="Risposta D")

        submitted = st.form_submit_button("✅ Aggiungi domanda", use_container_width=True)

        if submitted:
            risposte = {}
            for label, testo in [("A", r_a), ("B", r_b), ("C", r_c), ("D", r_d)]:
                if testo.strip():
                    risposte[label] = testo.strip()

            if not testo_domanda.strip():
                st.error("Inserisci il testo della domanda.")
            elif len(risposte) < 2:
                st.error("Inserisci almeno 2 risposte.")
            else:
                nuova = {
                    "id": len(st.session_state.domande) + 1,
                    "domanda": testo_domanda.strip(),
                    "risposte": risposte
                }
                st.session_state.domande.append(nuova)
                st.success(f"Domanda {nuova['id']} aggiunta!")

    st.divider()

    # ── Lista domande inserite ───────────────────────────────────────────────
    n = len(st.session_state.domande)
    if n == 0:
        st.info("Nessuna domanda ancora inserita.")
    else:
        st.subheader(f"📋 Domande inserite: {n}")

        for i, q in enumerate(st.session_state.domande):
            with st.expander(f"**{q['id']}.** {q['domanda'][:80]}{'...' if len(q['domanda']) > 80 else ''}"):
                st.markdown(f"**Domanda:** {q['domanda']}")
                for label, testo in q['risposte'].items():
                    st.markdown(f"- **{label}.** {testo}")
                if st.button(f"🗑️ Elimina domanda {q['id']}", key=f"del_{i}"):
                    st.session_state.domande.pop(i)
                    # Ricalcola gli id
                    for j, d in enumerate(st.session_state.domande):
                        d['id'] = j + 1
                    st.rerun()

        st.divider()

        # ── Import da JSON esistente ─────────────────────────────────────────
        st.subheader("📂 Importa da JSON esistente")
        uploaded_db = st.file_uploader("Carica un JSON esistente per aggiungere domande", type="json", key="import_db")
        if uploaded_db:
            try:
                imported = json.load(uploaded_db)
                imported_list = imported.get("quiz", imported) if isinstance(imported, dict) else imported
                start_id = len(st.session_state.domande) + 1
                added = 0
                for q in imported_list:
                    if "domanda" in q and "risposte" in q:
                        st.session_state.domande.append({
                            "id": start_id + added,
                            "domanda": q["domanda"],
                            "risposte": q["risposte"]
                        })
                        added += 1
                st.success(f"Importate {added} domande!")
                st.rerun()
            except Exception as e:
                st.error(f"Errore nell'importare il file: {e}")

        st.divider()

        # ── Scarica JSON ─────────────────────────────────────────────────────
        st.subheader("⬇️ Scarica il database")
        col_a, col_b = st.columns(2)
        with col_a:
            nome_file = st.text_input("Nome file", value="domande", placeholder="nome_file")
        with col_b:
            st.markdown("<br>", unsafe_allow_html=True)
            json_bytes = json.dumps({"quiz": st.session_state.domande}, ensure_ascii=False, indent=2).encode("utf-8")
            st.download_button(
                label="💾 Scarica JSON",
                data=json_bytes,
                file_name=f"{nome_file.strip() or 'domande'}.json",
                mime="application/json",
                use_container_width=True
            )

        if st.button("🗑️ Svuota tutto il database", type="secondary", use_container_width=True):
            st.session_state.domande = []
            st.rerun()
