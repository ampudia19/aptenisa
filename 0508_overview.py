import streamlit as st

url = "https://www.example.com"
# st.components.v1.html(html=f'<iframe src="{url}" width=1200 height=800></iframe>', width=1200, height=800, scrolling=True)

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import pydeck as pdk

st.set_page_config(layout="wide")

import altair as alt
import pandas as pd

def create_histogram(df, y_title, all_ecosystems):

    # Calculate the number of firms and breakdown by ecosystem
    ecosystem_counts = df["ecosystem"].value_counts()
    ecosystem_counts_df = pd.DataFrame(ecosystem_counts).reset_index()
    ecosystem_counts_df.columns = ["ecosystem", y_title]

    # Add missing ecosystems with zero observations
    ecosystem_counts_df = ecosystem_counts_df.set_index("ecosystem").reindex(all_ecosystems).fillna(0).reset_index()

    # Group by ecosystem and join project names
    project_names_by_ecosystem = (
        df.groupby("ecosystem")["project_name"]
        .apply(lambda x: ", ".join(x))
        .reset_index()
    )

    # Merge ecosystem_counts_df and project_names_by_ecosystem
    ecosystem_counts_df = ecosystem_counts_df.merge(
        project_names_by_ecosystem, on="ecosystem", how="left"
    )

    sort_order = sorted(list(ecosystem_counts_df["ecosystem"].unique()), key=lambda x: int(x.split('.')[0]))
    # Create a simple histogram with stacked bars and tooltips
    histogram = (
        alt.Chart(ecosystem_counts_df)
        .mark_bar()
        .encode(
            x=alt.X("ecosystem:N", title="ecosystem", sort=sort_order, axis=alt.Axis(labels=False)),
            y=alt.Y(f"{y_title}:Q", title=y_title, scale=alt.Scale(domain=[0, 5], nice=True)),
            color=alt.Color("ecosystem:N", legend=None),
            tooltip=["ecosystem", y_title, "project_name"],
            order=alt.Order(f"{y_title}:Q", sort="descending"),
        )
    ).properties(
                height=150,
            )

    # Display the histogram
    st.altair_chart(histogram, use_container_width=True)


# Function to apply custom CSS
def apply_custom_css(css):
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Set the DataFrame column widths
custom_css = """
table.dataframe {
    table-layout: fixed;
    width: 100%;
}
table.dataframe th, table.dataframe td {
    width: 33%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
"""

apply_custom_css(custom_css)

# Load the data from the CSV file
@st.cache_data()
def load_data():
    data = pd.read_csv("aptenisa_first_batch_preprocessed.csv")
    return data

data = load_data()
filtered_data = None
# Title and introduction
st.title("Start-up Dashboard")
st.write("This dashboard displays various graphs, plots, and tables for a group of start-ups that participated in APTEnisa Launch.")

# Sidebar filters
st.sidebar.header("Filters")

# Set revenue column to interpolated
interpolate_switch = st.sidebar.checkbox("Interpolate revenue column?")

if interpolate_switch:
    data["revenue"] = data["last_3_months_revenue_interpolated"]
    data["clients"] = data["last_3_months_avg_clients_interpolated"]
else:
    # data["revenue"] = data["last_3_months_revenue_interpolated"]
    # data["clients"] = data["last_3_months_avg_clients_interpolated"]
    data["revenue"] = data["last_3_months_revenue"]
    data["clients"] = data["last_3_months_avg_clients"]

# Filter by tech hub
tech_hub_filter = st.sidebar.selectbox(
    "Select a tech hub:",
    options=["All"] + sorted(list(data["ecosystem"].unique()), key=lambda x: int(x.split('.')[0])),
    index=0
)

# Filter by whether the business has been set up
setup_filter = st.sidebar.selectbox(
    "Has the business been set up?",
    options=["All", "Yes", "No"],
    index=0
)

# FIlter whether business has attempts to raise funding
binary_funding_filter = st.sidebar.selectbox(
    "Has the business attempted to raise funding?",
    options=["All", "Yes", "No"],
    index=0
)

# create all ecosystems
all_ecosystems = sorted(list(data["ecosystem"].unique()), key=lambda x: int(x.split('.')[0]))

data["company_established_date"] = pd.to_datetime(data["company_established_date"], errors="coerce")
min_date = data['company_established_date'].min().date()
max_date = data['company_established_date'].max().date()
# Create date range slider
selected_date_range = st.sidebar.date_input(
    "Company established between dates:",
    [min_date, max_date]
)
# Filter by revenue
revenue_filter = st.sidebar.slider(
    "Revenue generated in the last 3 months (in Euros):",
    min_value=0,
    max_value=int(data["revenue"].max()),
    value=(0,int(data["revenue"].max())),
    step=1000
)

