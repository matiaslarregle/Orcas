import streamlit as st
import pandas as pd
import folium
import base64
import os
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from streamlit_option_menu import option_menu
import plotly.express as px
import itertools
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Avistajes de Orcas Península Valdés", layout="wide")

df = pd.read_csv("Orcas.csv")
df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

with st.sidebar:
    seleccion = option_menu(
        "Visualizaciones", 
        [
            "Mapa de Avistajes",
            "Gráficos por Categorías",
            "Datos Generales",
            "Relación entre Orcas"
        ],
        icons=["map", "bar-chart", "clipboard-data", "people"],
        menu_icon="cast", 
        default_index=0
    )

st.sidebar.header("Filtros")

grupos = st.sidebar.multiselect("Grupo", options=sorted(df["Grupo"].dropna().unique()))
df_tmp = df[df["Grupo"].isin(grupos)] if grupos else df

orcas = st.sidebar.multiselect("Orca", options=sorted(df_tmp["Orca"].dropna().unique()))
df_tmp = df_tmp[df_tmp["Orca"].isin(orcas)] if orcas else df_tmp

lugares = st.sidebar.multiselect("Lugar", options=sorted(df_tmp["Lugar"].dropna().unique()))
df_tmp = df_tmp[df_tmp["Lugar"].isin(lugares)] if lugares else df_tmp

sexos = st.sidebar.multiselect("Sexo", options=sorted(df_tmp["Sexo"].dropna().unique()))
df_tmp = df_tmp[df_tmp["Sexo"].isin(sexos)] if sexos else df_tmp

varadoras = st.sidebar.multiselect("Varadora", options=sorted(df_tmp["Varadora"].dropna().unique()))

min_fecha = df["Fecha"].min().to_pydatetime()
max_fecha = df["Fecha"].max().to_pydatetime()
rango_fechas = st.sidebar.slider("Rango de fechas", min_fecha, max_fecha, (min_fecha, max_fecha), format="YYYY-MM-DD")

df_filtrado = df.copy()
if grupos:
    df_filtrado = df_filtrado[df_filtrado["Grupo"].isin(grupos)]
if orcas:
    df_filtrado = df_filtrado[df_filtrado["Orca"].isin(orcas)]
if lugares:
    df_filtrado = df_filtrado[df_filtrado["Lugar"].isin(lugares)]
if sexos:
    df_filtrado = df_filtrado[df_filtrado["Sexo"].isin(sexos)]
if varadoras:
    df_filtrado = df_filtrado[df_filtrado["Varadora"].isin(varadoras)]
df_filtrado = df_filtrado[(df_filtrado["Fecha"] >= rango_fechas[0]) & (df_filtrado["Fecha"] <= rango_fechas[1])]

st.markdown(f"📆 Mostrando registros entre **{rango_fechas[0].strftime('%d/%m/%Y')}** y **{rango_fechas[1].strftime('%d/%m/%Y')}**")

if seleccion == "Mapa de Avistajes":
    st.title("Orcas Península Valdés")

    df["Latitud"] = pd.to_numeric(df["Latitud"], errors="coerce")
    df["Longitud"] = pd.to_numeric(df["Longitud"], errors="coerce")
    df.dropna(subset=["Latitud", "Longitud"], inplace=True)

    df_avistajes = df[["Fecha", "Lugar", "Latitud", "Longitud", "Orcas", "Link"]].drop_duplicates()

    df_orcas_filtradas = df.copy()
    if grupos:
        df_orcas_filtradas = df_orcas_filtradas[df_orcas_filtradas["Grupo"].isin(grupos)]
    if orcas:
        df_orcas_filtradas = df_orcas_filtradas[df_orcas_filtradas["Orca"].isin(orcas)]
    if lugares:
        df_orcas_filtradas = df_orcas_filtradas[df_orcas_filtradas["Lugar"].isin(lugares)]
    if sexos:
        df_orcas_filtradas = df_orcas_filtradas[df_orcas_filtradas["Sexo"].isin(sexos)]
    if varadoras:
        df_orcas_filtradas = df_orcas_filtradas[df_orcas_filtradas["Varadora"].isin(varadoras)]
    df_orcas_filtradas = df_orcas_filtradas[
        (df_orcas_filtradas["Fecha"] >= rango_fechas[0]) & (df_orcas_filtradas["Fecha"] <= rango_fechas[1])
    ]

    def contiene_orca_valida(orcas_avistaje, orcas_validas):
        lista = [o.strip() for o in orcas_avistaje.split(",")]
        return any(orca in orcas_validas for orca in lista)

    orcas_validas = df_orcas_filtradas["Orca"].unique().tolist()
    df_avistajes_filtrado = df_avistajes[df_avistajes["Orcas"].apply(lambda x: contiene_orca_valida(x, orcas_validas))]

    def crear_popup_avistaje(row):
        return folium.Popup(f"""
            <div style="width:220px; font-family:Arial; font-size:13px">
                <strong>🐋 Orcas en el avistaje:</strong><br> {row['Orcas']}<br>
                <strong>📍 Lugar:</strong> {row['Lugar']}<br>
                <strong>📅 Fecha:</strong> {row['Fecha'].date()}<br><br>
                <a href="{row['Link']}" target="_blank" style="color:#0077cc">🔗 Ver en Instagram</a>
            </div>
        """, max_width=250)

    mapa_orcas = folium.Map(
        location=[-45.0, -62.0],
        zoom_start=6,
        tiles="https://basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png",
        attr="© CartoDB"
    )
    marker_cluster = MarkerCluster().add_to(mapa_orcas)

    for _, row in df_avistajes_filtrado.iterrows():
        icono_orca = folium.CustomIcon(
            "Orca.png", 
            icon_size=(40, 40)
        )

        folium.Marker(
            location=[row["Latitud"], row["Longitud"]],
            popup=crear_popup_avistaje(row),
            icon=icono_orca
        ).add_to(marker_cluster)

    st_folium(mapa_orcas, width=700, height=500, returned_objects=[])


