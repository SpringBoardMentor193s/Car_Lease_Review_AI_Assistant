from app.services.vin_lookup import lookup_vehicle_by_vin

vin = "JTDBR32E720123456"
result = lookup_vehicle_by_vin(vin)

print(result)
