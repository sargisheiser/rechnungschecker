"""OCR service for extracting text from scanned PDFs."""

import io
import tempfile
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class OCRService:
    """Service for extracting text from PDFs using OCR."""

    # DPI for rendering PDF pages as images
    DEFAULT_DPI = 300

    # Tesseract language configuration for German
    LANG = "deu+eng"

    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize OCR service.

        Args:
            tesseract_cmd: Path to tesseract executable (optional)
        """
        if tesseract_cmd and TESSERACT_AVAILABLE:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    @property
    def is_available(self) -> bool:
        """Check if OCR is available."""
        if not TESSERACT_AVAILABLE:
            return False
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def extract_text_from_pdf(
        self,
        pdf_content: bytes,
        use_ocr: bool = True,
        dpi: int = DEFAULT_DPI,
    ) -> str:
        """
        Extract text from PDF, using OCR if needed.

        Args:
            pdf_content: PDF file content as bytes
            use_ocr: Whether to use OCR for scanned pages
            dpi: DPI for rendering pages as images

        Returns:
            Extracted text from all pages
        """
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        all_text = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Try to extract text directly first
            text = page.get_text("text").strip()

            # If no text found and OCR is enabled, use OCR
            if not text and use_ocr and self.is_available:
                text = self._ocr_page(page, dpi)

            all_text.append(text)

        doc.close()
        return "\n\n".join(all_text)

    def _ocr_page(self, page: fitz.Page, dpi: int = DEFAULT_DPI) -> str:
        """
        Apply OCR to a single PDF page.

        Args:
            page: PyMuPDF page object
            dpi: DPI for rendering

        Returns:
            Extracted text from OCR
        """
        if not TESSERACT_AVAILABLE:
            return ""

        # Render page as image
        zoom = dpi / 72  # 72 is the default PDF DPI
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Apply OCR
        try:
            text = pytesseract.image_to_string(img, lang=self.LANG)
            return text.strip()
        except Exception:
            # Fall back to basic OCR without language pack
            try:
                text = pytesseract.image_to_string(img)
                return text.strip()
            except Exception:
                return ""

    def extract_text_from_image(self, image_content: bytes) -> str:
        """
        Extract text from an image file.

        Args:
            image_content: Image file content as bytes

        Returns:
            Extracted text
        """
        if not TESSERACT_AVAILABLE:
            return ""

        try:
            img = Image.open(io.BytesIO(image_content))
            text = pytesseract.image_to_string(img, lang=self.LANG)
            return text.strip()
        except Exception:
            return ""

    def is_scanned_pdf(self, pdf_content: bytes) -> bool:
        """
        Detect if a PDF is primarily scanned (image-based).

        Args:
            pdf_content: PDF file content as bytes

        Returns:
            True if the PDF appears to be scanned
        """
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        total_pages = len(doc)
        pages_without_text = 0

        for page_num in range(min(total_pages, 3)):  # Check first 3 pages
            page = doc[page_num]
            text = page.get_text("text").strip()
            if len(text) < 50:  # Very little text
                pages_without_text += 1

        doc.close()

        # If most checked pages have no text, it's likely scanned
        return pages_without_text > total_pages // 2
