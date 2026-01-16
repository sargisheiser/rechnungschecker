"""Main conversion service orchestrating PDF to e-invoice conversion."""

from enum import Enum
from typing import Optional
from dataclasses import dataclass

from app.services.converter.ocr import OCRService
from app.services.converter.extractor import InvoiceExtractor, InvoiceData
from app.services.converter.generator import XRechnungGenerator, ZUGFeRDGenerator


class OutputFormat(str, Enum):
    """Supported output formats."""

    XRECHNUNG = "xrechnung"
    ZUGFERD = "zugferd"


class ZUGFeRDProfile(str, Enum):
    """ZUGFeRD profile levels."""

    MINIMUM = "MINIMUM"
    BASIC = "BASIC"
    EN16931 = "EN16931"
    EXTENDED = "EXTENDED"


@dataclass
class ConversionResult:
    """Result of a PDF to e-invoice conversion."""

    success: bool
    output_format: OutputFormat
    content: bytes
    filename: str
    extracted_data: InvoiceData
    warnings: list[str]
    error: Optional[str] = None
    xml_content: Optional[bytes] = None  # Always contains the XML, even for ZUGFeRD PDFs


class ConversionService:
    """Service for converting PDFs to e-invoice formats."""

    def __init__(
        self,
        tesseract_cmd: Optional[str] = None,
    ):
        """
        Initialize conversion service.

        Args:
            tesseract_cmd: Optional path to tesseract executable
        """
        self.ocr_service = OCRService(tesseract_cmd=tesseract_cmd)
        self.extractor = InvoiceExtractor(ocr_service=self.ocr_service)
        self.xrechnung_generator = XRechnungGenerator()

    def convert(
        self,
        pdf_content: bytes,
        output_format: OutputFormat = OutputFormat.XRECHNUNG,
        zugferd_profile: ZUGFeRDProfile = ZUGFeRDProfile.EN16931,
        embed_in_pdf: bool = True,
    ) -> ConversionResult:
        """
        Convert a PDF invoice to e-invoice format.

        Args:
            pdf_content: PDF file content as bytes
            output_format: Desired output format (XRechnung or ZUGFeRD)
            zugferd_profile: ZUGFeRD profile level (if ZUGFeRD output)
            embed_in_pdf: Whether to embed XML in PDF (ZUGFeRD only)

        Returns:
            ConversionResult with the converted invoice
        """
        warnings: list[str] = []

        # Check if PDF is scanned
        if self.ocr_service.is_scanned_pdf(pdf_content):
            if not self.ocr_service.is_available:
                return ConversionResult(
                    success=False,
                    output_format=output_format,
                    content=b"",
                    filename="",
                    extracted_data=InvoiceData(),
                    warnings=[],
                    error="OCR ist nicht verfuegbar. Installieren Sie Tesseract fuer gescannte PDFs.",
                )
            warnings.append(
                "PDF scheint gescannt zu sein. OCR wird verwendet - "
                "bitte pruefen Sie die extrahierten Daten."
            )

        # Extract invoice data
        try:
            data = self.extractor.extract_from_pdf(pdf_content)
            warnings.extend(data.warnings)
        except Exception as e:
            return ConversionResult(
                success=False,
                output_format=output_format,
                content=b"",
                filename="",
                extracted_data=InvoiceData(),
                warnings=warnings,
                error=f"Fehler bei der Datenextraktion: {str(e)}",
            )

        # Check extraction quality
        if data.confidence < 0.3:
            warnings.append(
                "Niedrige Extraktionsqualitaet. Bitte pruefen Sie alle Felder."
            )

        # Generate output
        try:
            xml_content: bytes
            if output_format == OutputFormat.XRECHNUNG:
                content = self.xrechnung_generator.generate(data)
                xml_content = content
                filename = f"xrechnung_{data.invoice_number or 'invoice'}.xml"
            else:
                generator = ZUGFeRDGenerator(profile=zugferd_profile.value)
                xml_content = generator.generate_xml(data)
                if embed_in_pdf:
                    content = generator.generate_pdf(data, source_pdf=pdf_content)
                    filename = f"zugferd_{data.invoice_number or 'invoice'}.pdf"
                else:
                    content = xml_content
                    filename = f"factur-x_{data.invoice_number or 'invoice'}.xml"

            return ConversionResult(
                success=True,
                output_format=output_format,
                content=content,
                filename=filename,
                extracted_data=data,
                warnings=warnings,
                xml_content=xml_content,
            )

        except Exception as e:
            return ConversionResult(
                success=False,
                output_format=output_format,
                content=b"",
                filename="",
                extracted_data=data,
                warnings=warnings,
                error=f"Fehler bei der Generierung: {str(e)}",
            )

    def preview_extraction(self, pdf_content: bytes) -> InvoiceData:
        """
        Preview extracted data without generating output.

        Args:
            pdf_content: PDF file content as bytes

        Returns:
            Extracted invoice data
        """
        return self.extractor.extract_from_pdf(pdf_content)

    async def preview_extraction_async(self, pdf_content: bytes) -> InvoiceData:
        """
        Preview extracted data using AI-enhanced extraction if available.

        Args:
            pdf_content: PDF file content as bytes

        Returns:
            Extracted invoice data
        """
        return await self.extractor.extract_from_pdf_async(pdf_content)

    async def convert_async(
        self,
        pdf_content: bytes,
        output_format: OutputFormat = OutputFormat.XRECHNUNG,
        zugferd_profile: ZUGFeRDProfile = ZUGFeRDProfile.EN16931,
        embed_in_pdf: bool = True,
    ) -> ConversionResult:
        """
        Convert a PDF invoice to e-invoice format using AI-enhanced extraction.

        Args:
            pdf_content: PDF file content as bytes
            output_format: Desired output format (XRechnung or ZUGFeRD)
            zugferd_profile: ZUGFeRD profile level (if ZUGFeRD output)
            embed_in_pdf: Whether to embed XML in PDF (ZUGFeRD only)

        Returns:
            ConversionResult with the converted invoice
        """
        warnings: list[str] = []

        # Check if PDF is scanned
        if self.ocr_service.is_scanned_pdf(pdf_content):
            if not self.ocr_service.is_available and not self.extractor.ai_available:
                return ConversionResult(
                    success=False,
                    output_format=output_format,
                    content=b"",
                    filename="",
                    extracted_data=InvoiceData(),
                    warnings=[],
                    error="OCR ist nicht verfuegbar. Installieren Sie Tesseract fuer gescannte PDFs.",
                )
            if not self.extractor.ai_available:
                warnings.append(
                    "PDF scheint gescannt zu sein. OCR wird verwendet - "
                    "bitte pruefen Sie die extrahierten Daten."
                )

        # Extract invoice data (using AI if available)
        try:
            data = await self.extractor.extract_from_pdf_async(pdf_content)
            warnings.extend(data.warnings)
        except Exception as e:
            return ConversionResult(
                success=False,
                output_format=output_format,
                content=b"",
                filename="",
                extracted_data=InvoiceData(),
                warnings=warnings,
                error=f"Fehler bei der Datenextraktion: {str(e)}",
            )

        # Check extraction quality
        if data.confidence < 0.3:
            warnings.append(
                "Niedrige Extraktionsqualitaet. Bitte pruefen Sie alle Felder."
            )

        # Generate output
        try:
            xml_content: bytes
            if output_format == OutputFormat.XRECHNUNG:
                content = self.xrechnung_generator.generate(data)
                xml_content = content
                filename = f"xrechnung_{data.invoice_number or 'invoice'}.xml"
            else:
                generator = ZUGFeRDGenerator(profile=zugferd_profile.value)
                xml_content = generator.generate_xml(data)
                if embed_in_pdf:
                    content = generator.generate_pdf(data, source_pdf=pdf_content)
                    filename = f"zugferd_{data.invoice_number or 'invoice'}.pdf"
                else:
                    content = xml_content
                    filename = f"factur-x_{data.invoice_number or 'invoice'}.xml"

            return ConversionResult(
                success=True,
                output_format=output_format,
                content=content,
                filename=filename,
                extracted_data=data,
                warnings=warnings,
                xml_content=xml_content,
            )

        except Exception as e:
            return ConversionResult(
                success=False,
                output_format=output_format,
                content=b"",
                filename="",
                extracted_data=data,
                warnings=warnings,
                error=f"Fehler bei der Generierung: {str(e)}",
            )

    @property
    def ocr_available(self) -> bool:
        """Check if OCR is available."""
        return self.ocr_service.is_available

    @property
    def ai_available(self) -> bool:
        """Check if AI extraction is available."""
        return self.extractor.ai_available