elif seleccion == "Gráficos por Categorías":
    st.title("Orcas Península Valdés")

    orca_unica = len(orcas) == 1
    opciones_categoria = ["Lugar", "Orca"] if orca_unica else ["Sexo", "Orca", "Grupo", "Lugar", "Varadora"]

    categoria = st.selectbox("Seleccioná una categoría para agrupar los datos:", options=opciones_categoria)
    columna_categoria = "Orca" if categoria == "Avistajes" else categoria

    if df_filtrado.empty:
        st.warning("⚠️ No hay datos para mostrar con los filtros actuales.")
    else:
        conteo_cat = df_filtrado[columna_categoria].value_counts().reset_index()
        conteo_cat.columns = [categoria, "Cantidad"]

        fig = px.bar(conteo_cat, x=categoria, y="Cantidad", color="Cantidad",
                     color_discrete_sequence=px.colors.sequential.Blues,
                     text="Cantidad",
                     title=f"Cantidad de registros por {categoria}")
        st.plotly_chart(fig, use_container_width=True)

elif seleccion == "Datos Generales":
    st.title("Orcas Península Valdés")

    df_orcas_filtradas = df_filtrado.drop_duplicates(subset=["Orca"])

    df_base = df.copy()
    if grupos:
        df_base = df_base[df_base["Grupo"].isin(grupos)]
    if orcas:
        df_base = df_base[df_base["Orca"].isin(orcas)]
    if lugares:
        df_base = df_base[df_base["Lugar"].isin(lugares)]
    df_base = df_base[(df_base["Fecha"] >= rango_fechas[0]) & (df_base["Fecha"] <= rango_fechas[1])]

    if sexos:
        df_base = df_base[df_base["Sexo"].isin(sexos)]
    if varadoras:
        df_base = df_base[df_base["Varadora"].isin(varadoras)]

    df_base_unicas = df_base.drop_duplicates(subset=["Orca"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de orcas identificadas", df_orcas_filtradas["Orca"].nunique())
    col2.metric("Hembras", df_orcas_filtradas[df_orcas_filtradas["Sexo"] == "♀"]["Orca"].nunique())
    col3.metric("Machos", df_orcas_filtradas[df_orcas_filtradas["Sexo"] == "♂"]["Orca"].nunique())

    col4, col5 = st.columns(2)
    col4.metric("Orcas que varan", df_orcas_filtradas[df_orcas_filtradas["Varadora"] == "Sí"]["Orca"].nunique())
    col5.metric("Cantidad de grupos", df_orcas_filtradas["Grupo"].nunique())

    st.markdown("---")

    st.subheader("Distribución por Grupo")
    grupo_counts = df_orcas_filtradas["Grupo"].value_counts().reset_index()
    grupo_counts.columns = ["Grupo", "Cantidad"]
    fig_grupo = px.bar(grupo_counts, x="Grupo", y="Cantidad", text="Cantidad",
                       color="Cantidad", color_discrete_sequence=px.colors.sequential.Teal)
    st.plotly_chart(fig_grupo, use_container_width=True)

    st.markdown("---")

    st.subheader("Distribución por Sexo")
    sexo_counts = df_base_unicas["Sexo"].value_counts().reset_index()
    sexo_counts.columns = ["Sexo", "Cantidad"]
    fig_sexo = px.pie(sexo_counts, names="Sexo", values="Cantidad",
                      color_discrete_sequence=px.colors.sequential.Teal)
    st.plotly_chart(fig_sexo, use_container_width=True)

    st.markdown("---")

    st.subheader("Varadoras")
    varan = df_base_unicas[df_base_unicas["Varadora"] == "Sí"]["Orca"].tolist()
    if varan:
        st.write("Estas orcas fueron registradas como varadoras:")
        st.markdown(", ".join(sorted(varan)))
    else:
        st.info("No hay orcas registradas como varadoras.")

    st.markdown("---")

    st.subheader("Catálogo de Orcas")
    columnas_mostrar = ["Orca", "Sexo", "Grupo", "Varadora"]
    st.dataframe(df_orcas_filtradas[columnas_mostrar].sort_values("Orca").reset_index(drop=True))

    csv = df_orcas_filtradas[columnas_mostrar].to_csv(index=False).encode("utf-8")
    st.download_button("📥 Descargar como CSV", data=csv, file_name="orcas_filtradas.csv", mime="text/csv")

elif seleccion == "Relación entre Orcas":
    st.title("Orcas Península Valdés")

    df_filtrado = df.copy()
    if grupos:
        df_filtrado = df_filtrado[df_filtrado["Grupo"].isin(grupos)]
    if orcas:
        df_filtrado = df_filtrado[df_filtrado["Orca"].isin(orcas)]
    if lugares:
        df_filtrado = df_filtrado[df_filtrado["Lugar"].isin(lugares)]

    df_filtrado = df_filtrado[
        (df_filtrado["Fecha"] >= rango_fechas[0]) & (df_filtrado["Fecha"] <= rango_fechas[1])
    ]

    orcas_conocidas = df_filtrado["Orca"].unique()
    mapa_grupo = df_filtrado.drop_duplicates("Orca").set_index("Orca")["Grupo"].to_dict()

    df_avistajes = df_filtrado[["Fecha", "Lugar", "Orcas"]].drop_duplicates()
    parejas = []
    for orcas_str in df_avistajes["Orcas"]:
        orcas_list = [o.strip() for o in orcas_str.split(",")]
        orcas_validas = [o for o in orcas_list if o in orcas_conocidas]
        if len(orcas_validas) > 1:
            parejas.extend(itertools.combinations(sorted(orcas_validas), 2))

    conteo_parejas = Counter(parejas)

    PESO_MINIMO = 2

    st.subheader(f"Grafo de orcas avistadas juntas")

    G = nx.Graph()
    for (o1, o2), peso in conteo_parejas.items():
        if peso >= PESO_MINIMO:
            G.add_edge(o1, o2, weight=peso)

    pos = nx.spring_layout(G, k=0.7, seed=42)

    colores_grupos = {}
    palette = px.colors.qualitative.Set3 + px.colors.qualitative.Pastel
    grupos_unicos = sorted(set(map(str, mapa_grupo.values())))
    for i, grupo in enumerate(grupos_unicos):
        rgb = palette[i % len(palette)].replace("rgb(", "").replace(")", "").split(",")
        hex_color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
        colores_grupos[grupo] = hex_color

    colores_nodos = []
    tamaños_nodos = []
    for nodo in G.nodes:
        grupo = mapa_grupo.get(nodo, "Desconocido")
        color = colores_grupos.get(grupo, "#999999")
        colores_nodos.append(color)
        conexiones = list(G.neighbors(nodo))
        peso_total = sum(G[nodo][vecino]['weight'] for vecino in conexiones)
        tamaño = min(100 + peso_total * 30, 1000)
        tamaños_nodos.append(tamaño)

    fig, ax = plt.subplots(figsize=(14, 12))
    nx.draw_networkx_nodes(G, pos, node_color=colores_nodos, node_size=tamaños_nodos, alpha=0.9, ax=ax)

    pesos = [G[u][v]['weight'] for u, v in G.edges]
    anchos = [0.5 + w * 0.8 for w in pesos]
    opacidades = [0.2 + min(w / max(pesos), 1) * 0.5 for w in pesos]
    for (u, v), ancho, alpha in zip(G.edges, anchos, opacidades):
        nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], width=ancho, alpha=alpha, edge_color='black', ax=ax)

    for nodo, (x, y) in pos.items():
        ax.text(x, y, nodo, fontsize=10, fontweight='bold', ha='center', va='center',
                bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.15', alpha=0.8))

    handles = [plt.Line2D([0], [0], marker='o', color='w',
                          label=grupo,
                          markerfacecolor=color,
                          markersize=10)
               for grupo, color in colores_grupos.items()]
    ax.legend(handles=handles, title="Grupos", loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=9)
    fig.subplots_adjust(right=0.80)

    ax.set_title("Orcas avistadas juntas", fontsize=14)
    ax.axis("off")
    st.pyplot(fig)
