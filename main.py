import requests
import json
from tkinter import messagebox
from ttkwidgets.autocomplete import AutocompleteCombobox
from tkinter import ttk
import tkinter as tk
from datetime import datetime

states = [
    'AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA',
    'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME',
    'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM',
    'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX',
    'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY'
]


def error_box(field_error):
    """Display any errors produced from field entry

    Parameters
    ----------
    field_error
        The field to show the error on
    """
    tk.messagebox.showerror(
        title="Invalid Selection", message=f"Make sure all related fields are filled in!"
    )


def error_handle(response):
    """Handle any API errors

    Parameters
    ----------
    response
        requests object containing status code and reason for errors
    """
    if response.status_code != 200:
        tk.messagebox.showerror(
            title="API Failed", message=f"Error {response.status_code} occured with the API. Choose another option.\nAPI Reason: {response.reason})"
        )
        return True
    return False   


def get_state_zones(event):
    """Populates zone combo box given a state

    Parameters
    ----------
    event
        A widget object that contains the user's state selection
    """

    state = event.widget.get()
    if state not in states:
        error_box("State")
        return
    url = f"https://api.weather.gov/zones/forecast/?area={state}"
    headers = {
        'User-Agent': '(myweatherapp.com, contact@myweatherapp.com)'
    }
    response = requests.request("GET", url, headers=headers)
    if error_handle(response):
        return

    # place all names and id's into a dictionary to then be printed out
    all_zones = json.loads(response.text)['features']
    global all_areas
    all_areas = {}
    display_areas = []
    for zone in all_zones:
        display_areas.append(zone["properties"]["name"])
        all_areas[zone["properties"]["name"]] = zone["properties"]["id"]
    zone_selection.config(completevalues=display_areas)
    zone_selection.current(0)
    return get_zone_stations(zone_selection.get())


def get_zone_stations(event):
    """Populates station combo box given a zone.

    Parameters
    ----------
    event
        A string or widget object that contains the user's zone selection
    """

    zone = event
    if type(event) != str:
        zone = event.widget.get()
    if zone not in all_areas.keys():
        error_box("Zone")
        return
    zone_id = all_areas[zone]
    url = f"https://api.weather.gov/zones/forecast/{zone_id}/stations"
    headers = {
        'User-Agent': '(myweatherapp.com, contact@myweatherapp.com)'
    }
    response = requests.request("GET", url, headers=headers)
    if error_handle(response):
        return

    # place all names and id's into a dictionary to then be printed out
    all_stations = json.loads(response.text)['features']
    global display_stations
    display_stations = {}
    for zone in all_stations:
        display_stations[zone["properties"]["name"]] = [zone["properties"]["stationIdentifier"]]
    station_selection.config(completevalues=display_stations.keys())
    station_selection.current(0)
    return


def station_search():
    """Grabs coordinates of a station to be used to grab weather data.

    Parameters
    ----------
    None
    """

    station_id = display_stations[station_selection.get()]
    if not station_id or station_id not in display_stations.values():
        return error_box("Station")
    url = f"https://api.weather.gov/stations/{station_id[0]}"
    headers = {
        'User-Agent': '(myweatherapp.com, contact@myweatherapp.com)'
    }
    
    # the call needs to be twice sometimes to bypass a 500 error
    response = requests.request("GET", url, headers=headers)
    response = requests.request("GET", url, headers=headers)
    if error_handle(response):
        return
    coords = json.loads(response.text)["geometry"]["coordinates"]
    return get_forecast(coords[1], coords[0])


def coords_search():
    """Error handling an invalid coordinate.

    Parameters
    ----------
    None
    """

    try:
        latitude = float(lat_coord.get())
        longitude = float(lon_coord.get())
    except ValueError:
        tk.messagebox.showerror(
            title="Invalid Selection", message=f"Only numbers are allowed for coordinates!"
        )
    if not latitude or not longitude:
        return error_box("Coordinates")

    return get_forecast(latitude, longitude)


def get_forecast(latitude, longitude):
    """Gets information from coordinates that contains a forecast for hourly/daily to print.

    Parameters
    ----------
    latitude
        float for the x coordinate
    latitude
        float for the y coordinate
    """

    url = f"https://api.weather.gov/points/{latitude},{longitude}"
    headers = {
        'User-Agent': '(myweatherapp.com, contact@myweatherapp.com)'
    }

    # the call needs to be twice sometimes to bypass a 500 error
    response = requests.request("GET", url, headers=headers)
    response = requests.request("GET", url, headers=headers)
    if error_handle(response):
        return

    # use the api to get the daily/hourly forecast
    if forecast_selection.get() == "Hourly":
        url = json.loads(response.text)["properties"]["forecastHourly"]
    else:
        url = json.loads(response.text)["properties"]["forecastGridData"] + "/forecast"

    # the call needs to be twice sometimes to bypass a 500 error
    response = requests.request("GET", url, headers=headers)
    response = requests.request("GET", url, headers=headers)
    if error_handle(response):
        return
    if not view_window.get(tk.END):
        view_window.delete("1.0","end")
    
    # go through raw data and print it in a pretty way
    formatted = "Date       Time     UTC\n"
    json_data = json.loads(response.text)
    if forecast_selection.get() == "Hourly":
        for hour_data in json_data["properties"]["periods"]:
            date_time = datetime.strptime(hour_data['startTime'], '%Y-%m-%dT%X%z')
            formatted += f"{date_time}\n\t"
            formatted += f"Temperature: {hour_data['temperature']} {hour_data['temperatureUnit']}\n\t"
            formatted += f"Wind Speed: {hour_data['windSpeed']} {hour_data['windDirection']}\n\t"
            formatted += f"Forecast: {hour_data['shortForecast']}\n\n"
    else:
        for day_data in json_data["properties"]["periods"]:
            date_time = datetime.strptime(day_data['startTime'], '%Y-%m-%dT%X%z')
            formatted += f"{date_time}\n\t"
            formatted += f"{day_data['name']}\n\t"
            formatted += f"Temperature: {day_data['temperature']} {day_data['temperatureUnit']}\n\t"
            formatted += f"Wind Speed: {day_data['windSpeed']} {day_data['windDirection']}\n\t"
            formatted += f"Summary Forecast: {day_data['shortForecast']}\n\t"
            formatted += f"Forecast: {day_data['detailedForecast']}\n\n"
    view_window.insert(tk.END, formatted)


