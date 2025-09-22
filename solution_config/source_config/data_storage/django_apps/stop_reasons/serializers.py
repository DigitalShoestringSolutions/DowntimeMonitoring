from rest_framework import serializers

from . import models


class ReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Reason
        fields = ('id', 'text', 'category')

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        fields = ('id', 'text', 'colour')