# Filter by funding rounds
funding_filter = st.sidebar.slider(
    "Amount of funding raised:",
    min_value=0,
    max_value=int(data["funding_rounds_capital_raised"].max()),#int(data["¿En cuántas rondas de financiación se ha presentado?"].max()),
    value=(0,int(data["funding_rounds_capital_raised"].max())),
    step=1
)

# Filter by number of clients
clients_filter = st.sidebar.slider(
    "Number of average clients in the last 3 months:",
    min_value=0,
    max_value=int(data["clients"].max()),#int(data["¿En cuántas rondas de financiación se ha presentado?"].max()),
    value=(0,int(data["clients"].max())),
    step=1
)

overview_tab, business_tab, raw_tab = st.tabs(
    ["Overview", "Business", "Raw data"]
)

# Apply filters to the data
filtered_data = data.copy()
if tech_hub_filter != "All":
    filtered_data = filtered_data[filtered_data["ecosystem"] == tech_hub_filter]

if setup_filter != "All":
    yes_no_map = {"Yes": ["Sí", "Ya estaba constituida"], "No": ["No"]}
    filtered_data = filtered_data[filtered_data["company_established"].isin(yes_no_map[setup_filter])]

if binary_funding_filter != "All":
    # fillnas
    filtered_data["funding_rounds_count"] = filtered_data["funding_rounds_count"].fillna(0) 
    if binary_funding_filter == "Yes":
        filtered_data = filtered_data[filtered_data["funding_rounds_count"] > 0]
    else:
        filtered_data = filtered_data[filtered_data["funding_rounds_count"] == 0]

# fillna with zeros in revenue, clients, capital raised if setup is not "Ya estaba constituida"
if not interpolate_switch:
    filtered_data.loc[filtered_data["company_established"] != "Ya estaba constituida", ["revenue", "clients", "funding_rounds_capital_raised"]] = filtered_data.loc[filtered_data["company_established"] != "Ya estaba constituida", ["revenue", "clients", "funding_rounds_capital_raised"]].fillna(0)
else:
    filtered_data.loc[
        filtered_data["company_established"] != "tmp", 
        ["revenue", "clients", "funding_rounds_capital_raised"]
    ] = filtered_data.loc[
        filtered_data["company_established"] != "tmp", 
        ["revenue", "clients", "funding_rounds_capital_raised"]
    ].fillna(0)

filtered_data = filtered_data[(filtered_data["revenue"] >= revenue_filter[0]) & (filtered_data["revenue"] <= revenue_filter[1])]
filtered_data = filtered_data[(filtered_data["funding_rounds_capital_raised"] >= funding_filter[0]) & (filtered_data["funding_rounds_capital_raised"] <= funding_filter[1])]
filtered_data = filtered_data[(filtered_data["clients"] >= clients_filter[0]) & (filtered_data["clients"] <= clients_filter[1])]

st.sidebar.write("Number of start-ups:", len(filtered_data))

# Create dataframe with number of start-ups by ecosystem and write in sidebar
ecosystem_counts = filtered_data["ecosystem"].value_counts()
ecosystem_counts_df = pd.DataFrame(ecosystem_counts).reset_index()
ecosystem_counts_df.columns = ["ecosystem", "Number of start-ups"]
st.sidebar.table(ecosystem_counts_df)

