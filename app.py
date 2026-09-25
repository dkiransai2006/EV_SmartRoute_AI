import streamlit as st
import pandas as pd
import folium

from streamlit_folium import st_folium

from location import get_gps_location

from stations import (
    find_stations_along_route
)

from routing import (
    geocode_destination,
    get_route,
    get_route_matrix,
    get_route_via_station
)

from battery import (
    calculate_battery,
    can_reach
)

from graph import build_ev_graph
from ucs_graph import ucs
from greedy_bfs_graph import greedy_best_first
from aStar_graph import a_star


# ==================================================
# PAGE
# ==================================================

st.set_page_config(
    page_title="EV SmartRoute AI",
    page_icon="⚡",
    layout="wide"
)


# ==================================================
# TITLE
# ==================================================

st.title("⚡ EV SmartRoute AI")

st.subheader(
    "AI-Based Intelligent EV Route and Charging Planner"
)

st.write(
    "Find reachable charging stations along "
    "your real road journey."
)


# ==================================================
# SESSION STATE
# ==================================================

defaults = {

    "route": None,

    "route_stations": [],

    "destination_data": None,

    "station_analysis": [],

    "selected_station": None,

    "selected_route": None,

    "search_results": None

}


for key, value in defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ==================================================
# CURRENT LOCATION
# ==================================================

st.header("📍 Current Location")

latitude, longitude, accuracy, location_error = (
    get_gps_location()
)


if (
    latitude is not None
    and
    longitude is not None
):

    st.success(
        "📍 GPS location detected successfully!"
    )

    st.write(
        f"Latitude: {latitude:.6f}"
    )

    st.write(
        f"Longitude: {longitude:.6f}"
    )

    if accuracy is not None:

        st.write(
            f"GPS accuracy: approximately "
            f"{accuracy:.1f} meters"
        )

else:

    st.warning(
        location_error
        or
        "Waiting for GPS location..."
    )


# ==================================================
# DESTINATION
# ==================================================

st.header("🎯 Destination")

destination = st.text_input(

    "Where do you want to go?",

    placeholder=(
        "Example: Rajiv Gandhi "
        "International Airport"
    )

)


# ==================================================
# EV INFORMATION
# ==================================================

st.header("🔋 EV Information")

col1, col2, col3, col4 = st.columns(4)


with col1:

    battery_percentage = st.number_input(

        "Current Battery (%)",

        min_value=1.0,

        max_value=100.0,

        value=50.0,

        step=1.0

    )


with col2:

    battery_capacity = st.number_input(

        "Battery Capacity (kWh)",

        min_value=1.0,

        max_value=200.0,

        value=50.0,

        step=1.0

    )


with col3:

    consumption = st.number_input(

        "Energy Consumption (kWh/km)",

        min_value=0.01,

        max_value=2.0,

        value=0.15,

        step=0.01

    )


with col4:

    reserve_percentage = st.number_input(

        "Safety Reserve (%)",

        min_value=0.0,

        max_value=50.0,

        value=15.0,

        step=1.0

    )


# ==================================================
# BATTERY CALCULATION
# ==================================================

(
    available_energy,
    theoretical_range,
    usable_range
) = calculate_battery(

    battery_percentage,

    battery_capacity,

    consumption,

    reserve_percentage

)


st.info(

    f"🔋 Available Energy: "
    f"{available_energy:.2f} kWh | "

    f"🚗 Theoretical Range: "
    f"{theoretical_range:.1f} km | "

    f"🛡️ Usable Range: "
    f"{usable_range:.1f} km"

)


# ==================================================
# PLAN BUTTON
# ==================================================

st.divider()

plan = st.button(

    "🚗 Plan My EV Journey",

    type="primary"

)


