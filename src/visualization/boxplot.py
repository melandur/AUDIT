import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from src.commons.commons import pretty_string
from src.visualization.constants import Dashboard

constants = Dashboard()


def boxplot(data, x_axis, color_var, x_label=None):
    if x_label is None:
        x_label = f"{pretty_string(x_axis)}"

    # Use a predefined Plotly color palette
    color_palette = constants.discrete_color_palette

    # Map each unique value in color_var to a color from the palette
    unique_values = data[color_var].unique()
    color_map = {value: color_palette[i % len(color_palette)] for i, value in enumerate(unique_values)}

    # Collect data for each color category
    hist_data = []
    group_labels = []
    colors = []
    ids = []

    for color_value in unique_values:
        filtered_data = data[data[color_var] == color_value].sort_values(by="ID")[x_axis]
        ids_data = data[data[color_var] == color_value].sort_values(by="ID")["ID"]
        hist_data.append(filtered_data[~np.isnan(filtered_data)])  # removing nan values
        ids.append(ids_data[~np.isnan(filtered_data)])  # removing nan values
        group_labels.append(color_value)
        colors.append(color_map[color_value])

    fig = go.Figure()
    for x, c, n, id in zip(hist_data, colors, group_labels, ids):
        fig.add_trace(go.Box(
            x=x,
            customdata=id,
            name=n,
            jitter=0.3,
            pointpos=-1.8,
            boxpoints='all',  # represent all points
            marker_color=c,
            line_color=c,
            hovertemplate='ID: %{customdata}<br>' + pretty_string(x_axis) + ': %{x:,.2f}'  # Customize hover information
        ))

    # Update layout
    fig.update_layout(
        template='simple_white',
        height=500,
        width=1000,
        margin=dict(t=50),
        showlegend=True,
        xaxis_title=x_label,
        yaxis_title='',
        legend_title="Dataset",
        legend=dict(
            yanchor="top",
            xanchor="right",
        )
    )

    return fig


def models_performance_boxplot(data, points="outliers", aggregated=None):
    facet_row, height = None, 500
    if not aggregated:
        facet_row , height = 'region', 800

    # color palette
    color_palette = constants.discrete_color_palette

    fig = px.box(data, x='metric', y='score', color='model', facet_row=facet_row, points=points,
                 custom_data=["model", "metric", "score"],
                 title='Distribution of for each metric by model and region',
                 color_discrete_sequence=color_palette)

    # Update the layout for better visualization
    fig.update_xaxes(showline=False)
    fig.update_yaxes(title_text='')
    fig.update_layout(template='simple_white',
                      height=height,
                      width=1000,
                      margin=dict(t=120),
                      showlegend=True,
                      xaxis_title='Metric',
                      boxmode='group',  # group together boxes of the same metric
                      legend_title='Model',
                      legend=dict(
                          orientation="h",
                          yanchor="bottom",
                          y=1.02,
                          xanchor="left",
                          x=0,
                          # bgcolor="White",
                          # bordercolor="Black",
                          # borderwidth=1
                      )
                      )

    fig.update_traces(
                      hovertemplate='Model: %{customdata[0]}<br>'
                                    '%{customdata[1]}: %{customdata[2]:.3f}')

    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    return fig