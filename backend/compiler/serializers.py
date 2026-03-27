"""
BrailleCode API Serializers
"""

from rest_framework import serializers


class SourceCodeSerializer(serializers.Serializer):
    """Request: user sends English source code."""
    source = serializers.CharField(
        required=True,
        help_text="English source code to compile and/or execute",
    )


class TranslateResponseSerializer(serializers.Serializer):
    """Response: Braille translation result."""
    braille = serializers.CharField()
    english = serializers.CharField()


class CompileResponseSerializer(serializers.Serializer):
    """Response: full compilation + execution result."""
    success = serializers.BooleanField()
    braille = serializers.CharField()
    output = serializers.ListField(child=serializers.CharField())
    variables = serializers.DictField()
    ast = serializers.DictField()
    analysis = serializers.DictField()
    errors = serializers.ListField(child=serializers.DictField())
    tokens = serializers.ListField(child=serializers.DictField())
