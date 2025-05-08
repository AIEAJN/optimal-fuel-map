import requests
from django.http import JsonResponse, HttpResponseBadRequest
from django.views import View
import json
import geopy.distance as geo
import os
import csv
import polyline
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import re

# I think that for not repetitive call to the api we should save station coordinates in a csv file

# Global Variables
ORS_API_KEY = "5b3ce3597851110001cf62484208863a99e649afaf9909e34d119e6a"
ORS_DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
VEHICLE_MPG = 10
MAX_RANGE = 500
FUEL_STATIONS = []


csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fuel-prices-for-be-assessment.csv")

# I think that for not repetitive call to the api we should save station coordinates in a csv file, this file can be create with CreateGeocodedCsv view
geocoded_csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "geocoded-fuel-stations.csv") 

def clean_address(raw_address):
    address = re.sub(r'(I|US|SR|State Route|Interstate)[-\s]?\d+|EXIT\s*\d+[A-Z\-]*|&', '', raw_address, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', address).strip()

def geocode_address(address, station, retry=3):
    geolocator = Nominatim(user_agent="fuel_locator")
    cleaned_address = clean_address(address)
    address = f"{cleaned_address}, {station['City'].strip()}, {station['State'].strip()}"
    for attempt in range(retry):
        try:
            location = geolocator.geocode(address, timeout=10)
            if location:
                print(f"✅ Found: {address} → ({location.latitude}, {location.longitude})")
                station_exists = False
                
                if os.path.exists(geocoded_csv_path):
                    with open(geocoded_csv_path, 'r', newline='') as csvfile:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            if (row['OPIS Truckstop ID'] == station['OPIS Truckstop ID'] and 
                                row['Address'] == station['Address']):
                                station_exists = True
                                break
                else:
                    with open(geocoded_csv_path, 'w', newline='') as csvfile:
                        fieldnames = ['OPIS Truckstop ID', 'Truckstop Name', 'Address', 'City', 'State', 
                                     'Rack ID', 'Retail Price', 'Latitude', 'Longitude']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                
                if not station_exists:
                    with open(geocoded_csv_path, 'a', newline='') as csvfile:
                        fieldnames = ['OPIS Truckstop ID', 'Truckstop Name', 'Address', 'City', 'State', 
                                     'Rack ID', 'Retail Price', 'Latitude', 'Longitude']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        
                        row = {
                            'OPIS Truckstop ID': station['OPIS Truckstop ID'].strip(),
                            'Truckstop Name': station['Truckstop Name'].strip(),
                            'Address': station['Address'].strip(),
                            'City': station['City'].strip(),
                            'State': station['State'].strip(),
                            'Rack ID': station['Rack ID'].strip(),
                            'Retail Price': station['Retail Price'].strip(),
                            'Latitude': location.latitude,
                            'Longitude': location.longitude
                        }
                        writer.writerow(row)
                return (location.latitude, location.longitude)
            else:
                print(f"❌ Not found: {address}")
                return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"⚠️ Attempt {attempt+1} failed for '{address}': {e}")
            time.sleep(1)
    return None

class CreateGeocodedCsv(View):
    def post(self, request):
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            FUELS = list(reader)
        
        for station in FUELS:
            address = f"{station['Address'].strip()}, {station['City'].strip()}, {station['State']}"
            geocode_address(address, station)
            
        return JsonResponse({'status': 'success', 'stations_processed': len(FUELS)})



def nearest_station(coord, stations, radius_miles=10):
    """
    Find the nearest fuel station with the lowest price within a given radius.
    
    # Args:====
        coord (tuple): Latitude and longitude coordinates (lat, lon)
        stations (list): List of stations to search from
        radius_miles (float): Search radius in miles
        
    Returns:
        dict or None: The nearest station with distance added, or None if no station found
    """
    best_station = None
    

    # Use list comprehension to create a list of stations with distance and price
    stations_with_distance = []
    for station in stations:
        try:
            distance = geo.distance(coord, (float(station['Latitude']), float(station['Longitude']))).miles
            if distance <= radius_miles:
                station_copy = station.copy()
                station_copy["distance"] = distance
                stations_with_distance.append(station_copy)
        except (ValueError, TypeError):
            pass
    
    best_station = min(
        stations_with_distance, 
        key=lambda fuel_station: (float(fuel_station["Retail Price"]), fuel_station["distance"]),
        default=None
    ) if stations_with_distance else None
    return best_station

