from shiny import reactive
from shiny.express import ui, render, input
import plotly.graph_objects as go
from shinywidgets import render_widget
import faicons as fa
from pathlib import Path
import pandas as pd
from shiny.types import ImgData
from src.functions import serie_tiempo_empresa

ui.include_css(
    Path(__file__).parent / "styles.css"
)
ui.page_opts(static_assets=str(Path(__file__).parent))

with ui.sidebar():
    ui.input_selectize('categoria', 'Dataframe', ['Hoteles', 'Restaurantes'])
    ui.input_selectize('nombre_empresa', 'Nombre', [])
    
@reactive.Effect
def _():
    if input.categoria() == 'Hoteles':
        df = pd.read_csv('data/comentarios_hoteles.csv')
        ui.update_selectize('nombre_empresa', choices=list(df['Nombre'].unique()))
    elif input.categoria() == 'Restaurantes':
        df = pd.read_csv('data/comentarios_restaurante.csv')
        ui.update_selectize('nombre_empresa', choices=list(df['Nombre'].unique()))

with ui.card():
    @render_widget
    def plot_series_tiempo():
        if input.categoria() == 'Hoteles':
            df = pd.read_csv('data/comentarios_hoteles.csv')
        elif input.categoria() == 'Restaurantes':
            df = pd.read_csv('data/comentarios_restaurante.csv')
            
        series = serie_tiempo_empresa(df, input.nombre_empresa())
        fig = go.Figure()

        for column in series.columns:
            fig.add_trace(go.Scatter(x=series.index, y=series[column], mode='lines', name=column))

        fig.update_layout(
            title=f"Serie de tiempo de comentarios para {input.nombre_empresa()}",
            xaxis_title='Fecha',
            yaxis_title='Número de comentarios',
            template='plotly',
            hovermode='x unified'
        )
        return fig

def logo_image():
    from pathlib import Path
    dir = Path(__file__).resolve().parent
    img: ImgData = {"src": str(dir / "img/digital_mind.png"), "width": "100px"}
    return img