with overview_tab:
    summary_subtab, correlations_subtab, scatterplots_subtab = st.tabs(
        ["Summary", "Correlations", "Scatterplots"]
    )

    with summary_subtab:

        # Calculate statistics
        total_firms = len(filtered_data)
        firms_operating = len(filtered_data[filtered_data["company_established"] != "No"])
        firms_not_operating = total_firms - firms_operating
        female_cofounders = len(filtered_data[filtered_data["cofounders_female"] > 0])
        firms_with_funding_rounds = len(filtered_data[filtered_data["funding_rounds"] == "Sí"])
        firms_with_accelerator_support = len(filtered_data[filtered_data["other_accelerator"] == "Sí"])

        col1, col2 = st.columns(2)
        with col1:
            # Display statistics
            # st.markdown(f"**Total number of firms:** {total_firms}")
            st.markdown(f"<h3 style='color: #4CAF50; font-family: Arial;'>Total number of firms: <span style='color: #1A237E;'>{total_firms}</span></h3>", unsafe_allow_html=True)
            create_histogram(filtered_data, "Number of firms", all_ecosystems)

            st.markdown(f"<h3 style='color: #4CAF50; font-family: Arial;'>Firms operating: <span style='color: #1A237E;'>{firms_operating} ({firms_operating / total_firms * 100:.1f}%)</span></h3>", unsafe_allow_html=True)
            operating_firms = filtered_data[filtered_data["company_established"] != "No"]
            create_histogram(operating_firms, "Number of operating firms", all_ecosystems)

            st.markdown(f"<h3 style='color: #4CAF50; font-family: Arial;'>Firms not operating: <span style='color: #1A237E;'>{firms_not_operating} ({firms_not_operating / total_firms * 100:.1f}%)</span></h3>", unsafe_allow_html=True)
            not_operating_firms = filtered_data[filtered_data["company_established"] == "No"]
            create_histogram(not_operating_firms, "Number of firms not operating", all_ecosystems)


            st.markdown(f"<h3 style='color: #4CAF50; font-family: Arial;'>Firms with female cofounders: <span style='color: #1A237E;'>{female_cofounders} ({female_cofounders / total_firms * 100:.1f}%)</span></h3>", unsafe_allow_html=True)
            female_cofounders_firms = filtered_data[filtered_data["cofounders_female"] > 0]
            create_histogram(female_cofounders_firms, "Number of firms", all_ecosystems)
            
        with col2:
            import streamlit as st
            import pandas as pd
            import numpy as np

            png = "https://cdn-icons-png.flaticon.com/512/1087/1087815.png"
            icon_data = {
                # Icon from Wikimedia
                "url": png,
                "width": 480,
                "height": 480,
                "anchorY": 20,
            }
            filtered_plot = filtered_data.dropna(subset=["lat", "lon", "project_name", "revenue", "clients"])
            filtered_plot["icon_data"] = filtered_plot.apply(lambda _: icon_data, axis=1)
            filtered_plot = filtered_plot[["lat", "lon", "project_name", "revenue", "clients", "icon_data"]]
            
            st.pydeck_chart(pdk.Deck(
                map_style=None,
                initial_view_state=pdk.ViewState(
                    latitude=39.52,
                    longitude=-3.5,
                    zoom=5,
                    pitch=50,
                    height=900
                ),
                layers=[
                    pdk.Layer(
                    type='IconLayer',
                    data=filtered_plot,
                    get_position='[lon, lat]',
                    get_icon='icon_data',
                    get_size=3,
                    size_scale=15,
                    pickable=True,
                    )
                ],
                    tooltip={
                        "html": "<div style='font-family: Arial, sans-serif; font-size: 12px; color: #333333;'><b>Project:</b> {project_name}<br/><b>Revenue:</b> {revenue}<br/><b>Clients:</b> {clients}</div>",
                        "style": {"backgroundColor": "#D8D8D8", "color": "#f5821f", "border": "1px solid #808080", "padding": "5px"},
                    },
            ))

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<h3 style='color: #4CAF50; font-family: Arial;'>Firms that have participated in funding rounds: <span style='color: #1A237E;'>{firms_with_funding_rounds} ({firms_with_funding_rounds / total_firms * 100:.1f}%)</span></h3>", unsafe_allow_html=True)
            funding_firms = filtered_data[filtered_data["funding_rounds"] == "Sí"]
            create_histogram(funding_firms, "Number of firms", all_ecosystems)

            st.markdown(f"<h3 style='color: #4CAF50; font-family: Arial;'>Firms with other accelerator support: <span style='color: #1A237E;'>{firms_with_accelerator_support} ({firms_with_accelerator_support / total_firms * 100:.1f}%)</span></h3>", unsafe_allow_html=True)
            accelerator_firms = filtered_data[filtered_data["other_accelerator"] == "Sí"]
            create_histogram(accelerator_firms, "Number of firms", all_ecosystems)

        with col2:
            # write dataframe with reasons why some firms haven't participated in funding rounds
            reasons = filtered_data[filtered_data["funding_rounds"] == "No"]
            st.dataframe(reasons[["project_name", "no_funding_rounds_reason"]].dropna(), height=250)

            st.dataframe(accelerator_firms[["project_name", "other_accelerator_names"]].dropna(), height=250)





    with correlations_subtab:
        col1, col2 = st.columns(2)
        with col1:
            # Select relevant columns for correlation
            columns_to_correlate = ['revenue', 'clients', 'employees_at_start', 'employees_at_end', 'cofounders_female',
                                    'employees_hired_last_3_months', 'employees_left_last_3_months',
                                    'funding_rounds_count', 'funding_rounds_capital_raised', "other_accelerator_count", 'technology_count', 'technology_lb_cost']

            # Calculate correlation matrix
            corr_matrix = data[columns_to_correlate].corr()

            # Convert the correlation matrix to long format
            corr_long = corr_matrix.reset_index().melt(id_vars='index', var_name='column', value_name='correlation')

            # round correlation to two digits
            corr_long['correlation'] = corr_long['correlation'].round(2)

            # Create title and subtitle
            chart_title = alt.TitleParams(
                'Correlation Heatmap',
                subtitle=[" ".join(['Correlation between different variables for start-ups in', tech_hub_filter, 'tech hub'])],
            )
            # Create Altair heatmap
            heatmap = alt.Chart(corr_long, title=chart_title).mark_rect(stroke='black', strokeWidth=1).encode(
                x=alt.X('index:O', title=None, axis=alt.Axis(labelAngle=-90)),
                y=alt.Y('column:O', title=None),
                color=alt.Color('correlation:Q', scale=alt.Scale(domain=(-1, 1), range=['#d7191c', '#ffffbf', '#2c7bb6'])),
                tooltip=['index', 'column', 'correlation']
            ).properties(
                width=600,
                height=600,
            )

            st.altair_chart(heatmap, use_container_width=False)

        with col2:
            # Create histogram for last 3 months' revenue
            histogram = alt.Chart(filtered_data).mark_bar(opacity=0.7).encode(
                alt.X("revenue:Q", bin=alt.Bin(maxbins=50), title="Last 3 Months' Revenue"),
                alt.Y("count()", title="Number of Start-ups"),
                alt.Color("ecosystem:N", legend=alt.Legend(title="ecosystem")),
                tooltip=["project_name", "ecosystem", "count()"]
            ).properties(
                width=600,
                height=300,
                title="Histogram of Last 3 Months' Revenue by tech hub"
            )

            st.altair_chart(histogram, use_container_width=True)

            # Create histogram for last 3 months' revenue
            histogram = alt.Chart(filtered_data).mark_bar(opacity=0.7).encode(
                alt.X("clients:Q", bin=alt.Bin(maxbins=50), title="Number of clients"),
                alt.Y("count()", title="Number of Start-ups"),
                alt.Color("ecosystem:N", legend=alt.Legend(title="ecosystem")),
                tooltip=["project_name", "ecosystem", "count()"]
            ).properties(
                width=600,
                height=300,
                title="Histogram of Last 3 Months' number of clients by tech hub"
            )
            st.altair_chart(histogram, use_container_width=True)

    with scatterplots_subtab:
        st.header("Scatter plots")
        col1, col2 = st.columns(2)

        with col1:
            # List of available variables for scatter plot
            variables = ['revenue', 'clients',
                        'employees_at_start', 'employees_at_end', 'cofounders_female',
                        'employees_hired_last_3_months', 'employees_left_last_3_months',
                        'funding_rounds_count', 'funding_rounds_capital_raised']

            # Create dropdown selectors for x and y variables
            x_var = st.selectbox("Select X variable:", variables, index=0)
            y_var = st.selectbox("Select Y variable:", variables, index=1)

            # Jitter scale
            jitter_scale = 0.05

            # Create Altair scatter plot with jitter
            scatter_plot = alt.Chart(filtered_data).transform_calculate(
                jittered_x=f'datum.{x_var} + {jitter_scale}*random()',
                jittered_y=f'datum.{y_var} + {jitter_scale}*random()'
            ).mark_circle(size=60).encode(
                x=alt.X("jittered_x:Q", title=x_var),
                y=alt.Y("jittered_y:Q", title=y_var),
                color=alt.Color("ecosystem:N", legend=None),
                tooltip=["project_name", "ecosystem"]
            ).properties(
                width=600,
                height=400,
                title=f"Scatter Plot: {x_var} vs {y_var}"
            )

            st.altair_chart(scatter_plot, use_container_width=True)

        with col2:
            # List of available variables for scatter plot
            variables = ['revenue', 'clients',
                        'employees_at_start', 'employees_at_end', 'cofounders_female',
                        'employees_hired_last_3_months', 'employees_left_last_3_months',
                        'funding_rounds_count', 'funding_rounds_capital_raised']

            # Create dropdown selectors for x and y variables
            x_var = st.selectbox("Select X variable:", variables, index=2)
            y_var = st.selectbox("Select Y variable:", variables, index=3)

            # Jitter scale
            jitter_scale = 0.05

            # Create Altair scatter plot with jitter
            scatter_plot = alt.Chart(filtered_data).transform_calculate(
                jittered_x=f'datum.{x_var} + {jitter_scale}*random()',
                jittered_y=f'datum.{y_var} + {jitter_scale}*random()'
            ).mark_circle(size=60).encode(
                x=alt.X("jittered_x:Q", title=x_var),
                y=alt.Y("jittered_y:Q", title=y_var),
                color=alt.Color("ecosystem:N", legend=None),
                tooltip=["project_name", "ecosystem"]
            ).properties(
                width=600,
                height=400,
                title=f"Scatter Plot: {x_var} vs {y_var}"
            )

            st.altair_chart(scatter_plot, use_container_width=True)
    
