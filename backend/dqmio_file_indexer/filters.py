from typing import ClassVar

from django_filters import rest_framework as filters

from .models import FileIndex


class FileIndexFilter(filters.FilterSet):
    min_size = filters.NumberFilter(label="Minimum file size", field_name="file_size", lookup_expr="gte")
    era = filters.CharFilter(label="Era", field_name="era", lookup_expr="exact")
    campaign = filters.CharFilter(label="Campaign", field_name="campaign", lookup_expr="contains")
    dataset = filters.CharFilter(label="Dataset", field_name="dataset", lookup_expr="contains")
    logical_file_name = filters.CharFilter(
        label="Logical file name", field_name="logical_file_name", lookup_expr="contains"
    )
    status = filters.CharFilter(label="ETL pipeline status", field_name="status", lookup_expr="exact")

    class Meta:
        model = FileIndex
        fields: ClassVar[list[str]] = [
            "min_size",
            "era",
            "campaign",
            "dataset",
            "logical_file_name",
            "status",
        ]
