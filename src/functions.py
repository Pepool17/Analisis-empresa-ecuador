from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
import math
import nltk
from wordcloud import WordCloud
from nltk.util import ngrams
from collections import Counter
import string
import re
from gensim.models import Phrases
from gensim.models.phrases import Phraser
from nltk.corpus import stopwords
import mpld3
import matplotlib.pyplot as plt
import plotly.graph_objects as go

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
    return df_conteo.drop('Año-Mes', axis=1).set_index('Fecha')

def serie_tiempo_empresa(df, nombre_empresa='Total'):
    df_conteo = dataframe_series_tiempo(df)
    if nombre_empresa != 'Total':
        return df_conteo[df_conteo['Nombre'] == nombre_empresa][['Buenos', 'Neutros', 'Malos']]
    return df_conteo.groupby('Fecha')[['Buenos', 'Neutros', 'Malos']].sum()

def convertir_coordenadas(arreglo):
    return [tuple(map(float, coord.strip("()").replace("'", "").split(", "))) for coord in arreglo]


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
        empresa = df[df['Nombre'] == nombre].iloc[0]
        return [[empresa['Latitud'], empresa['Longitud']], empresa['Dirección'], empresa['Tipo Establecimiento']]
    except (IndexError, KeyError):
        return None

def mapa_floresta(df, nombre, total):
    def generar_popup(tipo, nombre, coord, dir):
        return f'<div style="text-align: center; width: 200px;"><b>{tipo}</b><br><b>{nombre}</b><br><b>({coord[0]}, {coord[1]})</b><br><b>{dir}</b></div>'

    if not total and nombre:
        info_empresa = extraer_info_empresa(df, nombre)
        if info_empresa is None:
            return folium.Map(location=[4.60971, -74.08175], zoom_start=13)  # Coordenadas de Bogotá
        coord, dir, tipo = info_empresa
        mapa = folium.Map(location=coord, zoom_start=18)
        folium.Marker(location=coord, popup=folium.Popup(generar_popup(tipo, nombre, coord, dir), max_width=300), 
                      icon=folium.Icon(color='red')).add_to(mapa)
        return mapa

    coordenadas = convertir_coordenadas(df['Coordenadas'].unique())
    punto_medio = calcular_punto_medio(coordenadas)
    mapa = folium.Map(location=punto_medio, zoom_start=16)

    for _, row in df.drop_duplicates('Nombre').iterrows():
        coord = [row['Latitud'], row['Longitud']]
        popuptext = generar_popup(row['Tipo Establecimiento'], row['Nombre'], coord, row['Dirección'])
        color = 'red' if row['Nombre'] == nombre else 'blue'
        folium.Marker(location=coord, popup=folium.Popup(popuptext, max_width=300), 
                      icon=folium.Icon(color=color)).add_to(mapa)

    return mapa

# Funciones para los bigramas
stop_words = stopwords.words('spanish')
stop_words = stop_words + ['ademas', 'dijo', 'dijeron', 'comment', 'found', 'toda', 'veces', 'dieron', 'solo', 'tarde', 'noche']


def clean_text(text):
    if isinstance(text, float):
        return ""
    text = str(text).lower()
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = ' '.join([word for word in text.split() if word not in stop_words])
    return text



def generar_nube_bigramas(df, columna_comentarios, columna_calificacion, calificacion, columna_nombre, nombre='Total', num_frecuencias=10):
    if nombre == 'Total':
        df_filtrado = df[df[columna_calificacion] == calificacion]
    else:
        df_filtrado = df[(df[columna_calificacion] == calificacion) & (df[columna_nombre] == nombre)]
    
    # Limpiar el texto
    comentarios_limpios = df_filtrado[columna_comentarios].apply(clean_text).tolist()
    
    # Verificar si hay suficientes palabras
    if not ' '.join(comentarios_limpios).split():
        return None, None
    
    # Tokenización de los comentarios
    tokenized_comments = [comment.split() for comment in comentarios_limpios]
    
    # Entrenamiento del modelo de bigramas
    bigram = Phrases(tokenized_comments, min_count=5, threshold=100)
    bigram_mod = Phraser(bigram)
    
    # Generación de bigramas
    bigram_comments = [bigram_mod[comment] for comment in tokenized_comments]
    
    # Unir los bigramas para contar las frecuencias
    bigramas = [' '.join(bigrama) for comentario in bigram_comments for bigrama in ngrams(comentario, 2)]
    
    # Contar frecuencia de bigramas
    bigramas_freq = Counter(bigramas)
    
    # Generar la nube de palabras
    wordcloud = WordCloud(width=800, height=400, background_color='white', colormap='viridis', collocations=False, max_words=30).generate_from_frequencies(bigramas_freq)
    
    # Crear la figura de la nube de palabras
    nube_fig, ax = plt.subplots(figsize=(8, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    
    # Ajustar los márgenes de la figura de la nube de palabras
    nube_fig.tight_layout(pad=0.5)
    
    # Crear la figura del gráfico de barras usando Plotly
    bigramas_comunes = bigramas_freq.most_common(num_frecuencias)
    bigramas, frecuencias = zip(*bigramas_comunes)
    
    freq_fig = go.Figure(go.Bar(
        x=frecuencias,
        y=bigramas,
        orientation='h',
        marker_color='skyblue'
    ))
    
    freq_fig.update_layout(
        title=f'Top {num_frecuencias} Bigramas más Comunes para {nombre}',
        xaxis_title='Frecuencia',
        yaxis_title='Bigramas',
        height=500,  # Ajusta esta altura según tus necesidades
        margin=dict(l=10, r=10, t=40, b=10)  # Ajusta los márgenes según tus necesidades
    )
    
    plt.close(nube_fig)
    
    return nube_fig, freq_fig