from shiny import App, render, ui, reactive
import plotly.graph_objects as go
from shinywidgets import output_widget, render_widget
from pathlib import Path
import pandas as pd
from src.functions import serie_tiempo_empresa, mapa_floresta
app_ui = ui.page_fluid(
    ui.include_css(
        Path(__file__).parent / "styles.css"  
    ),    
    ui.div(
        ui.h2("Análisis de Comentarios".upper()).add_class("panel-title")
    ),
    ui.div(
        ui.layout_column_wrap(
            1/2,  
            ui.input_selectize('categoria', 'CATEGORIAS', ['Hoteles', 'Restaurantes', 'Bares']),
            ui.input_selectize('nombre_empresa', 'NOMBRE', []),
        ),
        ui.input_checkbox("toggle", "Mostrar Total", value=False),
        ui.layout_column_wrap(
            1 / 2,
            ui.card(
                ui.output_ui("mapa_total")  
            ),
            ui.card(
                output_widget("plot_series_tiempo")
            )
        ),

    ).add_class("main-container"),
    
    ui.div(
        ui.div(
            ui.img(src="https://i.ibb.co/DDZwpbX/digital-mind-only-logo.png",
                style="width: 100px; height: auto; margin-right: 20px;"),
            ui.div(
                ui.h3("Digital Mind").add_style('color: #f5f5f5;'),
                ui.p("© 2024 Digital Mind. Todos los derechos reservados.").add_style('color: #f5f5f5;'),
            ),
            style="display: flex; align-items: center; justify-content: center;"
        ),
        style="text-align: center; padding: 20px; background-color: #373739;"
    )
)   

# Server 
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
    def mapa_total():
        if input.categoria() == 'Hoteles':
            df = pd.read_csv('data/comentarios_hoteles.csv')
        elif input.categoria() == 'Restaurantes':
            df = pd.read_csv('data/comentarios_restaurante.csv')
        elif input.categoria() == 'Bares':
            df = pd.read_csv('data/comentarios_bares.csv')
  
        return mapa_floresta(df, nombre=input.nombre_empresa(), total = input.toggle())

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