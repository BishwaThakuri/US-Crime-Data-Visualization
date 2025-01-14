import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc

# pip install plotly==5.15.0 dash==2.11.1 dash-bootstrap-components

# Load datasets
df_main = pd.read_csv('data/filtered_data.csv')
df_valid = pd.read_csv('data/valid_victim_data.csv')

# Convert date columns to datetime
df_main['DATE OCC'] = pd.to_datetime(df_main['DATE OCC'])
df_valid['DATE OCC'] = pd.to_datetime(df_valid['DATE OCC'])

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# App layout
app.layout = dbc.Container([
    html.H1("Violations Dashboard", className="text-center my-4"),

    # Dataset selection dropdown
    dbc.Row([
        dbc.Col([
            html.Label("Select Dataset:"),
            dcc.Dropdown(
                id='dataset-dropdown',
                options=[
                    {'label': 'Filtered Data', 'value': 'filtered_data'},
                    {'label': 'Valid Victim Data', 'value': 'valid_victim_data'}
                ],
                value='filtered_data',  # default value
                className="mb-3"
            )
        ], width=4),
    ], className="mb-4"),

    # Overview section with total violations, most common status, and top category
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Total Violations", className="card-title text-center"),
                    html.H2(id='total-violations', className="text-center")
                ])
            ])
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Most Common Status", className="card-title text-center"),
                    html.H2(id='most-common-status', className="text-center")
                ])
            ])
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Top Category", className="card-title text-center"),
                    html.H2(id='top-category', className="text-center")
                ])
            ])
        ], width=4),
    ], className="mb-4"),

    # Date range selector
    dbc.Row([
        dbc.Col([
            html.Label("Select Date Range:"),
            dcc.DatePickerRange(
                id='date-picker',
                display_format='YYYY-MM-DD',
                className="mb-3"
            ),
            dcc.Graph(id='trend-graph')
        ], width=12),
    ], className="mb-4"),

    # Violation Status Distribution Bar Chart
    dbc.Row([
        dbc.Col([
            html.H3("Violation Status Distribution", className="text-center"),
            dcc.Graph(id='status-bar-chart')
        ], width=12),
    ], className="mb-4"),

    # Violation Locations Map
    dbc.Row([
        dbc.Col([
            html.H3("Violation Locations", className="text-center"),
            dcc.Graph(id='location-map')
        ], width=12),
    ], className="mb-4"),

    # Crimes by Age Group Pie Chart
    dbc.Row([
        dbc.Col([
            html.H3("Crimes by Age Group", className="text-center"),
            dcc.Graph(id='age-group-pie-chart')
        ], width=6),
    ], className="mb-4"),
], fluid=True)

# Callback for updating overview information based on selected dataset
@app.callback(
    [
        Output('total-violations', 'children'),
        Output('most-common-status', 'children'),
        Output('top-category', 'children'),
        Output('date-picker', 'start_date'),
        Output('date-picker', 'end_date')
    ],
    Input('dataset-dropdown', 'value')
)
def update_overview(selected_dataset):
    # Select the appropriate dataset based on dropdown value
    dataset = df_main if selected_dataset == 'filtered_data' else df_valid

    total_violations = len(dataset)
    most_common_status = dataset['Status'].value_counts().idxmax()
    top_category = dataset['Crm Cd Desc'].value_counts().idxmax()
    start_date = dataset['DATE OCC'].min().date()
    end_date = dataset['DATE OCC'].max().date()

    return total_violations, most_common_status, top_category, start_date, end_date

# Callback for updating the trend graph based on date range
@app.callback(
    Output('trend-graph', 'figure'),
    Input('dataset-dropdown', 'value'),
    Input('date-picker', 'start_date'),
    Input('date-picker', 'end_date')
)
def update_trend(selected_dataset, start_date, end_date):
    dataset = df_main if selected_dataset == 'filtered_data' else df_valid
    filtered_df = dataset[(dataset['DATE OCC'] >= start_date) & (dataset['DATE OCC'] <= end_date)]

    # Handle empty dataset case
    if filtered_df.empty:
        return px.line(title="No data available in this date range")

    # Resample the data by month and count violations
    monthly_counts = filtered_df.resample('M', on='DATE OCC').size().reset_index(name='Count')

    trend_fig = px.line(
        monthly_counts,
        x='DATE OCC',
        y='Count',
        title='Violation Trends Over Time',
        labels={'DATE OCC': 'Date', 'Count': 'Number of Violations'}
    )
    return trend_fig

# Callback for updating status distribution bar chart
@app.callback(
    Output('status-bar-chart', 'figure'),
    Input('dataset-dropdown', 'value'),
    Input('date-picker', 'start_date'),
    Input('date-picker', 'end_date')
)
def update_status_chart(selected_dataset, start_date, end_date):
    dataset = df_main if selected_dataset == 'filtered_data' else df_valid
    filtered_df = dataset[(dataset['DATE OCC'] >= start_date) & (dataset['DATE OCC'] <= end_date)]

    # Handle empty dataset case
    if filtered_df.empty:
        return px.bar(title="Violation Status Distribution - No data available")

    status_counts = filtered_df['Status'].value_counts().reset_index()
    status_counts.columns = ['Violation Status', 'Count']

    status_fig = px.bar(
        status_counts,
        x='Violation Status',
        y='Count',
        title='Violation Status Distribution',
        labels={'Violation Status': 'Violation Status', 'Count': 'Number of Violations'},
        text='Count'
    )
    status_fig.update_layout(
        xaxis_title="Violation Status",
        yaxis_title="Count",
        template="plotly_white",
        barmode='stack'
    )
    return status_fig

# Callback for updating violation location map
@app.callback(
    Output('location-map', 'figure'),
    Input('dataset-dropdown', 'value'),
    Input('date-picker', 'start_date'),
    Input('date-picker', 'end_date')
)
def update_map(selected_dataset, start_date, end_date):
    dataset = df_main if selected_dataset == 'filtered_data' else df_valid
    filtered_df = dataset[(dataset['DATE OCC'] >= start_date) & (dataset['DATE OCC'] <= end_date)]

    # Handle empty dataset case
    if filtered_df.empty:
        return px.scatter_mapbox(title="Violation Locations - No data available")

    map_fig = px.scatter_mapbox(
        filtered_df,
        lat='LAT',
        lon='LON',
        hover_name='AREA NAME',
        color='Status',
        title='Violation Locations',
        mapbox_style="carto-positron",
        zoom=10
    )
    return map_fig

# Callback for updating age group pie chart
@app.callback(
    Output('age-group-pie-chart', 'figure'),
    Input('dataset-dropdown', 'value')
)
def update_age_group_chart(selected_dataset):
    dataset = df_main if selected_dataset == 'filtered_data' else df_valid
    age_group_counts = dataset['Age Group'].value_counts().reset_index()
    age_group_counts.columns = ['Age Group', 'Count']

    pie_chart = px.pie(
        age_group_counts,
        names='Age Group',
        values='Count',
        title='Crimes by Age Group',
        template='plotly_white'
    )
    return pie_chart

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)