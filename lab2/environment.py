import random

def generate_sensor_data(dormancy_bias=0.8):
    """
    dormancy_bias: 0.0 to 1.0
        - 1.0 → very likely dormant readings
        - 0.0 → very likely high readings (active/erupting)
    """

    def biased_random(low, high, dormancy_bias=(1-dormancy_bias)):
        """
        Returns a value between low and high.
        dormancy_bias: 0.0 (active) → 1.0 (dormant)
        """
        # Generate random number 0..1
        r = random.random()
        # Apply bias: higher dormancy_bias pushes values toward low end
        r = r ** (1 / (dormancy_bias + 0.001))  # Add small epsilon to avoid division by zero
        return round(low + (high - low) * r, 2)

    # Sensor readings
    co2 = biased_random(20, 1000)               # ppm (parts per million)
    so2 = biased_random(10, 700)                # ppm
    vibration = biased_random(0.0, 8.0)         # mm/s
    temperature = biased_random(25, 500)        # Celsius
    area_affected = biased_random(0.0, 50.0)    # km²
    lava_flow = 0.0                             # m³/s
    ash_density = 0.0                           # g/m³


    # Normal scoring for non-erupting states
    score = 0
    if co2 > 200: score += 2      # CO2 is a strong precursor
    if so2 > 150: score += 2      # SO2 is also strong
    if vibration > 2.0: score += 1
    if temperature > 80: score += 1
    # Max score now = 6
    
    if score <= 2:
        status = "dormant"
        ash_density = round(random.uniform(0, 0.1), 3)
    elif score <= 4:
        status = "active"
        ash_density = round(random.uniform(0.1, 2.0), 2)
    else:
        status = "erupting"  # Multiple indicators without lava
        lava_flow = round(random.uniform(0.1, 1000), 2)  
        ash_density = round(random.uniform(2.0, 50.0), 2)  
    emergency = status == "erupting"


    return {
        "status": status,
        "CO2_ppm": co2,
        "SO2_ppm": so2,
        "vibration_mm_s": vibration,
        "temperature_C": temperature,
        "ash_density_g_m3": ash_density,
        "lava_flow_m3_s": lava_flow,
        "emergency": emergency,
        "area_affected_km2": area_affected
    }