import streamlit as st
import fitz  # PyMuPDF
import io
from streamlit_sortables import sort_items

# Configuração da página
st.set_page_config(page_title="Organizador de PDFs", layout="centered")

# --- ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    div.stButton > button:first-child { background-color: #d32f2f; color: white; border-radius: 5px; width: 100%; }
    div.stDownloadButton > button { background-color: #1976d2; color: white; border-radius: 5px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.title("📄 Sistema de Mesclagem de Documentos")

# 1. ÁREA DE UPLOAD
uploaded_files = st.file_uploader("Selecione os arquivos PDF aqui", type="pdf", accept_multiple_files=True, key="upload_key")

if uploaded_files:
    arquivos_dict = {f.name: f for f in uploaded_files}
    nomes_arquivos = list(arquivos_dict.keys())

    st.write("---")
    st.subheader("🗂️ Arraste para Organizar a Ordem")
    st.caption("O primeiro arquivo da lista definirá o nome do documento final.")
    
    # COMPONENTE DE ARRASTAR E SOLTAR
    # Isso substitui o multiselect anterior
    ordem_selecionada = sort_items(nomes_arquivos)

    st.write("---")

    # Botão de Mesclagem
    if st.button("MESCLAR"):
        with st.spinner("Limpando metadados e organizando páginas..."):
            pdf_final = fitz.open()
            
            # Nomenclatura baseada no primeiro item da lista reordenada
            nome_original = ordem_selecionada[0]
            nome_base = nome_original[0:-4] if nome_original.lower().endswith('.pdf') else nome_original
            
            for nome in ordem_selecionada:
                arquivo_obj = arquivos_dict[nome]
                doc_temp = fitz.open(stream=arquivo_obj.read(), filetype="pdf")
                for pagina in doc_temp:
                    texto_limpo = " ".join(pagina.get_text().split())
                    termos = ["Documento original assinado eletronicamente", "INFORMAÇÕES DO DOCUMENTO", "Valor Legal: ORIGINAL"]
                    
                    # Filtro de páginas de assinatura isoladas
                    if any(t in texto_limpo for t in termos) and len(texto_limpo.split()) < 110:
                        continue 
                    
                    # Limpeza para aceitação no E-Docs
                    for w in pagina.widgets(): pagina.delete_widget(w)
                    for a in pagina.annots(): pagina.delete_annot(a)
                    
                    largura, altura = pagina.rect.width, pagina.rect.height
                    # Tarja lateral e rodapé
                    pagina.add_redact_annot(fitz.Rect(largura - 35, 0, largura, altura), fill=(1, 1, 1))
                    if any(t in texto_limpo for t in termos):
                         pagina.add_redact_annot(fitz.Rect(0, altura - 220, largura, altura), fill=(1, 1, 1))

                    pagina.apply_redactions()
                    pdf_final.insert_pdf(doc_temp, from_page=pagina.number, to_page=pagina.number)
            
            output = io.BytesIO()
            pdf_final.save(output, garbage=4, deflate=True, clean=True)
            st.session_state['pdf_gerado'] = output.getvalue()
            st.session_state['nome_arquivo'] = f"{nome_base} - mesclado.pdf"
            pdf_final.close()

    # ÁREA DE RESULTADO
    if 'pdf_gerado' in st.session_state:
        st.success(f"✅ Pronto: {st.session_state['nome_arquivo']}")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("⬇️ BAIXAR", st.session_state['pdf_gerado'], st.session_state['nome_arquivo'], "application/pdf")
        with col2:
            st.markdown('<a href="/" target="_self" style="text-decoration:none;"><button style="background-color:#6c757d; color:white; border-radius:5px; width:100%; border:none; height:38px; cursor:pointer;">🔄 LIMPAR TUDO</button></a>', unsafe_allow_html=True)