if plan:

    # ==================================================
    # RESET OLD RESULTS
    # ==================================================

    st.session_state.route = None

    st.session_state.route_stations = []

    st.session_state.destination_data = None

    st.session_state.station_analysis = []

    st.session_state.selected_station = None

    st.session_state.selected_route = None

    st.session_state.search_results = None


    # ==================================================
    # GPS CHECK
    # ==================================================

    if (
        latitude is None
        or
        longitude is None
    ):

        st.error(
            "❌ GPS location is not available."
        )

        st.stop()


    # ==================================================
    # DESTINATION CHECK
    # ==================================================

    if not destination.strip():

        st.error(
            "❌ Please enter a destination."
        )

        st.stop()


    # ==================================================
    # FIND DESTINATION
    # ==================================================

    with st.spinner(
        "🔎 Finding your destination..."
    ):

        destination_data = (
            geocode_destination(
                destination
            )
        )


    if destination_data is None:

        st.error(
            "❌ Destination could not be found."
        )

        st.stop()


    st.session_state.destination_data = (
        destination_data
    )


    destination_lat = (
        destination_data["latitude"]
    )

    destination_lon = (
        destination_data["longitude"]
    )


    st.success(

        "🎯 Destination found: "
        +
        destination_data["address"]

    )


    # ==================================================
    # REAL ROAD ROUTE
    # ==================================================

    with st.spinner(
        "🛣️ Calculating real road route..."
    ):

        route = get_route(

            latitude,

            longitude,

            destination_lat,

            destination_lon

        )


    if route is None:

        st.error(
            "❌ Could not calculate the road route."
        )

        st.stop()


    st.session_state.route = route


    # ==================================================
    # FIND CHARGING STATIONS
    # ==================================================

    with st.spinner(

        "🔌 Finding charging stations "
        "along your route..."

    ):

        route_stations = (
            find_stations_along_route(

                route,

                corridor_km=5

            )
        )


    if not route_stations:

        st.warning(

            "⚠️ No charging stations were found "
            "near your route."

        )

        st.stop()


    st.session_state.route_stations = (
        route_stations
    )


    st.success(

        f"Found {len(route_stations)} "
        "charging stations along your route."

    )


    # ==================================================
    # CANDIDATES
    # ==================================================

    candidates = route_stations


    st.info(

        f"🧠 Analyzing {len(candidates)} "
        "candidate charging stations using "
        "real road distances..."

    )


    # ==================================================
    # SOURCE → STATIONS
    # ==================================================

    with st.spinner(

        "📏 Calculating real driving distances..."

    ):

        matrix = get_route_matrix(

            latitude,

            longitude,

            candidates

        )


    if not matrix:

        st.error(

            "❌ Could not calculate road distances "
            "to the charging stations."

        )

        st.stop()


    # ==================================================
    # BATTERY CHECK
    # ==================================================

    station_analysis = []


    for index, station in enumerate(
        candidates
    ):

        if index >= len(matrix):

            continue


        cell = matrix[index]


        distance_meters = (
            cell.get("distance")
        )


        if distance_meters is None:

            continue


        distance_km = (
            distance_meters / 1000
        )


        reachable = can_reach(

            distance_km,

            usable_range

        )


        station_analysis.append({

            "id":
                station["id"],

            "name":
                station["name"],

            "latitude":
                station["latitude"],

            "longitude":
                station["longitude"],

            "address":
                station["address"],

            "town":
                station["town"],

            "state":
                station["state"],

            "distance_from_source":
                distance_km,

            "reachable":
                reachable

        })


    # ==================================================
    # REACHABLE STATIONS
    # ==================================================

    reachable = [

        station

        for station in station_analysis

        if station["reachable"]

    ]


    reachable = sorted(

        reachable,

        key=lambda x:
            x["distance_from_source"]

    )[:5]


    # ==================================================
    # DISTANCE TO DESTINATION
    # ==================================================

    if reachable:

        destination_matrix = (
            get_route_matrix(

                destination_lat,

                destination_lon,

                reachable

            )
        )


        for index, station in enumerate(
            reachable
        ):

            if index >= len(
                destination_matrix
            ):

                station[
                    "distance_to_destination"
                ] = None

                continue


            cell = destination_matrix[
                index
            ]


            distance_meters = (
                cell.get("distance")
            )


            if distance_meters is None:

                station[
                    "distance_to_destination"
                ] = None

            else:

                station[
                    "distance_to_destination"
                ] = (

                    distance_meters
                    /
                    1000

                )


    # ==================================================
    # SAVE ANALYSIS
    # ==================================================

    for station in station_analysis:

        if (

            station["reachable"]

            and

            "distance_to_destination"
            not in station

        ):

            station[
                "distance_to_destination"
            ] = None


    st.session_state.station_analysis = (
        station_analysis
    )


    # ==================================================
    # SIMPLE AI DECISION
    # ==================================================

    valid_stations = [

        station

        for station in reachable

        if station.get(
            "distance_to_destination"
        ) is not None

    ]


    if valid_stations:

        selected_station = min(

            valid_stations,

            key=lambda station:

                (

                    station[
                        "distance_from_source"
                    ]

                    +

                    station[
                        "distance_to_destination"
                    ]

                )

        )


        st.session_state.selected_station = (
            selected_station
        )


        # ==================================================
        # FINAL REAL ROUTE
        # ==================================================

        with st.spinner(

            "🧠 Building final route through "
            "the selected charging station..."

        ):

            selected_route = (
                get_route_via_station(

                    latitude,

                    longitude,

                    selected_station[
                        "latitude"
                    ],

                    selected_station[
                        "longitude"
                    ],

                    destination_lat,

                    destination_lon

                )
            )


        st.session_state.selected_route = (
            selected_route
        )


        # ==================================================
        # AI SEARCH ALGORITHMS
        # ==================================================

        search_stations = valid_stations


        graph, heuristic = build_ev_graph(
            search_stations
        )


        # ==================================================
        # UCS
        # ==================================================

        ucs_visited, ucs_path, ucs_cost = ucs(

            graph,

            "START",

            "DESTINATION"

        )


        # ==================================================
        # GREEDY BEST-FIRST
        # ==================================================

        greedy_visited, greedy_path = (
            greedy_best_first(

                graph,

                heuristic,

                "START",

                "DESTINATION"

            )
        )


        # ==================================================
        # A*
        # ==================================================

        astar_visited, astar_path, astar_cost = (
            a_star(

                graph,

                heuristic,

                "START",

                "DESTINATION"

            )
        )


        # ==================================================
        # GET STATION FROM PATH
        # ==================================================

        def get_station_from_path(
            path,
            stations
        ):

            for node in path:

                if node.startswith(
                    "STATION_"
                ):

                    number = node.split(
                        "_"
                    )[1]

                    index = int(
                        number
                    ) - 1


                    if (
                        0 <= index
                        <
                        len(stations)
                    ):

                        return stations[
                            index
                        ]

            return None


        ucs_station = (
            get_station_from_path(

                ucs_path,

                search_stations

            )
        )


        greedy_station = (
            get_station_from_path(

                greedy_path,

                search_stations

            )
        )


        astar_station = (
            get_station_from_path(

                astar_path,

                search_stations

            )
        )


        # ==================================================
        # SAVE SEARCH RESULTS
        # ==================================================

        st.session_state.search_results = {

            "ucs_path":
                ucs_path,

            "ucs_cost":
                ucs_cost,

            "ucs_visited":
                ucs_visited,

            "ucs_station":
                ucs_station,

            "greedy_path":
                greedy_path,

            "greedy_visited":
                greedy_visited,

            "greedy_station":
                greedy_station,

            "astar_path":
                astar_path,

            "astar_cost":
                astar_cost,

            "astar_visited":
                astar_visited,

            "astar_station":
                astar_station

        }


