def estimate_vehicle_price(make, model, year):
    """
    Simulated market price estimator.
    """

    base_prices = {
        "Toyota Camry": 24000,
        "Honda Civic": 22000,
        "Hyundai Verna": 18000,
        "Maruti Swift": 9000
    }

    key = f"{make} {model}"

    if key in base_prices:
        return base_prices[key]
    else:
        return 20000  # default estimate
