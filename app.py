from shiny import App, render, ui, reactive
import plotly.graph_objects as go
from shinywidgets import output_widget, render_widget
from pathlib import Path
import pandas as pd
from src.functions import serie_tiempo_empresa, mapa_floresta, generar_nube_bigramas
import mpld3

app_ui = ui.page_fluid(
    ui.include_css(
        Path(__file__).parent / "styles.css"
    ),
    ui.div(
        ui.h2("Explorando Experiencias de Clientes ".upper()).add_class("panel-title")
    ),
    ui.div(
        ui.layout_column_wrap(
            1 / 2,
            ui.input_selectize('categoria', 'CATEGORIAS', ['Total', 'Hoteles', 'Restaurantes', 'Bares'], width='50%'),
            ui.div(
                ui.output_ui("nombre_empresa_ui", inline=True),
                style="width: 100%;"
            )
        ),
        ui.output_ui("toggle_checkbox"),
        ui.layout_column_wrap(
            1 / 2,
            ui.card(
                ui.output_ui("mapa_total")
            ),
            ui.card(
                output_widget("plot_series_tiempo")
            ),
        ),
        ui.output_ui("caracteristicas_ui_card"),
        ui.input_select('calificacion', 'CALIFICACIÓN', ['Negativo', 'Neutro', 'Positivo'], selected='Negativo'),
        ui.layout_column_wrap(
            1 / 2,
            ui.card(
                ui.output_ui("nube_palabras")
            ),
            ui.card(
                output_widget("grafico_frecuencias")
            )
        ),
        ui.output_ui("grafico_html_card")
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

################## SERVER ####################
def server(input, output, session):

    @reactive.Calc
    def get_dataframe():
        if input.categoria() == 'Total':
            return pd.read_csv('data/comentarios.csv')
        elif input.categoria() == 'Hoteles':
            return pd.read_csv('data/comentarios_hoteles.csv')
        elif input.categoria() == 'Restaurantes':
            return pd.read_csv('data/comentarios_restaurante.csv')
        elif input.categoria() == 'Bares':
            return pd.read_csv('data/comentarios_bares.csv')

    @reactive.Calc
    def get_caracteristicas_bares():
        if input.categoria() == 'Bares':
            return pd.read_csv('data/caracteristicas_bares.csv')
        return pd.DataFrame()
    
    @reactive.Calc 
    def get_caracteristicas_restaurantes():
        if input.categoria() == 'Restaurantes':
            return pd.read_csv('data/caracteristicas_restaurantes.csv')
        return pd.DataFrame()

    @reactive.Calc
    def show_caracteristicas_ui():
        return input.categoria() in ['Bares', 'Restaurantes'] and input.nombre_empresa() != 'Total'

    @reactive.Effect
    @reactive.event(input.categoria)
    def update_empresa_choices():
        if input.categoria() != 'Total':
            df = get_dataframe()
            ui.update_selectize('nombre_empresa', choices=['Total'] + list(df['Nombre'].unique()))

    @output
    @render.ui
    def nombre_empresa_ui():
        if input.categoria() != 'Total':
            return ui.input_selectize('nombre_empresa', 'NOMBRE', [], width="50%")
        else:
            return ui.div()

    @output
    @render.ui
    def mapa_total():
        df = get_dataframe()
        nombre = input.nombre_empresa() if input.categoria() != 'Total' else None
        mostrar_total = input.toggle() if input.categoria() != 'Total' else True
        return mapa_floresta(df, nombre=nombre, total=mostrar_total)

    @reactive.Calc
    def get_time_series():
        df = get_dataframe()
        nombre = input.nombre_empresa() if input.categoria() != 'Total' else 'Total'
        return serie_tiempo_empresa(df, nombre)

    @output
    @render_widget
    def plot_series_tiempo():
        series = get_time_series()
        fig = go.Figure()

        for column in series.columns:
            fig.add_trace(go.Scatter(x=series.index, y=series[column], mode='lines', name=column))

        fig.update_layout(
            title=f"Serie de tiempo de comentarios para {input.nombre_empresa() if input.categoria() != 'Total' else 'Total'}",
            xaxis_title='Fecha',
            yaxis_title='Número de comentarios',
            template='plotly',
            hovermode='x unified'
        )
        return fig

    @output
    @render.ui
    def toggle_checkbox():
        if input.categoria() != 'Total':
            return ui.input_checkbox("toggle", "Mostrar todos los locales.", value=True)
        else:
            return ui.div()

    @output
    @render.ui
    def nube_palabras():
        df = get_dataframe()
        nombre = input.nombre_empresa() if input.categoria() != 'Total' else 'Total'
        calificacion_map = {'Negativo': -1, 'Neutro': 0, 'Positivo': 1}
        calificacion = calificacion_map[input.calificacion()]
        nube_fig, _ = generar_nube_bigramas(df, 'Comentario', 'Calificación', calificacion, 'Nombre', nombre)

        if nube_fig is None:
            return ui.HTML("""
                <div style="display: flex; justify-content: center; align-items: center; height: 100%; min-height: 200px;">
                    <p style="font-size: 24px; font-weight: bold; text-align: center;">
                        No hay suficientes comentarios para crear el gráfico.
                    </p>
                </div>
            """)
        else:
            return ui.HTML(mpld3.fig_to_html(nube_fig))

    @output
    @render_widget
    def grafico_frecuencias():
        df = get_dataframe()
        nombre = input.nombre_empresa() if input.categoria() != 'Total' else 'Total'
        calificacion_map = {'Negativo': -1, 'Neutro': 0, 'Positivo': 1}
        calificacion = calificacion_map[input.calificacion()]
        _, freq_fig = generar_nube_bigramas(df, 'Comentario', 'Calificación', calificacion, 'Nombre', nombre)

        if freq_fig is None:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay suficientes comentarios para crear el gráfico",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        else:
            return freq_fig

    @output
    @render.ui
    def grafico_html():
        categoria = input.categoria().upper()
        calificacion = input.calificacion().upper()

        html_filename = f"LDA_{categoria}_{calificacion}.html"
        html_path = Path(f'html/{html_filename}')

        if html_path.exists():
            with open(html_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            return ui.div(
                ui.HTML(f"<div style='display: flex; justify-content: center;'>{html_content}</div>"),
                ui.input_action_button("toggle_text", "Mostrar/Ocultar Interpretación del Gráfico de Análisis de Temas"),
                ui.output_ui("texto_explicativo")
            )
        else:
            return ui.HTML("<p>El gráfico no está disponible.</p>")

    @output
    @render.ui
    def grafico_html_card():
        if input.categoria() == 'Total' or input.nombre_empresa() != 'Total':
            return ui.div()
        else:
            return ui.card(ui.output_ui("grafico_html"))

    @output
    @render.ui
    def caracteristicas_ui_card():
        if show_caracteristicas_ui():
            return ui.card(ui.output_ui("caracteristicas_ui"))
        else:
            return ui.div()
    
    @output
    @render.ui
    def caracteristicas_ui():
        if input.categoria() == 'Bares' and input.nombre_empresa() != 'Total':
            df = get_caracteristicas_bares()
        elif input.categoria() == 'Restaurantes' and input.nombre_empresa() != 'Total':
            df = get_caracteristicas_restaurantes()
        else:
            return ui.div()

        if not df.empty:
            data = df[df['Nombre'] == input.nombre_empresa()]
            if not data.empty:
                exclude_columns = ['Nombre', 'Latitud', 'Longitud']
                info = data.drop(columns=exclude_columns).dropna(axis=1, how='all').iloc[0].to_dict()
                info = {k: v for k, v in info.items() if pd.notna(v)}
                info_list = ''.join([f"<li><strong>{k}:</strong> {v}</li>" for k, v in info.items()])
                return ui.HTML(f"<ul>{info_list}</ul>")
        return ui.div()

app = App(app_ui, server)
