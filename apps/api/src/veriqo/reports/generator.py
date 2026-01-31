"""PDF report generator using ReportLab."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from veriqo.reports.qr import generate_qr_code


@dataclass
class TestResultData:
    """Test result data for report."""

    name: str
    status: str
    notes: Optional[str] = None


@dataclass
class ReportData:
    """All data needed to generate a report."""

    job_id: str
    serial_number: str
    device_platform: str
    device_model: str

    # Workflow data
    intake_date: datetime
    completion_date: Optional[datetime]
    technician_name: str
    qc_technician_name: Optional[str]
    qc_initials: Optional[str]

    # Test results
    test_results: list[TestResultData]

    # Summary metrics
    total_tests: int
    passed_tests: int
    failed_tests: int

    # Report metadata
    scope: str
    variant: str
    access_token: str
    public_url: str


@dataclass
class BrandingConfig:
    """Branding configuration for reports."""

    brand_name: str
    logo_path: Optional[Path]
    primary_color: str
    secondary_color: str
    footer_text: Optional[str]


class PDFReportGenerator:
    """Generates white-label PDF reports using ReportLab."""

    def __init__(self, branding: BrandingConfig):
        self.branding = branding
        self.styles = self._setup_styles()
        self._executor = ThreadPoolExecutor(max_workers=4)

    def _setup_styles(self) -> dict:
        """Configure custom styles with branding."""
        styles = getSampleStyleSheet()

        # Convert hex to RGB
        primary = colors.HexColor(self.branding.primary_color)

        styles.add(
            ParagraphStyle(
                name="BrandTitle",
                parent=styles["Heading1"],
                textColor=primary,
                fontSize=24,
                spaceAfter=12,
            )
        )

        styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=styles["Heading2"],
                textColor=primary,
                fontSize=14,
                spaceBefore=12,
                spaceAfter=6,
            )
        )

        styles.add(
            ParagraphStyle(
                name="CenteredNormal",
                parent=styles["Normal"],
                alignment=TA_CENTER,
            )
        )

        return styles

    async def generate(self, data: ReportData, output_path: Path) -> Path:
        """Generate PDF asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self._generate_sync,
            data,
            output_path,
        )

    def _generate_sync(self, data: ReportData, output_path: Path) -> Path:
        """Synchronous PDF generation."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        story = []

        # Header with logo and brand
        story.extend(self._build_header(data))

        # Device information section
        story.extend(self._build_device_section(data))

        # Test results table
        story.extend(self._build_results_table(data))

        # QC sign-off
        if data.qc_initials:
            story.extend(self._build_qc_section(data))

        # QR code for public access
        story.extend(self._build_qr_section(data))

        # Footer
        story.extend(self._build_footer())

        doc.build(story)
        return output_path

    def _build_header(self, data: ReportData) -> list:
        """Build report header."""
        elements = []

        # Logo or brand name
        if self.branding.logo_path and self.branding.logo_path.exists():
            logo = RLImage(
                str(self.branding.logo_path), width=2 * inch, height=0.75 * inch
            )
            elements.append(logo)
        else:
            elements.append(
                Paragraph(self.branding.brand_name, self.styles["BrandTitle"])
            )

        elements.append(Spacer(1, 0.25 * inch))

        # Report title
        scope_titles = {
            "master": "Verification Certificate",
            "intake": "Intake Report",
            "reset": "Reset Verification",
            "functional": "Functional Test Report",
            "qc": "Quality Control Report",
        }
        title = scope_titles.get(data.scope, "Verification Report")
        elements.append(Paragraph(title, self.styles["Title"]))

        elements.append(Spacer(1, 0.25 * inch))

        return elements

    def _build_device_section(self, data: ReportData) -> list:
        """Build device information section."""
        elements = []

        elements.append(Paragraph("Device Information", self.styles["SectionHeader"]))

        info_data = [
            ["Serial Number:", data.serial_number],
            ["Platform:", data.device_platform],
            ["Model:", data.device_model],
            ["Intake Date:", data.intake_date.strftime("%Y-%m-%d %H:%M")],
            ["Technician:", data.technician_name],
        ]

        if data.completion_date:
            info_data.append(
                ["Completion Date:", data.completion_date.strftime("%Y-%m-%d %H:%M")]
            )

        table = Table(info_data, colWidths=[2 * inch, 4 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 0.25 * inch))

        return elements

    def _build_results_table(self, data: ReportData) -> list:
        """Build test results table."""
        elements = []

        elements.append(Paragraph("Test Results", self.styles["SectionHeader"]))

        # Summary
        summary = f"Passed: {data.passed_tests}/{data.total_tests} | Failed: {data.failed_tests}"
        elements.append(Paragraph(summary, self.styles["Normal"]))
        elements.append(Spacer(1, 0.1 * inch))

        if data.test_results:
            # Results table
            table_data = [["Test", "Status", "Notes"]]

            for result in data.test_results:
                table_data.append(
                    [
                        result.name,
                        result.status.upper(),
                        result.notes or "-",
                    ]
                )

            table = Table(table_data, colWidths=[2.5 * inch, 1 * inch, 2.5 * inch])
            table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            colors.HexColor(self.branding.primary_color),
                        ),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("ALIGN", (1, 0), (1, -1), "CENTER"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )

            elements.append(table)
        else:
            elements.append(Paragraph("No test results recorded.", self.styles["Normal"]))

        elements.append(Spacer(1, 0.25 * inch))

        return elements

    def _build_qc_section(self, data: ReportData) -> list:
        """Build QC sign-off section."""
        elements = []

        elements.append(Paragraph("Quality Control", self.styles["SectionHeader"]))

        qc_data = [
            ["QC Technician:", data.qc_technician_name or "N/A"],
            ["QC Initials:", data.qc_initials or "N/A"],
        ]

        table = Table(qc_data, colWidths=[2 * inch, 4 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 0.25 * inch))

        return elements

    def _build_qr_section(self, data: ReportData) -> list:
        """Build QR code section."""
        elements = []

        elements.append(Paragraph("Verify This Report", self.styles["SectionHeader"]))

        # Generate QR code
        qr_buffer = generate_qr_code(data.public_url, primary_color=self.branding.primary_color)
        qr_image = RLImage(qr_buffer, width=1.5 * inch, height=1.5 * inch)

        elements.append(qr_image)
        elements.append(
            Paragraph(f"Scan or visit: {data.public_url}", self.styles["CenteredNormal"])
        )

        elements.append(Spacer(1, 0.25 * inch))

        return elements

    def _build_footer(self) -> list:
        """Build report footer."""
        elements = []

        if self.branding.footer_text:
            elements.append(Spacer(1, 0.5 * inch))
            elements.append(Paragraph(self.branding.footer_text, self.styles["Normal"]))

        # Generation timestamp
        elements.append(Spacer(1, 0.25 * inch))
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        elements.append(
            Paragraph(
                f"Generated: {timestamp} | Powered by {self.branding.brand_name}",
                self.styles["CenteredNormal"],
            )
        )

        return elements


def get_report_generator() -> PDFReportGenerator:
    """Get report generator instance."""
    from veriqo.config import get_settings

    settings = get_settings()

    branding = BrandingConfig(
        brand_name=settings.brand_name,
        logo_path=settings.brand_logo_path,
        primary_color=settings.brand_primary_color,
        secondary_color=settings.brand_secondary_color,
        footer_text=settings.brand_footer_text,
    )

    return PDFReportGenerator(branding)
