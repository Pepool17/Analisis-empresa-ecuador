from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
import math

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
    df['Fecha_numero'] = pd.to_datetime(df['Fecha_numero'])
    df['Año-Mes'] = df['Fecha_numero'].dt.to_period('M')
    df_conteo = df.groupby(['Nombre', 'Año-Mes', 'Calificación']).size().unstack(fill_value=0)
    df_conteo.columns = ['Malos', 'Neutros', 'Buenos']
    df_conteo = df_conteo.reset_index()
    df_conteo['Fecha'] = df_conteo['Año-Mes'].dt.to_timestamp()
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


def convertir_coordenadas(arreglo):

    coordenadas = []
    for coord_str in arreglo:
        # Eliminar paréntesis y comillas
        coord_str = coord_str.replace("(", "").replace(")", "").replace("'", "")
        # Separar la latitud y longitud
        lat_str, lon_str = coord_str.split(", ")
        # Convertir a floats
        lat = float(lat_str)
        lon = float(lon_str)
        # Añadir a la lista de coordenadas
        coordenadas.append((lat, lon))
    return coordenadas


def calcular_punto_medio(coordenadas):

    if len(coordenadas) == 0:
        return None
    
    x = 0
    y = 0
    z = 0

    for lat, lon in coordenadas:
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        
        x += math.cos(lat_rad) * math.cos(lon_rad)
        y += math.cos(lat_rad) * math.sin(lon_rad)
        z += math.sin(lat_rad)
    
    total = len(coordenadas)
    x /= total
    y /= total
    z /= total
    
    lon_media = math.atan2(y, x)
    hyp = math.sqrt(x * x + y * y)
    lat_media = math.atan2(z, hyp)
    
    lat_media = math.degrees(lat_media)
    lon_media = math.degrees(lon_media)
    
    return (lat_media, lon_media)

def extraer_info_empresa(df, nombre):
    try:
        df_pivot = df.pivot_table(index='Nombre', values=['Latitud', 'Longitud', 'Dirección', 'Tipo Establecimiento'], aggfunc='first')
        df_empresa = df_pivot.loc[nombre, ['Latitud', 'Longitud', 'Dirección', 'Tipo Establecimiento']]
        df_empresa = df_empresa.fillna('')
        return [[df_empresa['Latitud'], df_empresa['Longitud']], df_empresa['Dirección'], df_empresa['Tipo Establecimiento']]
    except KeyError:
        #print(f'No se encontró la empresa con el nombre {nombre} en el DataFrame.')
        return None
    except Exception as e:
        #print(f'Error inesperado: {e}')
        return None


def mapa_floresta(df, nombre, total):
    def generar_popup(tipo, nombre, coord, dir):
        popup = f'<div style="text-align: center; width: 200px;">'
        if tipo:
            popup += f'<b>{tipo}</b><br>'
        if nombre:
            popup += f'<b>{nombre}</b><br>'
        if coord:
            popup += f'<b>({coord[0]}, {coord[1]})</b><br>'
        if dir:
            popup += f'<b>{dir}</b>'
        popup += '</div>'
        return popup

    if not total:
        info_empresa = extraer_info_empresa(df, nombre)
        if info_empresa is None:
            #print(f"No se pudo obtener la información de la empresa: {nombre}")
            return None

        coord, dir, tipo = info_empresa
        popuptext = generar_popup(tipo, nombre, coord, dir)
        floresta = folium.Map(location=coord, zoom_start=18)
        folium.Marker(location=coord, popup=folium.Popup(popuptext, max_width=300), icon=folium.Icon(color='red')).add_to(floresta)
        folium.Circle(location=coord, color='red', fill_color='red', radius=10, weight=4, fill_opacity=0.5).add_to(floresta)
        return floresta

    try:
        coordenadas = convertir_coordenadas(df['Coordenadas'].unique())
        punto_medio = calcular_punto_medio(coordenadas)
        floresta = folium.Map(location=punto_medio, zoom_start=16)

        for nombres in df['Nombre'].dropna().unique():
            info_empresa = extraer_info_empresa(df, nombres)
            if info_empresa is None:
                #print(f"No se pudo obtener la información de la empresa: {nombres}")
                continue

            coord, dir, tipo = info_empresa
            popuptext = generar_popup(tipo, nombres, coord, dir)

            if nombres == nombre:
                folium.Circle(location=coord, color='red', fill_color='red', radius=12, weight=5, fill_opacity=0.5).add_to(floresta)
                folium.Marker(location=coord, popup=folium.Popup(popuptext, max_width=300), icon=folium.Icon(color='red')).add_to(floresta)
            else:
                folium.Circle(location=coord, color='blue', fill_color='blue', radius=10, weight=4, fill_opacity=0.5).add_to(floresta)
                folium.Marker(location=coord, popup=folium.Popup(popuptext, max_width=300), icon=folium.Icon(color='blue')).add_to(floresta)
        return floresta
    except Exception as e:
        #print(f"Error inesperado: {e}")
        return None