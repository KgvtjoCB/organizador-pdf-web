import streamlit as st
import fitz  # PyMuPDF
import io

# Configuração da página
st.set_page_config(page_title="Organizador de PDFs", layout="centered")

# --- ESTILIZAÇÃO CSS CUSTOMIZADA ---
st.markdown("""
    <style>
    /* Botão MESCLAR (Vermelho) */
    div.stButton > button:first-child {
        background-color: #d32f2f;
        color: white;
        border-radius: 5px;
        width: 100%;
    }
    /* Botão de DOWNLOAD (Azul) */
    div.stDownloadButton > button {
        background-color: #1976d2;
        color: white;
        border-radius: 5px;
        width: 100%;
    }
    /* Botão LIMPAR (Cinza) */
    .stButton > button[kind="secondary"] {
        background-color: #6c757d;
        color: white;
        border-radius: 5px;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📄 Sistema de Mesclagem de Documentos")

# Função para resetar o estado
def limpar_sessao():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# 1. ÁREA DE UPLOAD
uploaded_files = st.file_uploader("Selecione os arquivos PDF aqui", type="pdf", accept_multiple_files=True)

if uploaded_files:
    arquivos_dict = {f.name: f for f in uploaded_files}
    nomes_arquivos = list(arquivos_dict.keys())

    st.write("---")
    st.subheader("🗂️ Organizar Ordem de Mesclagem")
    
    ordem_selecionada = st.multiselect(
        "Selecione os arquivos na ordem correta:",
        options=nomes_arquivos,
        default=nomes_arquivos 
    )

    if st.button("MESCLAR"):
        if not ordem_selecionada:
            st.error("Selecione pelo menos um arquivo.")
        else:
            with st.spinner("Limpando metadados e comprimindo..."):
                pdf_final = fitz.open()
                
                nome_original = ordem_selecionada[0]
                nome_base = nome_original[0:-4] if nome_original.lower().endswith('.pdf') else nome_original
                nome_final_str = f"{nome_base} - mesclado.pdf"
                
                for nome in ordem_selecionada:
                    arquivo_obj = arquivos_dict[nome]
                    doc_temp = fitz.open(stream=arquivo_obj.read(), filetype="pdf")
                    
                    for pagina in doc_temp:
                        texto_pagina = pagina.get_text()
                        texto_limpo = " ".join(texto_pagina.split())
                        contagem_palavras = len(texto_limpo.split())
                        
                        termos_assinatura = [
                            "Documento original assinado eletronicamente",
                            "INFORMAÇÕES DO DOCUMENTO",
                            "Valor Legal: ORIGINAL",
                            "Natureza: DOCUMENTO NATO-DIGITAL"
                        ]
                        
                        if any(termo in texto_limpo for termo in termos_assinatura) and contagem_palavras < 110:
                            continue 
                        
                        for widget in pagina.widgets(): pagina.delete_widget(widget)
                        for annot in pagina.annots(): pagina.delete_annot(annot)
                            
                        largura, altura = pagina.rect.width, pagina.rect.height
                        margem_direita = fitz.Rect(largura - 35, 0, largura, altura)
                        pagina.add_redact_annot(margem_direita, fill=(1, 1, 1))
                        
                        if any(termo in texto_limpo for termo in termos_assinatura):
                             area_rodape = fitz.Rect(0, altura - 220, largura, altura)
                             pagina.add_redact_annot(area_rodape, fill=(1, 1, 1))

                        pagina.apply_redactions()
                        pdf_final.insert_pdf(doc_temp, from_page=pagina.number, to_page=pagina.number)
                
                output = io.BytesIO()
                pdf_final.save(output, garbage=4, deflate=True, clean=True)
                pdf_final.close()
                
                st.session_state['pdf_gerado'] = output.getvalue()
                st.session_state['nome_arquivo'] = nome_final_str

    # Exibição dos botões lado a lado
    if 'pdf_gerado' in st.session_state:
        st.success(f"✅ Arquivo gerado: {st.session_state['nome_arquivo']}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="⬇️ BAIXAR",
                data=st.session_state['pdf_gerado'],
                file_name=st.session_state['nome_arquivo'],
                mime="application/pdf"
            )
        with col2:
            st.button("🔄 LIMPAR", on_click=limpar_sessao)
