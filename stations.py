import requests
import streamlit as st
import math


# ==================================================
# OPEN CHARGE MAP API KEY
# ==================================================

API_KEY = st.secrets["OPEN_CHARGE_MAP_API_KEY"]


# ==================================================
# FIND STATIONS NEAR A POINT
# ==================================================

def find_stations_near_point(
    latitude,
    longitude,
    distance=10,
    maxresults=50
):

    url = "https://api.openchargemap.io/v3/poi/"

    params = {

        "output": "json",

        "latitude": latitude,

        "longitude": longitude,

        "distance": distance,

        "distanceunit": "KM",

        "maxresults": maxresults,

        "compact": "false",

        "verbose": "false",

        "key": API_KEY

    }

    try:

        response = requests.get(

            url,

            params=params,

            headers={
                "x-api-key": API_KEY
            },

            timeout=10

        )

        if response.status_code != 200:

            return []

        data = response.json()

        if not isinstance(data, list):

            return []

        return data

    except requests.exceptions.RequestException:

        return []


# ==================================================
# GET COMPLETE ROUTE COORDINATES
# ==================================================

def get_route_coordinates(route):

    coordinates = []

    try:

        geometry = route[
            "features"
        ][0][
            "geometry"
        ]

        geometry_type = geometry[
            "type"
        ]

        geometry_coordinates = geometry[
            "coordinates"
        ]

        # ------------------------------------------
        # LINE STRING
        # ------------------------------------------

        if geometry_type == "LineString":

            for point in geometry_coordinates:

                longitude = point[0]

                latitude = point[1]

                coordinates.append(
                    (
                        latitude,
                        longitude
                    )
                )

        # ------------------------------------------
        # MULTI LINE STRING
        # ------------------------------------------

        elif geometry_type == "MultiLineString":

            for line in geometry_coordinates:

                for point in line:

                    longitude = point[0]

                    latitude = point[1]

                    coordinates.append(
                        (
                            latitude,
                            longitude
                        )
                    )

    except (
        KeyError,
        IndexError,
        TypeError
    ):

        return []

    return coordinates


# ==================================================
# CALCULATE ROUTE LENGTH
# ==================================================

def calculate_route_length(
    route_coordinates
):

    if len(route_coordinates) < 2:

        return 0

    earth_radius = 6371.0

    total_distance = 0

    for i in range(
        1,
        len(route_coordinates)
    ):

        lat1, lon1 = (
            route_coordinates[i - 1]
        )

        lat2, lon2 = (
            route_coordinates[i]
        )

        lat1 = math.radians(lat1)

        lon1 = math.radians(lon1)

        lat2 = math.radians(lat2)

        lon2 = math.radians(lon2)

        dlat = lat2 - lat1

        dlon = lon2 - lon1

        a = (

            math.sin(dlat / 2) ** 2

            +

            math.cos(lat1)
            *
            math.cos(lat2)
            *
            math.sin(dlon / 2) ** 2

        )

        c = 2 * math.atan2(

            math.sqrt(a),

            math.sqrt(
                1 - a
            )

        )

        total_distance += (
            earth_radius * c
        )

    return total_distance


# ==================================================
# NUMBER OF SEARCH POINTS
# ==================================================

def get_number_of_samples(
    route_distance_km
):

    if route_distance_km < 30:

        return 6

    elif route_distance_km < 60:

        return 8

    elif route_distance_km < 100:

        return 10

    elif route_distance_km < 200:

        return 14

    elif route_distance_km < 300:

        return 18

    elif route_distance_km < 500:

        return 24

    else:

        return 30


# ==================================================
# SAMPLE COMPLETE ROUTE
# ==================================================

def sample_route_points(
    route_coordinates,
    number_of_points
):

    if not route_coordinates:

        return []

    if len(route_coordinates) <= number_of_points:

        return route_coordinates

    sampled = []

    last_index = (
        len(route_coordinates) - 1
    )

    for i in range(
        number_of_points
    ):

        index = round(

            i
            *
            last_index
            /
            (number_of_points - 1)

        )

        sampled.append(
            route_coordinates[index]
        )

    return sampled


# ==================================================
# CREATE UNIQUE STATION ID
# ==================================================

def get_station_id(station):

    station_id = station.get("ID")

    if station_id is not None:

        return str(station_id)

    address_info = station.get(
        "AddressInfo",
        {}
    )

    latitude = address_info.get(
        "Latitude"
    )

    longitude = address_info.get(
        "Longitude"
    )

    if (
        latitude is None
        or
        longitude is None
    ):

        return None

    return (

        str(round(latitude, 5))

        +

        "_"

        +

        str(round(longitude, 5))

    )


