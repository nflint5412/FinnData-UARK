import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import yfinance as yf
import plotly.graph_objs as go

# Function to calculate RSI
def calculate_rsi(data, period=14):
    delta = data.diff().dropna()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    RS = gain / loss
    RSI = 100 - (100 / (1 + RS))
    return RSI

# Function to fetch data and calculate RSI for 90 days
def fetch_data_and_calculate_rsi(symbols):
    stock_data = {}
    for symbol in symbols:
        data = yf.download(symbol, period="90d")
        if data.empty:
            continue
        close_prices = data['Close']
        rsi = calculate_rsi(close_prices)
        stock_data[symbol] = {'ohlc': data[['Open', 'High', 'Low', 'Close']], 'rsi': rsi}
    return stock_data

# Initialize Dash app
app = dash.Dash(__name__)

# Define app layout
app.layout = html.Div([
    html.H1("Flint's Fab 5 Analytics"),
    html.P("Please enter up to 5 stock symbols separated by commas"),
    dcc.Input(id='input-stock', type='text', value=''),
    html.Button('Submit', id='submit-val', n_clicks=0),
    html.Div(id='output-graph')
])

# Callback for updating the graph
@app.callback(
    Output('output-graph', 'children'),
    [Input('submit-val', 'n_clicks')],
    [State('input-stock', 'value')]
)
def update_graph(n_clicks, value):
    if n_clicks > 0:
        symbols = [s.strip().upper() for s in value.split(',') if s.strip()][:5]
        stock_data = fetch_data_and_calculate_rsi(symbols)
        graphs = []
        for symbol, data in stock_data.items():
            # OHLC chart
            candlestick = go.Candlestick(x=data['ohlc'].index,
                                         open=data['ohlc']['Open'],
                                         high=data['ohlc']['High'],
                                         low=data['ohlc']['Low'],
                                         close=data['ohlc']['Close'])
            fig_stock = go.Figure(data=[candlestick], layout=go.Layout(title=f"{symbol} Stock Data", xaxis={'title': 'Date'}, yaxis={'title': 'Price'}))
            graphs.append(dcc.Graph(figure=fig_stock))

            # RSI chart with threshold lines
            rsi_trace = go.Scatter(x=data['rsi'].index, y=data['rsi'], name='RSI')
            fig_rsi = go.Figure(data=[rsi_trace], layout=go.Layout(title=f"{symbol} RSI", xaxis={'title': 'Date'}, yaxis={'title': 'RSI'}))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
            graphs.append(dcc.Graph(figure=fig_rsi))

        return graphs

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
