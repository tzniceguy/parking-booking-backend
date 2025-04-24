from rest_framework import serializers
from .models import ParkingLot

class ParkingLotSerializers(serializers.ModelSerializer):
    operator_name = serializers.CharField(source="operator.company_name", read_only=True)

    class Meta:
        model = ParkingLot
        fields = "__all__"
        read_only_fields = ("id", "created_at")