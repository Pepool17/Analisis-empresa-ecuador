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



def generar_nube_bigramas(df, columna_comentarios, columna_calificacion, calificacion, columna_nombre, nombre, num_frecuencias=10):
    df_filtrado = df[(df[columna_calificacion] == calificacion) & (df[columna_nombre] == nombre)]
    comentarios_limpios = df_filtrado[columna_comentarios].apply(clean_text).tolist()
    
    tokenized_comments = [comment.split() for comment in comentarios_limpios]
    bigram = Phrases(tokenized_comments, min_count=5, threshold=100)
    bigram_mod = Phraser(bigram)
    
    bigram_comments = [bigram_mod[comment] for comment in tokenized_comments]
    bigramas = [' '.join(bigrama) for comentario in bigram_comments for bigrama in ngrams(comentario, 2)]
    bigramas_freq = Counter(bigramas)
    
    wordcloud = WordCloud(width=800, height=400, background_color='white', colormap='viridis', collocations=False, max_words=30).generate_from_frequencies(bigramas_freq)
    
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    ax1.imshow(wordcloud, interpolation='bilinear')
    ax1.axis('off')
    
    bigramas_comunes = bigramas_freq.most_common(num_frecuencias)
    bigramas, frecuencias = zip(*bigramas_comunes)
    
    fig2, ax2 = plt.subplots(figsize=(12, 8))
    ax2.barh(bigramas, frecuencias, color='skyblue')
    ax2.set_xlabel('Frecuencia')
    ax2.set_title(f'Top {num_frecuencias} Bigramas más Comunes para {nombre}')
    ax2.invert_yaxis()
    
    return fig1, fig2