"""Telemetry snapshots are passed through as dicts; this module exists for parity
with the spec layout and as the place to add stricter schemas later if needed."""
from rest_framework import serializers


class MetricsSnapshotSerializer(serializers.Serializer):
    """Loose passthrough — concrete shape comes from
    :func:`core.monitoring.telemetry.collect_snapshot`."""

    timestamp = serializers.CharField()
    cpu = serializers.DictField()
    memory = serializers.DictField()
    disk = serializers.DictField()
    gpu = serializers.DictField()
    uptime = serializers.DictField()