# ==================================================
# CONVERT STATION DATA
# ==================================================

def convert_station(
    station,
    sample_index
):

    address_info = station.get(
        "AddressInfo",
        {}
    )

    station_id = get_station_id(
        station
    )

    latitude = address_info.get(
        "Latitude"
    )

    longitude = address_info.get(
        "Longitude"
    )

    if (
        station_id is None
        or
        latitude is None
        or
        longitude is None
    ):

        return None

    return {

        "id":
            station_id,

        "name":
            address_info.get(
                "Title",
                "Unknown Charging Station"
            ),

        "latitude":
            latitude,

        "longitude":
            longitude,

        "address":
            address_info.get(
                "AddressLine1",
                ""
            ),

        "town":
            address_info.get(
                "Town",
                ""
            ),

        "state":
            address_info.get(
                "StateOrProvince",
                ""
            ),

        "sample_index":
            sample_index

    }


# ==================================================
# FIND STATIONS ALONG COMPLETE ROUTE
# ==================================================

def find_stations_along_route(

    route,

    corridor_km=10,

    max_candidates=40

):

    # ==================================================
    # GET ROUTE COORDINATES
    # ==================================================

    route_coordinates = (
        get_route_coordinates(
            route
        )
    )

    if not route_coordinates:

        return []


    # ==================================================
    # CALCULATE ROUTE LENGTH
    # ==================================================

    route_distance_km = (
        calculate_route_length(
            route_coordinates
        )
    )


    # ==================================================
    # CHOOSE NUMBER OF SEARCH POINTS
    # ==================================================

    number_of_samples = (
        get_number_of_samples(
            route_distance_km
        )
    )


    # ==================================================
    # SAMPLE WHOLE ROUTE
    # ==================================================

    sample_points = (
        sample_route_points(

            route_coordinates,

            number_of_samples

        )
    )


    # ==================================================
    # STORE UNIQUE STATIONS
    # ==================================================

    all_stations = {}


    # ==================================================
    # SEARCH EACH PART OF ROUTE
    # ==================================================

    for sample_index, point in enumerate(
        sample_points
    ):

        latitude = point[0]

        longitude = point[1]


        stations = (
            find_stations_near_point(

                latitude,

                longitude,

                distance=corridor_km,

                maxresults=50

            )
        )


        # ------------------------------------------
        # PROCESS RESULTS
        # ------------------------------------------

        for station in stations:

            converted = (
                convert_station(

                    station,

                    sample_index

                )
            )


            if converted is None:

                continue


            station_id = (
                converted["id"]
            )


            # --------------------------------------
            # REMOVE DUPLICATES
            # --------------------------------------

            if station_id not in all_stations:

                all_stations[
                    station_id
                ] = converted


    # ==================================================
    # NO STATIONS FOUND
    # ==================================================

    if not all_stations:

        return []


    stations = list(
        all_stations.values()
    )


    # ==================================================
    # DISTRIBUTE STATIONS ACROSS ROUTE
    # ==================================================

    number_of_sections = min(

        number_of_samples,

        10

    )


    sections = [

        []

        for _ in range(
            number_of_sections
        )

    ]


    for station in stations:

        sample_index = (
            station["sample_index"]
        )


        section = (

            sample_index
            *
            number_of_sections
            //
            max(
                1,
                number_of_samples
            )

        )


        if section >= number_of_sections:

            section = (
                number_of_sections - 1
            )


        sections[
            section
        ].append(station)


    # ==================================================
    # SELECT STATIONS FROM ALL SECTIONS
    # ==================================================

    selected = []


    # ------------------------------------------
    # FIRST PASS
    # One station from each section
    # ------------------------------------------

    for section in sections:

        if section:

            selected.append(
                section[0]
            )


    # ------------------------------------------
    # SECOND PASS
    # More stations from each section
    # ------------------------------------------

    for section in sections:

        for station in section[1:]:

            if len(selected) >= max_candidates:

                break

            selected.append(
                station
            )


        if len(selected) >= max_candidates:

            break


    # ==================================================
    # FINAL FALLBACK
    # ==================================================

    if len(selected) < max_candidates:

        selected_ids = {

            station["id"]

            for station in selected

        }


        for station in stations:

            if station["id"] in selected_ids:

                continue


            selected.append(
                station
            )


            if len(selected) >= max_candidates:

                break


    return selected