def main_screen():
    """Creates GUI screen to allow inputs for state, zone, and forecast type.

    Parameters
    ----------
    None
    """

    main_view = tk.Tk()

    # display screen in the middle of monitor
    width_of_window = 1400
    height_of_window = 600
    screen_width = main_view.winfo_screenwidth()
    screen_height = main_view.winfo_screenheight()
    x_coordinate = (screen_width/2) - (width_of_window/2)
    y_coordinate = (screen_height/2) - (height_of_window/2)
    main_view.geometry('%dx%d+%d+%d' % (width_of_window, height_of_window,
                                                x_coordinate, y_coordinate))

    # setup window with the right background and title
    main_view.title('Weather_Forecast')
    main_view.config(bg='#59bfff')

    # create an inner frame for dynamic combo boxes
    frame = tk.Frame(main_view, bg='#59bfff')
    frame.pack(expand=True)

    tk.Label(
        frame, 
        bg='#59bfff',
        font = ('Times',21),
        text='Search by State, Zone, Station'
    ).grid(row=0, columnspan=3, sticky='S')

    # combo box to select state
    tk.Label(frame, text="States").grid(row=1, column=0, sticky="E")
    state_entry = AutocompleteCombobox(
        frame, 
        completevalues=states
    )
    state_entry.grid(row=1, column=1, padx=10, sticky="W")
    state_entry.bind("<<ComboboxSelected>>", get_state_zones)


    # combo box to select zone
    global zone_selection
    tk.Label(frame, text="Zones").grid(row=1, column=2, sticky="E")
    zone_selection = AutocompleteCombobox(
        frame,
        font=('Times'),
        completevalues=[]
    )
    zone_selection.grid(row=1, column=3, padx=10, sticky="WE")
    zone_selection.bind("<<ComboboxSelected>>", get_zone_stations)

    # combo box to select station
    global station_selection
    tk.Label(frame, text="Stations").grid(row=1, column=4, sticky="E")
    station_selection = AutocompleteCombobox(
        frame,
        font=('Times'),
        completevalues=[]
    )
    station_selection.grid(row=1, column=5, padx=10, sticky="W")

    tk.Label(
        frame, 
        bg='#59bfff',
        font = ('Times', 21),
        text='Search by Latitude, Longititude'
    ).grid(row=2, columnspan=3, sticky='S')

    # latitude input box
    tk.Label(frame, text="Latitude").grid(row=3, column=0, sticky="E")
    global lat_coord
    lat_coord = tk.Entry(frame, width=25)
    lat_coord.grid(row=3, column=1, sticky="W", padx=10)

    # longitude input box
    tk.Label(frame, text="Longitutude").grid(row=3, column=2, sticky="E")
    global lon_coord
    lon_coord = tk.Entry(frame, width=25)
    lon_coord.grid(row=3, column=3, sticky="W", padx=10)


    # combo box to select forecast type
    global forecast_selection
    options = [
        "Hourly", "Daily", "Hourly"
    ]
    forecast_selection = tk.StringVar()
    forecast_selection.set(options[0])
    ttk.OptionMenu(
        frame,
        forecast_selection,
        *options
    ).grid(row=4, column=0, padx=15)

    # buttons to begin gathering forecast data
    tk.Button(frame, text="Search by Station", command=station_search).grid(row=4, column=1, sticky='E')
    tk.Button(frame, text="Search by Coordinates", command=coords_search).grid(row=4, column=3, sticky='W', padx=10)

    # create a viewable window with scrollbars for x/y directions
    global view_window
    xScrollbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL) 
    yScrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
    view_window = tk.Text(frame, xscrollcommand=xScrollbar.set, yscrollcommand=yScrollbar.set, width=65, height=30, wrap="none")
    xScrollbar.grid(row=5, column=6, sticky='WE')
    yScrollbar.grid(row=0, column=7, rowspan=5, sticky='NS')
    view_window.grid(row=0, column=6, rowspan=5)
    xScrollbar.config(command=view_window.xview)
    yScrollbar.config(command=view_window.yview)

    frame.mainloop()   


if __name__ == "__main__":
    main_screen()
