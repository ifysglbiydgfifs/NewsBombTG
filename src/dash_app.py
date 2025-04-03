import dash
from dash import dcc, html
import requests
import networkx as nx
import plotly.graph_objects as go

app = dash.Dash(__name__)

# Загружаем данные о графе из API
response = requests.get("http://127.0.0.1:8000/graph")
data = response.json()

G = nx.Graph()

# Добавляем узлы (сущности)
for node in data["nodes"]:
    G.add_node(node["id"], label=node["name"], type=node["type"])

# Добавляем связи
for node in data["nodes"]:
    for news in node["news"]:
        G.add_edge(node["id"], news["id"], label=news["text"])

# Генерируем позиции для узлов
pos = nx.spring_layout(G)

# Создаем граф Plotly
edge_trace = go.Scatter(
    x=[], y=[], line=dict(width=0.5, color="#888"), hoverinfo="none", mode="lines"
)

node_trace = go.Scatter(
    x=[], y=[], text=[], mode="markers+text", textposition="top center",
    marker=dict(size=10, color="blue")
)

for node in G.nodes():
    x, y = pos[node]
    node_trace["x"] += (x,)
    node_trace["y"] += (y,)
    node_trace["text"] += (G.nodes[node]["label"],)

# Интерфейс Dash
app.layout = html.Div([
    html.H1("Интерактивный граф сущностей"),
    dcc.Graph(id="graph", figure=go.Figure(data=[edge_trace, node_trace]))
])

if __name__ == "__main__":
    app.run(debug=True)