def geocode(address):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json&limit=1"
        headers = {
            'User-Agent': 'FuelRouteOptimizer/1.0'
        }
        response = requests.get(url, headers=headers)
        res = response.json()
        if res:
            return float(res[0]["lat"]), float(res[0]["lon"])
        return None
    except (requests.exceptions.RequestException, ValueError, KeyError, IndexError):
        return None


with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "geocoded-fuel-stations.csv"), 'r') as f:
    reader = csv.DictReader(f)
    FUEL_STATIONS = list(reader)

class RouteView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            start = data.get("start")
            end = data.get("end")
            
            if not start or not end:
                return JsonResponse({"error": "Start and end locations are required"}, status=400)

        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON input.")

        start_coords = geocode(start)
        end_coords = geocode(end)

        if not start_coords or not end_coords:
            return JsonResponse({"error": "Could not geocode start or end location. Please check the addresses and try again."}, status=400)

        headers = {"Authorization": ORS_API_KEY}
        payload = {
            "coordinates": [[start_coords[1], start_coords[0]], [end_coords[1], end_coords[0]]]
        }
        
        try:
            ors_res = requests.post(ORS_DIRECTIONS_URL, json=payload, headers=headers)
            ors_res.raise_for_status()
            data = ors_res.json()
            
            if "routes" not in data:
                return JsonResponse({"error": "Invalid response from routing service"}, status=500)
        
        except requests.exceptions.RequestException:
            return JsonResponse({"error": "Failed to get route directions"}, status=500)

        routes = data["routes"][0]
        
        total_distance_meters = routes['summary']['distance']
        print(f"🔍 Total distance meters: {total_distance_meters}")
        total_distance_miles = total_distance_meters * 0.000621371
        print(f"🔍 Total distance miles: {total_distance_miles}")
        num_stops_needed = max(0, int(total_distance_miles / MAX_RANGE))
        print(f"🔍 Number of stops needed: {num_stops_needed}")
        geometry = polyline.decode(routes['geometry'])
        
        fuel_stops = []
        current_range = MAX_RANGE  # Start with a full tank
        total_fuel_cost = 0
        last_stop_coords = start_coords
        
        sample_interval = max(1, len(geometry) // (num_stops_needed + 1))
        print(f"🔍 Sample interval: {sample_interval}")
        for i in range(0, len(geometry), sample_interval):
            print(f"🔍 Processing point {i} of {len(geometry)}")
            point = geometry[i]
            distance_from_last = geo.distance(last_stop_coords, point).miles
            if current_range - distance_from_last < 50 or (len(fuel_stops) < num_stops_needed and i >= len(geometry) - sample_interval):
                print(f"🔍 Finding nearest station for point {i}")
                best_station = nearest_station(point, FUEL_STATIONS, 20)
                if best_station:
                    gallons_needed = MAX_RANGE / VEHICLE_MPG
                    fuel_price = float(best_station["Retail Price"])
                    cost = gallons_needed * fuel_price
                    fuel_stops.append({
                        "station_name": best_station["Truckstop Name"],
                        "location": {
                            "lat": float(best_station["Latitude"]),
                            "lng": float(best_station["Longitude"])
                        },
                        "address": f"{best_station['Address']}, {best_station['City']}, {best_station['State']}",
                        "price_per_gallon": fuel_price,
                        "gallons": gallons_needed,
                        "cost": cost,
                        "distance_from_start": distance_from_last
                    })
                    total_fuel_cost += cost
                    current_range = MAX_RANGE
                    last_stop_coords = (float(best_station["Latitude"]), float(best_station["Longitude"]))
            current_range -= distance_from_last
        
        total_gallons_used = total_distance_miles / VEHICLE_MPG
        
        return JsonResponse({
            "status": "success",
            "route": {
                "distance_miles": round(total_distance_miles, 2),
                "duration_minutes": round(routes['summary']['duration'] / 60, 2),
                "fuel_stops": fuel_stops,
                "total_fuel_cost": round(total_fuel_cost, 2),
                "total_gallons": round(total_gallons_used, 2)
            },
            "message": "Route calculated with optimal fuel stops"
        })