with business_tab:
    select_business = st.selectbox(
        "Select a business:",
        sorted(list(filtered_data["project_name"].unique())),
        index=0
    )

    col1, col2 = st.columns([0.3,0.7])
    with col1:

        firm_data = data[data["project_name"] == select_business]

        # Display the firm's information
        st.markdown(f"## {select_business}")

        st.markdown("### General Information")
        st.markdown(f"- Ecosystem: {firm_data['ecosystem'].values[0]}")
        st.markdown(f"- Website URL: {firm_data['website_url'].values[0]}")
        st.markdown(f"- Company Established: {'Yes' if firm_data['company_established'].values[0] else 'No'}")
        st.markdown(f"- Date Established: {pd.to_datetime(firm_data['company_established_date'].values[0]).date()}")

        st.markdown("### Financials")
        st.markdown(f"- Last 3 months revenue: {firm_data['last_3_months_revenue'].values[0]}")
        st.markdown(f"- Last 12 months revenue: {firm_data['last_12_months_revenue'].values[0]}")

        st.markdown('### Clients')
        st.markdown(f"- Last 3 months clients: {firm_data['last_3_months_avg_clients'].values[0]}")
        st.markdown(f"- Last 12 months clients: {firm_data['last_12_months_avg_clients'].values[0]}")

        st.markdown("### Employees")
        st.markdown(f"- Employees at start: {firm_data['employees_at_start'].values[0]}")
        st.markdown(f"- Employees at end: {firm_data['employees_at_end'].values[0]}")
        st.markdown(f"- Female co-founders: {firm_data['cofounders_female'].values[0]}")

        st.markdown('### Technology')
        st.markdown(f"- Technology count: {firm_data['technology_count'].values[0]}")
        st.markdown(f"- Technology cost: {firm_data['technology_lb_cost'].values[0]}")

        st.markdown("### Funding")
        st.markdown(f"- Funding rounds: {firm_data['funding_rounds_count'].values[0]}")
        st.markdown(f"- Reason for no funding rounds: {firm_data['no_funding_rounds_reason'].values[0]}")
        st.markdown(f"- Capital raised: {firm_data['funding_rounds_capital_raised'].values[0]}")

        st.markdown('### Accelerator')
        st.markdown(f"- Number of Accelerators: {firm_data['other_accelerator_count'].values[0]}")
        st.markdown(f"- Accelerator Names: {firm_data['other_accelerator_names'].values[0]}")

    with col2:
        url = filtered_data[filtered_data["project_name"] == select_business]["website_url"].values[0]
        st.components.v1.html(html=f'<iframe src="{url}" width=920 height=1200></iframe>', width=1200, height=1200, scrolling=True)

# Aggregate/tech hub-specific data
# with park_tab:
#     st.header("Aggregate/Tech Hub-Specific Data")

    # # ecosystem distribution of start-ups
    # st.subheader("ecosystem Distribution of Start-ups")
    # ecosystem_counts = filtered_data["Ecosistema al que pertenece:"].value_counts()
    # st.bar_chart(ecosystem_counts)

    # # Percentage of start-ups with a website
    # st.subheader("Percentage of Start-ups with a Website")
    # # website_counts = filtered_data["¿Tiene su empresa página web?"].apply(lambda x: "With website" if x != "No tiene web" else "Without website").value_counts()
    # st.pie_chart(website_counts)

    # # Start-up legal status
    # st.subheader("Start-up Legal Status")
    # legal_status_counts = filtered_data["¿Ha constituido su empresa?"].value_counts()
    # st.bar_chart(legal_status_counts)

    # # Add more graphs, plots, and tables specific to aggregate/tech hub-specific data
    # # ...

# Raw data
with raw_tab:
    st.header("Raw Data")
    st.dataframe(filtered_data, use_container_width=True)

