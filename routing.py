import requests
import streamlit as st


GEOAPIFY_API_KEY = st.secrets["GEOAPIFY_API_KEY"]


def geocode_destination(destination):

    url = "https://api.geoapify.com/v1/geocode/search"

    params = {
        "text": destination,
        "format": "json",
        "limit": 1,
        "apiKey": GEOAPIFY_API_KEY
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        if response.status_code != 200:
            return None

        data = response.json()

        results = data.get(
            "results",
            []
        )

        if not results:
            return None

        result = results[0]

        return {
            "latitude": result.get("lat"),
            "longitude": result.get("lon"),
            "address": result.get(
                "formatted",
                destination
            )
        }

    except requests.exceptions.RequestException:

        return None


def get_route(
    source_lat,
    source_lon,
    destination_lat,
    destination_lon
):

    url = "https://api.geoapify.com/v1/routing"

    waypoints = (
        f"{source_lat},{source_lon}|"
        f"{destination_lat},{destination_lon}"
    )

    params = {
        "waypoints": waypoints,
        "mode": "drive",
        "format": "geojson",
        "units": "metric",
        "apiKey": GEOAPIFY_API_KEY
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        if response.status_code != 200:
            return None

        return response.json()

    except requests.exceptions.RequestException:

        return None


def get_route_distance(
    source_lat,
    source_lon,
    destination_lat,
    destination_lon
):

    route = get_route(
        source_lat,
        source_lon,
        destination_lat,
        destination_lon
    )

    if route is None:
        return None

    try:

        properties = (
            route["features"][0]["properties"]
        )

        distance_meters = (
            properties.get("distance")
        )

        if distance_meters is None:
            return None

        return distance_meters / 1000

    except (
        KeyError,
        IndexError,
        TypeError
    ):

        return None


def get_route_matrix(
    source_lat,
    source_lon,
    stations
):

    if not stations:
        return []

    url = (
        "https://api.geoapify.com/v1/"
        "routematrix"
    )

    sources = [
        {
            "location": [
                source_lon,
                source_lat
            ]
        }
    ]

    targets = []

    for station in stations:

        targets.append(
            {
                "location": [
                    station["longitude"],
                    station["latitude"]
                ]
            }
        )

    payload = {
        "mode": "drive",
        "sources": sources,
        "targets": targets,
        "units": "metric"
    }

    params = {
        "apiKey": GEOAPIFY_API_KEY
    }

    try:

        response = requests.post(
            url,
            params=params,
            json=payload,
            timeout=20
        )

        if response.status_code != 200:
            return []

        data = response.json()

        matrix = data.get(
            "sources_to_targets",
            []
        )

        if not matrix:
            return []

        return matrix[0]

    except (
        requests.exceptions.RequestException,
        ValueError
    ):

        return []


def get_route_via_station(
    source_lat,
    source_lon,
    station_lat,
    station_lon,
    destination_lat,
    destination_lon
):

    url = "https://api.geoapify.com/v1/routing"

    waypoints = (
        f"{source_lat},{source_lon}|"
        f"{station_lat},{station_lon}|"
        f"{destination_lat},{destination_lon}"
    )

    params = {
        "waypoints": waypoints,
        "mode": "drive",
        "format": "geojson",
        "units": "metric",
        "intermediate_waypoint_mode": "stopover",
        "apiKey": GEOAPIFY_API_KEY
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        if response.status_code != 200:
            return None

        return response.json()

    except requests.exceptions.RequestException:

        return None