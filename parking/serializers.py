from rest_framework import serializers
from .models import ParkingLot

class ParkingLotSerializer(serializers.ModelSerializer):
    operator_name = serializers.CharField(source="operator.company_name", read_only=True)

    class Meta:
        model = ParkingLot
        fields = "__all__"
        read_only_fields = ("id", "created_at")

    def get_available_spots(self, obj):
        return obj.spots.filter(is_available=True).count()