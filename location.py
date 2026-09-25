from streamlit_js_eval import get_geolocation


def get_gps_location():

    location = get_geolocation()

    if location is None:
        return None, None, None, "Waiting for GPS permission..."

    if "error" in location:

        error = location["error"]

        return (
            None,
            None,
            None,
            error.get(
                "message",
                "Unable to get your location."
            )
        )

    coords = location.get("coords")

    if coords is None:

        return (
            None,
            None,
            None,
            "GPS coordinates were not returned."
        )

    latitude = coords.get("latitude")
    longitude = coords.get("longitude")
    accuracy = coords.get("accuracy")

    if latitude is None or longitude is None:

        return (
            None,
            None,
            None,
            "Latitude or longitude is missing."
        )

    return latitude, longitude, accuracy, None