"""Report generation module for login tracking dashboard."""
from .data_collector import ReportDataCollector
from .excel_generator import ExcelReportGenerator

__all__ = [
    'ReportDataCollector',
    'ExcelReportGenerator',
]
