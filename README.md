# Optimal Fuel Map API

This Django-based API helps users find the most cost-effective fuel stops along their route in the USA, taking into account the vehicle's range and fuel efficiency.

## Features

- Route planning between two US locations
- Optimal fuel stop recommendations based on current prices
- Cost calculation for the entire journey
- Support for vehicles with 500-mile range
- Assumes 10 miles per gallon fuel efficiency

## Setup

1. Install dependencies:
```bash
poetry install
```


```
OPENROUTE_API_KEY=your_api_key_here
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Load fuel price data:
```bash
python manage.py load_fuel_prices path/to/your/fuel_prices.csv
```

5. Run the development server:
```bash
python manage.py runserver 8003
```

## API Usage

### Get Optimal Fuel Route

```
GET /fuelmap/

```

Example:
```
GET /fuelmap/
{
    "start":"location",
    "end": location
}
```

Response:
```json
{
    "status": "success",
    "route": {
        "distance_miles": 1143.05,
        "duration_minutes": 1173.22,
        "fuel_stops": [
            {
                "station_name": "BUSY CORNER TRUCK STOP AND MARKET",
                "location": {
                    "lat": 47.5477103,
                    "lng": -122.541408
                },
                "address": "I-24, EXIT 105 & US-41/SR-2, Manchester, TN",
                "price_per_gallon": 3.049,
                "gallons": 50.0,
                "cost": 152.45,
                "distance_from_start": 958.9041036182074
            }
        ],
        "total_fuel_cost": 152.45,
        "total_gallons": 114.3
    },
    "message": "Route calculated with optimal fuel stops"
}
```

## Notes

- The API uses OpenRouteService for routing
- Fuel prices are updated daily
- All distances are in meters
- All costs are in USD
