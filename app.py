import streamlit as st
import numpy as np
import pandas as pd
import altair as alt

# -------------------------------------------------
# CONFIGURACIÓN GENERAL
# -------------------------------------------------
st.set_page_config(page_title="Simulador de Inventario Avanzado", layout="wide")
st.title("Simulador Interactivo de Inventario – Política (s, Q)")

st.markdown("""
Este simulador permite analizar el comportamiento del inventario de un producto 
bajo una política de reorden **(s, Q)**.  
Incluye:
- Escenarios comparativos
- Gráficas interactivas
- Análisis automático de resultados
""")

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.header("Parámetros del Modelo")

dias = st.sidebar.slider("Días a simular", 15, 120, 60)
I0 = st.sidebar.number_input("Inventario inicial", 0, 2000, 120)
s = st.sidebar.number_input("Punto de reorden (s)", 1, 500, 50)
Q = st.sidebar.number_input("Cantidad de pedido (Q)", 1, 1000, 100)
L = st.sidebar.number_input("Tiempo de entrega (L)", 1, 15, 3)
demanda_media = st.sidebar.slider("Demanda promedio diaria", 1, 50, 12)
escenarios = st.sidebar.checkbox("Activar comparación de escenarios")

# -------------------------------------------------
# FUNCIÓN PRINCIPAL
# -------------------------------------------------
def simular_inventario(dias, I0, s, Q, L, demanda_media):

    inventario = I0
    llegada_pedido = -1
    registros = []

    for t in range(dias):
        # demanda aleatoria Poisson
        demanda = np.random.poisson(demanda_media)

        # llegada del pedido
        if t == llegada_pedido:
            inventario += Q

        # ventas y faltantes
        ventas = min(inventario, demanda)
        faltantes = max(0, demanda - inventario)
        inventario -= ventas

        # disparo del pedido
        if inventario <= s and llegada_pedido < t:
            llegada_pedido = t + L

        # guardar registro
        registros.append([
            t, inventario, demanda, ventas, faltantes
        ])

    df = pd.DataFrame(registros, columns=["Día", "Inventario", "Demanda", "Ventas", "Faltantes"])
    return df


# -------------------------------------------------
# EJECUCIÓN PRINCIPAL
# -------------------------------------------------
if st.button("▶ Ejecutar simulación"):
    df = simular_inventario(dias, I0, s, Q, L, demanda_media)

    col1, col2 = st.columns(2)

    # Tabla
    col1.subheader("Tabla de resultados")
    col1.dataframe(df)

    # Gráfica
    col2.subheader("Evolución del inventario")
    
    chart = alt.Chart(df).mark_line(point=True).encode(
        x='Día',
        y='Inventario',
        tooltip=['Día', 'Inventario', 'Demanda', 'Faltantes']
    ).interactive()

    col2.altair_chart(chart, use_container_width=True)

    st.subheader("Faltantes por día")
    falt_chart = alt.Chart(df).mark_bar().encode(
        x='Día',
        y='Faltantes'
    ).interactive()
    st.altair_chart(falt_chart, use_container_width=True)

    # -------------------------------------------------
    # ANÁLISIS AUTOMÁTICO
    # -------------------------------------------------
    st.subheader("Análisis automático")
    falt_total = df["Faltantes"].sum()
    falt_dias = sum(df["Faltantes"] > 0)
    pedidos = (df["Inventario"] <= s).sum()

    st.write(f"""
    - **Total de faltantes:** {falt_total} unidades  
    - **Días con faltantes:** {falt_dias}  
    - **Días en que se disparó pedido:** {pedidos}
    """)

    # -------------------------------------------------
    # COMPARACIÓN DE ESCENARIOS
    # -------------------------------------------------
    if escenarios:
        st.subheader("Comparación de Escenarios Automática")
        escenarios_data = []
        for param in [demanda_media-3, demanda_media, demanda_media+3]:
            temp = simular_inventario(dias, I0, s, Q, L, param)
            temp["Escenario"] = f"Demanda={param}"
            escenarios_data.append(temp)

        full = pd.concat(escenarios_data)

        chart2 = alt.Chart(full).mark_line().encode(
            x="Día",
            y="Inventario",
            color="Escenario"
        ).interactive()

        st.altair_chart(chart2, use_container_width=True)

    # -------------------------------------------------
    # CONCLUSIONES AUTOMÁTICAS
    # -------------------------------------------------
    st.subheader("Conclusiones Generadas")
    concl = ""

    if falt_total == 0:
        concl += "- No se presentaron faltantes: la política (s, Q) es conservadora.\n"
    elif falt_total < 10:
        concl += "- Los faltantes son bajos: se podría ajustar ligeramente Q.\n"
    else:
        concl += "- Existen faltantes significativos: se recomienda aumentar s o Q.\n"

    if pedidos > dias * 0.4:
        concl += "- Se realizan demasiados pedidos: s es muy bajo.\n"
    elif pedidos == 0:
        concl += "- Nunca se dispara pedido: s es demasiado alto.\n"

    st.write(concl.replace("\n", "<br>"), unsafe_allow_html=True)
