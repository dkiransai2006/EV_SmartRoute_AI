def calculate_battery(
    battery_percentage,
    battery_capacity,
    consumption,
    reserve_percentage=15
):
    available_energy = (
        battery_capacity
        * battery_percentage
        / 100
    )

    estimated_range = (
        available_energy
        / consumption
    )

    usable_range = (
        estimated_range
        * (1 - reserve_percentage / 100)
    )

    return (
        available_energy,
        estimated_range,
        usable_range
    )


def can_reach(
    distance_km,
    usable_range
):
    return distance_km <= usable_range