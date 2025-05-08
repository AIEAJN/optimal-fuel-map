from django.core.management.base import BaseCommand
from fuel.models import Location, FuelPrice
import csv
from decimal import Decimal

class Command(BaseCommand):
    help = 'Load fuel prices from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        with open(options['csv_file'], 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Create or update location
                location, created = Location.objects.get_or_create(
                    name=row['city'],
                    defaults={
                        'latitude': float(row['latitude']),
                        'longitude': float(row['longitude']),
                        'state': row['state']
                    }
                )
                
                # Create fuel price
                FuelPrice.objects.create(
                    location=location,
                    price_per_gallon=Decimal(row['price'])
                )
                
                if created:
                    self.stdout.write(f'Created location: {location}')
                self.stdout.write(f'Added fuel price for {location}: ${row["price"]}/gallon') 