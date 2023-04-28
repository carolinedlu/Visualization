import pandas as pd
import folium
import folium.plugins
from folium.plugins import HeatMap
import plotly.express as px
import json
import tempfile
import sys
#from PyQt5 import *
from PyQt5.QtWidgets import *
#from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets
#from PyQt5.QtCore import QTimer, QFile, QIODevice



app = QtWidgets.QApplication(sys.argv)

# Load data
data = pd.read_csv('Food_Security_Data_E_All_Data_NOFLAG.csv', encoding='ISO-8859-1', dtype={'97': str, '103': str, '109': str, '115': str, '121': str, '127': str, '131': str})

# Create map centered at (0, 0) with zoom level 2
m = folium.Map(location=[0, 0], zoom_start=2)

# Store the current map style
current_style = None

# Load the country coordinates from the file
with open('country_coords.json', 'r') as f:
    all_coords = json.load(f)

# Extract the country coordinates
start = "Afghanistan"
end = "Zimbabwe"
country_coords = {}
for k, v in all_coords.items():
    if start <= k <= end and len(v) == 2:
        country_coords[k] = v

def update_year_label(value):
    year_slider.setProperty("data-year", str(value))

# Define function to display the map in the QWebEngineView widget
def display_map(item_var=None, year_slider=None, m=None, country_coords=None):

    # Save the map to a temporary HTML file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
    m.save(temp_file.name)

    # Load the map into the QWebEngineView widget
    url = QtCore.QUrl.fromLocalFile(temp_file.name)
    view.load(url)

    # Connect the loadFinished signal to a slot that deletes the temporary file
    def delete_temp_file():
        # Open the temporary file using QFile
        file = QFile(temp_file.name)

        # Open the file in WriteOnly mode
        if file.open(QIODevice.WriteOnly):
            # Set the size of the file to 0 bytes to ensure it is deleted
            file.resize(0)
            file.remove()

    view.loadFinished.connect(delete_temp_file)

# Define function to update map based on user inputs
def update_map(item_var, year_slider, style_var, m):
    # Get user inputs
    item = item_var.currentText()
    year = year_slider.value()
    style = style_var.currentText()

    # Filter data based on user inputs
    item_data = data.loc[data['Item'] == item]
    year_data = item_data[['Area', 'Y{}'.format(year)]].dropna()

    # Replace non-numerical values with 0
    year_data['Y{}'.format(year)] = pd.to_numeric(year_data['Y{}'.format(year)], errors='coerce').fillna(0)

    if style == 'Heatmap':
        # Create map using filtered data
        heatmap_data = []
        for index, row in year_data.iterrows():
            try:
                lat, lon = country_coords[row['Area']]
                value = row['Y{}'.format(year)]
                heatmap_data.append([lat, lon, value])
            except KeyError:
                print('Could not get location for {}'.format(row['Area']))
            except Exception as e:
                print('Error:', e)

        # Create a new instance of the Map object
        m = folium.Map(location=[0, 0], zoom_start=2)

        if len(heatmap_data) > 0:
            # Normalize the value
            min_value = min(heatmap_data, key=lambda x: x[2])[2]
            max_value = max(heatmap_data, key=lambda x: x[2])[2]
            heatmap_data = [[lat, lon, (value - min_value) / (max_value - min_value)] for lat, lon, value in heatmap_data]

        HeatMap(heatmap_data, min_opacity=0.5, max_val=1, radius=25, blur=15, gradient={0.2: 'blue', 0.4: 'limegreen', 0.6: 'yellow', 1: 'red'}).add_to(m)            
        display_map(item_var, year_slider, m, country_coords)
    
    elif style == 'Bar Chart':
        bar_chart_data = []
        for index, row in year_data.iterrows():
            try:
                lat, lon = country_coords[row['Area']]
                bar_chart_data.append([row['Area'], row['Y{}'.format(year)]])
            except KeyError:
                print('Could not get location for {}'.format(row['Area']))
            except Exception as e:
                print('Error:', e)

        bar_chart_df = pd.DataFrame(bar_chart_data, columns=['Area', 'value'])
        bar_chart_df['value'] = pd.to_numeric(bar_chart_df['value'])
        bar_chart_df = bar_chart_df.sort_values(by='value', ascending=False)
        fig = px.bar(bar_chart_df, x='Area', y='value',
                        color='value',
                        title='Bar Chart of Data')

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
        fig.write_html(temp_file.name)

        url = QtCore.QUrl.fromLocalFile(temp_file.name)
        view.load(url)

        # Connect the loadFinished signal to a slot that deletes the temporary file
        def delete_temp_file():
            # Open the temporary file using QFile
            file = QFile(temp_file.name)

            # Open the file in WriteOnly mode
            if file.open(QIODevice.WriteOnly):
                # Set the size of the file to 0 bytes to ensure it is deleted
                file.resize(0)
                file.remove()

        view.loadFinished.connect(delete_temp_file)

    if style == 'Bubble Map':
        bar_chart_data = []
        for index, row in year_data.iterrows():
            try:
                lat, lon = country_coords[row['Area']]
                bar_chart_data.append([row['Area'], lat, lon, row['Y{}'.format(year)]])
            except KeyError:
                print('Could not get location for {}'.format(row['Area']))
            except Exception as e:
                print('Error:', e)

        bar_chart_df = pd.DataFrame(bar_chart_data, columns=['Area', 'lat', 'lon', 'value'])
        bar_chart_df['value'] = pd.to_numeric(bar_chart_df['value'])
        fig = px.scatter_mapbox(bar_chart_df, lat='lat', lon='lon', text='Area',
                            size='value', color='value',
                            size_max=25,
                            color_continuous_scale="Viridis",
                            mapbox_style="carto-positron",
                            opacity=0.7,
                            center=dict(lat=0, lon=0),
                            zoom=1,
                            title='Bubble Map of {}'.format(item_var.currentText()))

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
        fig.write_html(temp_file.name)

        url = QtCore.QUrl.fromLocalFile(temp_file.name)
        view.load(url)

        # Connect the loadFinished signal to a slot that deletes the temporary file
        def delete_temp_file():
            # Open the temporary file using QFile
            file = QFile(temp_file.name)

            # Open the file in WriteOnly mode
            if file.open(QIODevice.WriteOnly):
                # Set the size of the file to 0 bytes to ensure it is deleted
                file.resize(0)
                file.remove()

        view.loadFinished.connect(delete_temp_file)
    
    elif style == 'Bar Chart Map':
        bar_chart_data = []
        popup_data = []
        for index, row in year_data.iterrows():
            try:
                lat, lon = country_coords[row['Area']]
                value = row['Y{}'.format(year)]
                bar_chart_data.append([row['Area'], lat, lon, value])
                popup_data.append([row['Area'], value])
            except KeyError:
                print('Could not get location for {}'.format(row['Area']))
            except Exception as e:
                print('Error:', e)

        m = folium.Map(location=[0, 0], zoom_start=2)

        if len(bar_chart_data) > 0:
            min_value = min(bar_chart_data, key=lambda x: x[3])[3]
            max_value = max(bar_chart_data, key=lambda x: x[3])[3]
            bar_chart_data = [[area, lat, lon, (value - min_value) / (max_value - min_value)] for area, lat, lon, value in bar_chart_data]

            for area, lat, lon, value in bar_chart_data:
                scaling_factor = 1 / (1 + abs(lat) / 35)
                popup_value = next(popup_data[1] for popup_data in popup_data if popup_data[0] == area)
                folium.Rectangle(bounds=[(lat-value*10*scaling_factor+0.5, lon-0.75), (lat+value*10*scaling_factor+0.5, lon+0.75)], color='black', fill=True, fill_color='red', weight=0.5, fill_opacity=0.8).add_child(folium.Popup(f"{area}: {popup_value}")).add_to(m)
        display_map(item_var, year_slider, m, country_coords)
    
    # Use a delay before displaying the map to ensure that it loads completely
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(lambda: display_map(item_var, year_slider, m, country_coords))
    timer.start(200)  # Wait 200ms before displaying the map

