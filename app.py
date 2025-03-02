from flask import Flask, request, render_template_string
import networkx as nx
import folium
from geopy.geocoders import Nominatim
from werkzeug.urls import url_quote  # Ensure correct import

app = Flask(__name__)

# Sample graph creation function (expand with real data)
def create_graph():
    G = nx.Graph()
    G.add_edge('Delhi', 'Mumbai', weight=1400)
    G.add_edge('Mumbai', 'Pune', weight=150)
    G.add_edge('Pune', 'Hyderabad', weight=560)
    G.add_edge('Hyderabad', 'Chennai', weight=630)
    G.add_edge('Chennai', 'Bangalore', weight=330)
    G.add_edge('Bangalore', 'Mumbai', weight=980)
    G.add_edge('Delhi', 'Jaipur', weight=270)
    G.add_edge('Jaipur', 'Ahmedabad', weight=540)
    return G

# Initialize the graph
graph = create_graph()

def get_shortest_path(graph, source, destination):
    try:
        path = nx.shortest_path(graph, source=source, target=destination, weight='weight')
        length = nx.shortest_path_length(graph, source=source, target=destination, weight='weight')
        return path, length
    except nx.NetworkXNoPath:
        return None, None
    except nx.NodeNotFound:
        return None, None

def create_map(path):
    geolocator = Nominatim(user_agent="nav_assistant")
    map = folium.Map(location=[20.5937, 78.9629], zoom_start=5)  # Center of India
    for location in path:
        loc = geolocator.geocode(location)
        folium.Marker([loc.latitude, loc.longitude], popup=location, icon=folium.Icon(color='blue')).add_to(map)
    for i in range(len(path) - 1):
        loc1 = geolocator.geocode(path[i])
        loc2 = geolocator.geocode(path[i+1])
        folium.PolyLine(locations=[[loc1.latitude, loc1.longitude], [loc2.latitude, loc2.longitude]], color="blue").add_to(map)
    return map._repr_html_()

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        source = request.form.get('source')
        destination = request.form.get('destination')
        path, length = get_shortest_path(graph, source, destination)
        if path:
            result = f"The shortest path from {source} to {destination} is: {' -> '.join(path)}<br>Total travel time (or distance): {length} km"
            map_html = create_map(path)
        else:
            result = f"No path found from {source} to {destination}."
            map_html = None
        return render_template_string(TEMPLATE, result=result, map_html=map_html)
    return render_template_string(TEMPLATE, result=None, map_html=None)

TEMPLATE = '''
<!doctype html>
<html>
    <head>
        <title>Navigation Assistant</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                color: #333;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .container {
                background-color: #fff;
                padding: 20px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                width: 80%;
                max-width: 600px;
            }
            h1 {
                color: #007BFF;
            }
            form {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            input[type="text"] {
                width: 100%;
                padding: 8px;
                margin-bottom: 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            input[type="submit"] {
                background-color: #007BFF;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            input[type="submit"]:hover {
                background-color: #0056b3;
            }
            #map {
                width: 100%;
                height: 500px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to the Navigation Assistant!</h1>
            <form method="post">
                <label for="source">Enter the starting point:</label>
                <input type="text" id="source" name="source" required><br>
                <label for="destination">Enter the destination point:</label>
                <input type="text" id="destination" name="destination" required><br><br>
                <input type="submit" value="Find Shortest Path">
            </form>
            {% if result %}
                <h2>Result:</h2>
                <p>{{ result|safe }}</p>
                {% if map_html %}
                    <div id="map">{{ map_html|safe }}</div>
                {% endif %}
            {% endif %}
        </div>
    </body>
</html>
'''

if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1')
