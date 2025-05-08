from django.db import models

# Create your models here.

class Location(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    state = models.CharField(max_length=2)  # US state code

    def __str__(self):
        return f"{self.name}, {self.state}"

class FuelPrice(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    price_per_gallon = models.DecimalField(max_digits=4, decimal_places=2)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.location.name}: ${self.price_per_gallon}/gallon"
