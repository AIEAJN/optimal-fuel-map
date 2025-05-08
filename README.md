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

2. Set up environment variables:
Create a `.env` file in the project root with:
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
GET /fuelmap/{departureLocation}/{destinationLocation}/
```

Example:
```
GET /fuelmap/New York/Los Angeles/
```

Response:
```json
{
    "route": {
        "distance": 4500000,  // in meters
        "duration": 144000,   // in seconds
        "steps": [...]        // detailed route steps
    },
    "fuel_stops": [
        {
            "location": "Chicago, IL",
            "price_per_gallon": 3.45,
            "distance": 1200000  // in meters
        },
        // ... more stops
    ],
    "total_cost": 450.75,
    "total_distance": 4500000,
    "estimated_fuel_used": 450000
}
```

## Notes

- The API uses OpenRouteService for routing
- Fuel prices are updated daily
- All distances are in meters
- All costs are in USD
