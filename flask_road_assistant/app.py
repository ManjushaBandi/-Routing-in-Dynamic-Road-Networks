from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import networkx as nx
import folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderInsufficientPrivileges, GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user_data.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    mobile = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

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

graph = create_graph()

def get_shortest_path(graph, source, destination):
    try:
        path = nx.shortest_path(graph, source=source, target=destination, weight='weight')
        length = nx.shortest_path_length(graph, source=source, target=destination, weight='weight')
        return path, length
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None, None

def create_map(path):
    geolocator = Nominatim(user_agent="nav_assistant")
    map = folium.Map(location=[20.5937, 78.9629], zoom_start=5)  # Center of India
    for location in path:
        loc = geolocator.geocode(location)
        folium.Marker([loc.latitude, loc.longitude], popup=location, icon=folium.Icon(color='blue')).add_to(map)
    for i in range(len(path) - 1):
        loc1 = geolocator.geocode(path[i])
        loc2 = geolocator.geocode(path[i + 1])
        folium.PolyLine(locations=[[loc1.latitude, loc1.longitude], [loc2.latitude, loc2.longitude]], color="blue").add_to(map)
    return map._repr_html_()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_location', methods=['POST'])
def get_location():
    try:
        location_data = request.json
        latitude = location_data['latitude']
        longitude = location_data['longitude']
        if latitude is None or longitude is None:
            return jsonify({"error": "Latitude and longitude are required"}), 400

        geolocator = Nominatim(user_agent="geoapiExercises")
        location = geolocator.reverse(f"{latitude}, {longitude}")
        address = location.address
        city = location.raw['address'].get('city', '') or location.raw['address'].get('town', '') or location.raw['address'].get('village', '')
        return jsonify({'city': city, 'address': address})
    except (GeocoderInsufficientPrivileges, GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable):
        return jsonify({'city': "Andhra Pradesh Kakinada", 'address': "Unable to determine exact address due to network issues"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/welcome', methods=['GET', 'POST'])
def welcome():
    current_location = "Andhra Pradesh Kakinada"
    if request.method == 'POST':
        source = request.form['source']
        destination = request.form['destination']
        path, length = get_shortest_path(graph, source, destination)
        if path:
            map_html = create_map(path)
            return render_template('route.html', current_location=current_location, source=source, destination=destination, map_html=map_html)
        else:
            return render_template('route.html', current_location=current_location, source=source, destination=destination, error="No path found")
    return render_template('welcome.html', current_location=current_location)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']
        user = User.query.filter_by(mobile=mobile, password=password).first()
        if user:
            session['username'] = user.username
            return redirect(url_for('welcome'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        mobile = request.form['mobile']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password == confirm_password:
            try:
                new_user = User(username=username, mobile=mobile, password=password)
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('login'))
            except Exception as e:
                return render_template('register.html', error='Username already exists')
        else:
            return render_template('register.html', error='Passwords do not match')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1')
