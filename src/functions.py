from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import MiniMap

def texto_a_fecha(texto):
    hoy = datetime.now()
    palabras = texto.split()
    
    if len(palabras) < 2:
        return hoy.strftime('%m/%d/%Y')
    
    cantidad = palabras[1]
    unidad = palabras[2]
    
    if cantidad == 'un' or cantidad == 'una':
        cantidad = 1
    else:
        try:
            cantidad = int(cantidad)
        except ValueError:
            return hoy.strftime('%m/%d/%Y')
    
    if 'año' in unidad:
        return (hoy - timedelta(days=cantidad*365)).strftime('%m/%d/%Y')
    elif 'mes' in unidad:
        return (hoy - timedelta(days=cantidad*30)).strftime('%m/%d/%Y')
    elif 'semana' in unidad:
        return (hoy - timedelta(weeks=cantidad)).strftime('%m/%d/%Y')
    else:
        return hoy.strftime('%m/%d/%Y')
    

def dataframe_series_tiempo(df):
    # Convertir la columna Fecha_numero a datetime si aún no lo es
    df['Fecha_numero'] = pd.to_datetime(df['Fecha_numero'])
    # Crear una columna de año-mes
    df['Año-Mes'] = df['Fecha_numero'].dt.to_period('M')
    # Crear el nuevo DataFrame con el conteo
    df_conteo = df.groupby(['Nombre', 'Año-Mes', 'Calificación']).size().unstack(fill_value=0)
    # Renombrar las columnas
    df_conteo.columns = ['Malos', 'Neutros', 'Buenos']
    # Resetear el índice para tener Nombre y Año-Mes como columnas
    df_conteo = df_conteo.reset_index()
    # Convertir Año-Mes de nuevo a datetime para facilitar el manejo posterior
    df_conteo['Fecha'] = df_conteo['Año-Mes'].dt.to_timestamp()
    # Eliminar la columna Año-Mes ya que ahora tenemos Fecha
    df_conteo = df_conteo.drop('Año-Mes', axis=1)
    return df_conteo


def serie_tiempo_empresa(df, nombre_empresa):
    df_conteo = dataframe_series_tiempo(df)
    # Filtrar el DataFrame para la empresa específica
    df_empresa = df_conteo[df_conteo['Nombre'] == nombre_empresa]
    # Establecer la fecha como índice
    df_empresa = df_empresa.set_index('Fecha')
    # Seleccionar solo las columnas de interés
    series = df_empresa[['Buenos', 'Neutros', 'Malos']]
    return series


def graficar_serie_tiempo(df, nombre_empresa):
    series = serie_tiempo_empresa(df, nombre_empresa)
    fig = go.Figure()

    # Añadir las series de tiempo al gráfico
    for column in series.columns:
        fig.add_trace(go.Scatter(x=series.index, y=series[column], mode='lines', name=column))
    
    # Configurar el layout del gráfico
    fig.update_layout(
        title=f"Serie de tiempo de comentarios para {nombre_empresa}",
        xaxis_title='Fecha',
        yaxis_title='Número de comentarios',
        template='plotly',
        hovermode='x unified'
    )
    

def mapa_floresta(coord = [-0.2086949, -78.4854354], nombre= 'Pollos Asados'):
    popuptext = f'<b>{nombre}</b>'
    floresta = folium.Map(location = coord, zoom_start=18)
    folium.Marker(location= coord, popup= popuptext ).add_to(floresta)
    folium.Circle(location= coord, color = 'purple', fill_color = 'red', radius = 10, weight = 4, fill_opacity = 0.5, tooltip = f'{nombre}').add_to(floresta)
    #minimap = MiniMap()
    #floresta.add_child(minimap)
    return floresta

def extraer_coordenada(df, nombre):
    df = df.copy()
    
    df['Nombre'] = df['Nombre'].str.lower().str.strip()
    nombre = nombre.lower().strip()
    
    if nombre not in df['Nombre'].values:
        from difflib import get_close_matches
        nombres = df['Nombre'].unique()
        coincidencias = get_close_matches(nombre, nombres, n=1, cutoff=0.6)
        if coincidencias:
            nombre = coincidencias[0]
        else:
            raise ValueError(f"No se encontró ninguna coincidencia para '{nombre}'")

    df_filtrado = df[df['Nombre'] == nombre]
    
    if df_filtrado.empty:
        raise ValueError(f"No hay datos para '{nombre}'")
    
    latitud = df_filtrado['Latitud'].iloc[0]
    longitud = df_filtrado['Longitud'].iloc[0]
    
    return [latitud, longitud]


