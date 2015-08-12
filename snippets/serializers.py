from django.forms import widgets
from rest_framework import serializers
from drf_compound_fields.fields import DictField
from snippets.models import WordCard


class WordCardSerializer(serializers.Serializer):
    
    word=serializers.CharField(max_length=100)
    dictdetails=serializers.CharField()


    def create(self, validated_data):
        """
        Create and return a new `Snippet` instance, given the validated data.
        """
        return WordCard.objects.create(**validated_data)