if __name__ == '__main__':
    # Create GUI window
    window = QtWidgets.QWidget()
    window.setWindowTitle('Food Security Heatmap')
    window.setGeometry(100, 100, 900, 400)

    # Load CSS file
    css_file = QFile("styleFAO.css")
    css_file.open(QFile.ReadOnly | QFile.Text)
    stream = QtCore.QTextStream(css_file)
    app.setStyleSheet(stream.readAll())
    css_file.close()

    # Create layout for the window
    layout = QtWidgets.QVBoxLayout()

    # Create dropdown selector for items
    item_var = QtWidgets.QComboBox(window)
    item_options = list(data['Item'].unique())
    item_options.sort()
    item_var.addItems(item_options)
    item_var.setCurrentIndex(0)
    layout.addWidget(item_var)

    # Create slider for years
    year_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, window)
    year_slider.setMinimum(2000)
    year_slider.setMaximum(2021)
    year_slider.setTickInterval(1)
    year_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
    year_slider.setSingleStep(1)
    year_slider.setValue(2021)
    layout.addWidget(year_slider)

    # Create a label to display the year value
    year_label = QtWidgets.QLabel(str(year_slider.value()), window)
    year_label.setAlignment(QtCore.Qt.AlignCenter)
    layout.addWidget(year_label)

    # Connect the year_slider valueChanged signal to update the year_label text
    year_slider.valueChanged.connect(lambda value: year_label.setText(str(value)))

    # Create dropdown selector for styles
    style_var = QtWidgets.QComboBox(window)
    style_options = ['Heatmap', 'Bubble Map','Bar Chart Map', 'Bar Chart']
    style_var.addItems(style_options)
    style_var.setCurrentIndex(0)
    layout.addWidget(style_var)

    # Create button to update map
    update_button = QtWidgets.QPushButton('Update Map', window)
    update_button.clicked.connect(lambda: update_map(item_var, year_slider, style_var, m))
    layout.addWidget(update_button)

    # Create QWebEngineView widget to display the map
    view = QtWebEngineWidgets.QWebEngineView(window)
    view.setFixedSize(1200, 800)
    layout.addWidget(view)

    # Set the layout of the QWidget to hold the widgets
    window.setLayout(layout)

    # Display initial map
    update_map(item_var, year_slider, style_var, m)

    # Show the window and start the event loop
    window.show()
    sys.exit(app.exec_())
