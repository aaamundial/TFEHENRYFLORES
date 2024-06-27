import streamlit as st

# Configurar la página
st.set_page_config(page_title="Mi Aplicación de IA", page_icon=":robot_face:", layout="wide")

# CSS Personalizado
st.markdown("""
<style>
    body {
        background-color: #0f0f0f;
        color: #ffffff;
        font-family: 'Arial', sans-serif;
    }
    .main-header {
        color: #00C48F;
        font-size: 48px;
        font-weight: bold;
        text-align: center;
        margin-top: 50px;
    }
    .sub-header {
        color: #ffffff;
        font-size: 24px;
        text-align: center;
        margin-bottom: 30px;
    }
    .search-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 30px;
    }
    .search-input {
        background-color: #333;
        color: #fff;
        border: 1px solid #00C48F;
        border-radius: 5px;
        padding: 10px;
        font-size: 18px;
        width: 400px;
        margin-right: 10px;
    }
    .search-button {
        background-color: #00C48F;
        color: #fff;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 18px;
    }
    .cards-container {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 20px;
    }
    .card {
        background-color: #1a1a1a;
        color: #00C48F;
        border: 1px solid #00C48F;
        border-radius: 5px;
        padding: 20px;
        text-align: center;
        width: 200px;
        cursor: pointer;
        transition: transform 0.2s;
    }
    .card:hover {
        transform: scale(1.05);
    }
</style>
""", unsafe_allow_html=True)

# Título y subtítulo
st.markdown('<div class="main-header">La escuela de tecnología de Latinoamérica</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Más de 5 millones de estudiantes y más de 3,000 empresas aprenden en [TuNombreDeApp]</div>', unsafe_allow_html=True)

# Barra de búsqueda
st.markdown('<div class="search-container">', unsafe_allow_html=True)
search_query = st.text_input("", placeholder="¿Qué quieres aprender?", key="search", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# Botón de búsqueda
if st.button('Buscar', key="search_button"):
    st.write(f"Resultados de búsqueda para: {search_query}")

# Tarjetas de ejemplo
st.markdown('<div class="cards-container">', unsafe_allow_html=True)
if st.button("Data Science e Inteligencia Artificial", key="card1"):
    pass
if st.button("Ciberseguridad", key="card2"):
    pass
if st.button("Liderazgo y Management", key="card3"):
    pass
if st.button("English Academy", key="card4"):
    pass
st.markdown('</div>', unsafe_allow_html=True)
