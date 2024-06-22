from shiny import App, render, ui, reactive
import plotly.graph_objects as go
from shinywidgets import output_widget, render_widget
from pathlib import Path
import pandas as pd
from shiny.types import ImgData
from src.functions import serie_tiempo_empresa, mapa_floresta, extraer_coordenada

app_ui = ui.page_fluid(
    ui.include_css(
        Path(__file__).parent / "styles.css"
    ),
    ui.panel_title("Análisis de Comentarios"),
    ui.layout_column_wrap(
        1,  # Ensure full-width column for the inputs
        ui.input_selectize('categoria', 'Dataframe', ['Hoteles', 'Restaurantes', 'Bares']),
        ui.input_selectize('nombre_empresa', 'Nombre', [])
    ),
    ui.layout_column_wrap(
        1 / 2,  # Two columns for the output cards
        ui.card(
            ui.output_ui("mapa")
        ),
        ui.card(
            output_widget("plot_series_tiempo")
        )
    ),
    ui.div(
        ui.div(
            ui.img(src="https://i.ibb.co/DDZwpbX/digital-mind-only-logo.png", 
                   #https://i.ibb.co/wR2SQ18/digital-mind.png
                style="width: 100px; height: auto; margin-right: 20px;"),
            ui.div(
                ui.h3("Digital Mind"),
                ui.p("© 2024 Digital Mind. Todos los derechos reservados."),
                style="display: inline-block; vertical-align: middle;"
            ),
            style="display: flex; align-items: center; justify-content: center;"
        ),
        style="text-align: center; padding: 20px; background-color: #f8f9fa;"
    )   
)

def server(input, output, session):
    @reactive.Effect
    def _():
        if input.categoria():
            if input.categoria() == 'Hoteles':
                df = pd.read_csv('data/comentarios_hoteles.csv')
            elif input.categoria() == 'Restaurantes':
                df = pd.read_csv('data/comentarios_restaurante.csv')
            elif input.categoria() == 'Bares':
                df = pd.read_csv('data/comentarios_bares.csv')
            ui.update_selectize('nombre_empresa', choices=list(df['Nombre'].unique()))

    @output
    @render.ui
    def mapa():
        if input.categoria():
            if input.categoria() == 'Hoteles':
                df = pd.read_csv('data/comentarios_hoteles.csv')
            elif input.categoria() == 'Restaurantes':
                df = pd.read_csv('data/comentarios_restaurante.csv')
            elif input.categoria() == 'Bares':
                df = pd.read_csv('data/comentarios_bares.csv')
            
            coord = extraer_coordenada(df, input.nombre_empresa())
            return mapa_floresta(coord=coord, nombre=input.nombre_empresa())

    @output
    @render_widget
    def plot_series_tiempo():
        if input.categoria():
            if input.categoria() == 'Hoteles':
                df = pd.read_csv('data/comentarios_hoteles.csv')
            elif input.categoria() == 'Restaurantes':
                df = pd.read_csv('data/comentarios_restaurante.csv')
            elif input.categoria() == 'Bares':
                df = pd.read_csv('data/comentarios_bares.csv')
                
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


app = App(app_ui, server)
