import streamlit as st
import fitz  # PyMuPDF
import io

# Configuração da página
st.set_page_config(page_title="Organizador de PDFs", layout="centered")

# --- ESTILIZAÇÃO CSS CUSTOMIZADA ---
st.markdown("""
    <style>
    /* Estilo para o botão MESCLAR (Vermelho Harmônico) */
    div.stButton > button:first-child {
        background-color: #d32f2f;
        color: white;
        border-radius: 5px;
        border: none;
        width: 100%;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        background-color: #b71c1c;
        color: white;
    }

    /* Estilo para o botão de DOWNLOAD (Azul Harmônico) */
    div.stDownloadButton > button {
        background-color: #1976d2;
        color: white;
        border-radius: 5px;
        border: none;
        width: 100%;
        transition: 0.3s;
    }
    div.stDownloadButton > button:hover {
        background-color: #1565c0;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📄 Sistema de Mesclagem de Documentos")
st.info("Organize a ordem dos documentos abaixo. O download será feito via navegador.")

# 1. ÁREA DE UPLOAD
uploaded_files = st.file_uploader("Selecione os arquivos PDF aqui", type="pdf", accept_multiple_files=True)

if uploaded_files:
    arquivos_dict = {f.name: f for f in uploaded_files}
    nomes_arquivos = list(arquivos_dict.keys())

    st.write("---")
    st.subheader("🗂️ Organizar Ordem de Mesclagem")
    
    ordem_selecionada = st.multiselect(
        "Selecione os arquivos na ordem correta (o 1º define o nome final):",
        options=nomes_arquivos,
        default=nomes_arquivos 
    )

    # Botão MESCLAR (Estilizado via CSS como vermelho)
    if st.button("MESCLAR"):
        if not ordem_selecionada:
            st.error("Selecione pelo menos um arquivo.")
        else:
            with st.spinner("Limpando metadados e comprimindo arquivo..."):
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
                            "Natureza: DOCUMENTO NATO-DIGITAL",
                            "A disponibilidade do documento pode ser conferida"
                        ]
                        
                        tem_termo = any(termo in texto_limpo for termo in termos_assinatura)
                        if tem_termo and contagem_palavras < 110:
                            continue 
                        
                        for widget in pagina.widgets():
                            pagina.delete_widget(widget)
                        for annot in pagina.annots():
                            pagina.delete_annot(annot)
                            
                        largura, altura = pagina.rect.width, pagina.rect.height
                        margem_direita = fitz.Rect(largura - 35, 0, largura, altura)
                        pagina.add_redact_annot(margem_direita, fill=(1, 1, 1))
                        
                        if tem_termo:
                             area_rodape = fitz.Rect(0, altura - 220, largura, altura)
                             pagina.add_redact_annot(area_rodape, fill=(1, 1, 1))

                        pagina.apply_redactions()
                        pdf_final.insert_pdf(doc_temp, from_page=pagina.number, to_page=pagina.number)
                
                output = io.BytesIO()
                pdf_final.save(output, garbage=4, deflate=True, clean=True)
                pdf_final.close()
                
                st.session_state['pdf_gerado'] = output.getvalue()
                st.session_state['nome_arquivo'] = nome_final_str

    # Botão de DOWNLOAD (Estilizado via CSS como azul)
    if 'pdf_gerado' in st.session_state:
        st.success(f"✅ Arquivo gerado: {st.session_state['nome_arquivo']}")
        st.download_button(
            label="⬇️ CLIQUE AQUI PARA BAIXAR",
            data=st.session_state['pdf_gerado'],
            file_name=st.session_state['nome_arquivo'],
            mime="application/pdf"
        )