# ==================================================
# GET SAVED RESULTS
# ==================================================

route = st.session_state.route

destination_data = (
    st.session_state.destination_data
)

station_analysis = (
    st.session_state.station_analysis
)

selected_station = (
    st.session_state.selected_station
)

selected_route = (
    st.session_state.selected_route
)

search_results = (
    st.session_state.search_results
)


# ==================================================
# SHOW RESULTS
# ==================================================

if (

    route is not None

    and

    destination_data is not None

):

    destination_lat = (
        destination_data["latitude"]
    )

    destination_lon = (
        destination_data["longitude"]
    )


    # ==================================================
    # AI DECISION
    # ==================================================

    if selected_station:

        st.header(
            "🧠 AI Charging Decision"
        )


        st.success(

            "🔌 Selected Charging Station: "
            +
            selected_station["name"]

        )


        st.write(

            "The system selected a reachable "
            "charging station using real road "
            "distance and battery feasibility."

        )


        col1, col2, col3 = st.columns(3)


        with col1:

            st.metric(

                "Source → Station",

                f"{selected_station['distance_from_source']:.1f} km"

            )


        with col2:

            st.metric(

                "Station → Destination",

                f"{selected_station['distance_to_destination']:.1f} km"

            )


        with col3:

            total = (

                selected_station[
                    "distance_from_source"
                ]

                +

                selected_station[
                    "distance_to_destination"
                ]

            )


            st.metric(

                "Total Journey",

                f"{total:.1f} km"

            )


        st.markdown(

            """
            ### Why this station?

            ✅ Reachable with current battery

            ✅ Within the safety-adjusted range

            ✅ Located near the planned journey

            ✅ Supports continuation toward the destination
            """

        )


    # ==================================================
    # MAP
    # ==================================================

    st.header(
        "🗺️ Intelligent EV Route"
    )


    map_object = folium.Map(

        location=[

            latitude,

            longitude

        ],

        zoom_start=7

    )


    # ==================================================
    # SOURCE
    # ==================================================

    folium.Marker(

        [

            latitude,

            longitude

        ],

        tooltip="📍 Your Location",

        popup="Current GPS Location",

        icon=folium.Icon(

            color="green",

            icon="play"

        )

    ).add_to(map_object)


    # ==================================================
    # DESTINATION
    # ==================================================

    folium.Marker(

        [

            destination_lat,

            destination_lon

        ],

        tooltip="🎯 Destination",

        popup=destination_data["address"],

        icon=folium.Icon(

            color="red",

            icon="flag"

        )

    ).add_to(map_object)


    # ==================================================
    # SELECTED STATION
    # ==================================================

    if selected_station:

        folium.Marker(

            [

                selected_station[
                    "latitude"
                ],

                selected_station[
                    "longitude"
                ]

            ],

            tooltip=(
                "🔌 AI Selected Charging Station"
            ),

            popup=(

                "<b>"

                +

                selected_station["name"]

                +

                "</b><br>"

                +

                selected_station["address"]

            ),

            icon=folium.Icon(

                color="blue",

                icon="flash"

            )

        ).add_to(map_object)


    # ==================================================
    # ROUTE
    # ==================================================

    route_to_display = (

        selected_route

        if selected_route is not None

        else route

    )


    try:

        features = route_to_display[
            "features"
        ]


        for feature in features:

            geometry = feature.get(
                "geometry"
            )


            if geometry is None:

                continue


            geometry_type = geometry.get(
                "type"
            )


            coordinates = geometry.get(
                "coordinates"
            )


            if geometry_type == "LineString":

                lines = [
                    coordinates
                ]

            elif geometry_type == "MultiLineString":

                lines = coordinates

            else:

                lines = []


            for line in lines:

                points = [

                    [

                        point[1],

                        point[0]

                    ]

                    for point in line

                ]


                folium.PolyLine(

                    points,

                    weight=7,

                    opacity=0.85,

                    tooltip=(

                        "🧠 Source → "

                        "Charging Station → "

                        "Destination"

                    )

                ).add_to(map_object)


    except (

        KeyError,

        IndexError,

        TypeError

    ):

        st.warning(

            "⚠️ Could not display route geometry."

        )


    # ==================================================
    # OTHER STATIONS
    # ==================================================

    for station in station_analysis:

        if (

            selected_station

            and

            station["id"]
            ==
            selected_station["id"]

        ):

            continue


        if station["reachable"]:

            icon_color = "lightblue"

            tooltip = (

                "🟢 Reachable: "

                +

                station["name"]

            )

        else:

            icon_color = "gray"

            tooltip = (

                "🔴 Not reachable: "

                +

                station["name"]

            )


        folium.Marker(

            [

                station["latitude"],

                station["longitude"]

            ],

            tooltip=tooltip,

            popup=(

                "<b>"

                +

                station["name"]

                +

                "</b><br>"

                +

                station["address"]

                +

                "<br><br>"

                +

                "Source → Station: "

                +

                f"{station['distance_from_source']:.1f}"

                +

                " km"

            ),

            icon=folium.Icon(

                color=icon_color,

                icon="flash"

            )

        ).add_to(map_object)


    st_folium(

        map_object,

        width=1100,

        height=600

    )


    # ==================================================
    # BATTERY FEASIBILITY
    # ==================================================

    st.header(
        "🔋 Battery Feasibility"
    )


    reachable_count = sum(

        1

        for station in station_analysis

        if station["reachable"]

    )


    unreachable_count = (

        len(station_analysis)

        -

        reachable_count

    )


    col1, col2 = st.columns(2)


    with col1:

        st.success(

            f"🟢 Reachable: "
            f"{reachable_count}"

        )


    with col2:

        st.error(

            f"🔴 Unreachable: "
            f"{unreachable_count}"

        )


    # ==================================================
    # STATION TABLE
    # ==================================================

    st.header(
        "🔌 Charging Station Analysis"
    )


    rows = []


    for station in station_analysis:

        rows.append({

            "Charging Station":
                station["name"],

            "Source → Station (km)":
                round(

                    station[
                        "distance_from_source"
                    ],

                    2

                ),

            "Reachable":

                "YES"

                if station["reachable"]

                else "NO"

        })


    if rows:

        df = pd.DataFrame(rows)


        st.dataframe(

            df,

            use_container_width=True,

            hide_index=True

        )


    # ==================================================
    # AI SEARCH COMPARISON
    # ==================================================

    if search_results:

        st.divider()


        st.header(
            "🧠 AI Search Algorithm Comparison"
        )


        st.write(

            "The same reachable charging options "
            "are tested using three search methods."

        )


        col1, col2, col3 = st.columns(3)


        # ==================================================
        # UCS
        # ==================================================

        with col1:

            st.subheader(
                "UCS"
            )


            ucs_station = (
                search_results[
                    "ucs_station"
                ]
            )


            if ucs_station:

                st.write(

                    "🔌 "

                    +

                    ucs_station["name"]

                )


            st.write(

                "Graph Cost: "

                +

                f"{search_results['ucs_cost']:.0f} steps"

            )


            st.write(

                "Nodes checked: "

                +

                str(

                    len(

                        search_results[
                            "ucs_visited"
                        ]

                    )

                )

            )


            st.write(
                "Nodes explored:"
            )


            st.code(

                " → ".join(

                    search_results[
                        "ucs_visited"
                    ]

                )

            )


            st.write(
                "Actual path:"
            )


            st.code(

                " → ".join(

                    search_results[
                        "ucs_path"
                    ]

                )

            )


        # ==================================================
        # GREEDY BEST-FIRST
        # ==================================================

        with col2:

            st.subheader(
                "Greedy Best-First"
            )


            greedy_station = (
                search_results[
                    "greedy_station"
                ]
            )


            if greedy_station:

                st.write(

                    "🔌 "

                    +

                    greedy_station["name"]

                )


            st.write(

                "Nodes checked: "

                +

                str(

                    len(

                        search_results[
                            "greedy_visited"
                        ]

                    )

                )

            )


            st.write(
                "Nodes explored:"
            )


            st.code(

                " → ".join(

                    search_results[
                        "greedy_visited"
                    ]

                )

            )


            st.write(
                "Actual path:"
            )


            st.code(

                " → ".join(

                    search_results[
                        "greedy_path"
                    ]

                )

            )


        # ==================================================
        # A*
        # ==================================================

        with col3:

            st.subheader(
                "A*"
            )


            astar_station = (
                search_results[
                    "astar_station"
                ]
            )


            if astar_station:

                st.write(

                    "🔌 "

                    +

                    astar_station["name"]

                )


            st.write(

                "Graph Cost: "

                +

                f"{search_results['astar_cost']:.0f} steps"

            )


            st.write(

                "Nodes checked: "

                +

                str(

                    len(

                        search_results[
                            "astar_visited"
                        ]

                    )

                )

            )


            st.write(
                "Nodes explored:"
            )


            st.code(

                " → ".join(

                    search_results[
                        "astar_visited"
                    ]

                )

            )


            st.write(
                "Actual path:"
            )


            st.code(

                " → ".join(

                    search_results[
                        "astar_path"
                    ]

                )

            )


        # ==================================================
        # SIMPLE EXPLANATION
        # ==================================================

        st.markdown(

            """
            ### Simple Explanation

            **UCS:** Checks the path cost and chooses the lowest-cost path.

            **Greedy Best-First:** Looks mainly at which option seems closer to the destination.

            **A\*:** Uses both the cost already travelled and the estimated cost remaining.
            """

        )


    # ==================================================
    # FINAL JOURNEY
    # ==================================================

    if selected_station:

        st.divider()


        st.header(
            "🚗 Final Journey Plan"
        )


        st.info(

            "📍 Your Location  →  "

            "🔌 "

            +

            selected_station["name"]

            +

            "  →  🎯 "

            +

            destination_data["address"]

        )


    else:

        st.warning(

            "⚠️ No reachable charging station "
            "could be selected."

        )