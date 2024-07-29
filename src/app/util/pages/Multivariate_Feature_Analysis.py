import streamlit as st

from src.app.util.constants import MultivariatePage
from src.commons.commons import load_config_file, run_itk_snap
from src.commons.commons import read_datasets_from_dict
from src.visualization.scatter_plots import scatter_plot_features
from streamlit_plotly_events import plotly_events

const = MultivariatePage()

# Load configuration and data
config = load_config_file("./src/app/util/config.yml")
datasets_root_path = config.get("datasets_root_path")
data_paths = config.get("features_analysis").get('data_paths')
features = const.mapping_buttons_columns


# Sidebar setup for selecting datasets and variables
def setup_sidebar(data_paths, allowed_features):
    """
    Set up the sidebar with options to select datasets and variables.

    Args:
        data_paths (dict): Dictionary with paths to datasets.
        allowed_features (dict): Dictionary of allowed features for selection.

    Returns:
        tuple: Contains selected datasets, X-axis variable, Y-axis variable, and color-axis variable.
    """
    with st.sidebar:
        st.header("Configuration")

        # Select datasets
        with st.sidebar.expander("Datasets", expanded=True):
            selected_sets = st.multiselect(
                label="Select datasets to visualize:",
                options=data_paths.keys(),
                default=data_paths.keys()
            )

        # Select features for X-axis, Y-axis, and color
        with st.sidebar.expander("Features", expanded=True):
            select_x_axis = st.selectbox(
                label="X-axis variable:",
                options=allowed_features.keys(),
                index=0
            )
            select_y_axis = st.selectbox(
                label="Y-axis variable:",
                options=allowed_features.keys(),
                index=1
            )
            select_color_axis = st.selectbox(
                label="Color-axis variable:",
                options=["Dataset"] + list(allowed_features.keys()),
                index=0
            )

        st.write("[Contact us - MIA group](%s)" % const.mia_url)

        return selected_sets, select_x_axis, select_y_axis, select_color_axis


# Main function for visualization and ITK-SNAP interaction
def main(sets, x_axis, y_axis, color_axis):
    """
    Main function to load datasets, filter data, create scatter plots, and handle ITK-SNAP interaction.

    Args:
        sets (list): List of selected datasets.
        x_axis (str): Selected X-axis variable.
        y_axis (str): Selected Y-axis variable.
        color_axis (str): Selected color-axis variable.
    """
    # Load datasets and combine
    # dfs = [load_csv(path=path).assign(set=name) for name, path in data_paths.items()]
    # concat = pd.concat(dfs)
    concat = read_datasets_from_dict(data_paths)

    # Filter datasets
    concat = concat[concat.set.isin(sets)]

    # Scatter plot visualization
    st.markdown("**Click on a point to visualize it in ITK-SNAP app.**")
    concat.reset_index(drop=True, inplace=True)
    fig = scatter_plot_features(data=concat,
                                x_axis=features.get(x_axis),
                                y_axis=features.get(y_axis),
                                y_label=y_axis,
                                x_label=x_axis,
                                color=features.get(color_axis, "Dataset"),
                                legend_title=color_axis
                                )
    selected_points = plotly_events(fig, click_event=True, override_height=None)

    # retrieving selected ID
    selected_case, st.session_state.selected_case = None, None
    if selected_points:
        point = selected_points[0]
        filtered_set_data = concat[concat.set == concat.set.unique()[point['curveNumber']]]
        selected_case = filtered_set_data.iloc[point['pointIndex']]["ID"]

    # Visualize case in ITK-SNAP
    if selected_case != st.session_state.selected_case:
        st.session_state.selected_case = selected_case
        dataset = concat[concat.ID == selected_case]['set'].unique()[0].lower()
        verification_check = run_itk_snap(datasets_root_path, dataset, selected_case, config.get("labels"))
        if not verification_check:
            st.error('Ups, something went wrong when opening the file in ITK-SNAP', icon="🚨")


def set_page_config():
    st.set_page_config(
        page_title="Multivariate Analysis",
        page_icon=":brain:",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def multivariate():
    # Define page layout
    st.header(const.header)
    st.markdown(const.sub_header)

    # Sidebar setup
    sets, x_axis, y_axis, color_axis = setup_sidebar(data_paths, features)

    # Main functionality
    main(sets, x_axis, y_axis, color_axis)

    # Description
    st.markdown(const.description)
