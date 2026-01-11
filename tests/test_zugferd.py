"""Tests for ZUGFeRD extraction and validation services."""

import pytest

from app.services.validator.zugferd import (
    ZUGFeRDExtractor,
    ZUGFeRDProfile,
)


class TestZUGFeRDProfileDetection:
    """Tests for ZUGFeRD profile detection from XML content."""

    def test_detect_basic_profile(self) -> None:
        """Test detection of BASIC profile."""
        extractor = ZUGFeRDExtractor()
        xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100">
            <rsm:ExchangedDocumentContext>
                <ram:GuidelineSpecifiedDocumentContextParameter xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
                    <ram:ID>urn:factur-x.eu:1p0:basic</ram:ID>
                </ram:GuidelineSpecifiedDocumentContextParameter>
            </rsm:ExchangedDocumentContext>
        </rsm:CrossIndustryInvoice>"""

        profile, version = extractor._detect_profile(xml_content)
        assert profile == ZUGFeRDProfile.BASIC

    def test_detect_en16931_profile(self) -> None:
        """Test detection of EN16931 (COMFORT) profile."""
        extractor = ZUGFeRDExtractor()
        xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100">
            <rsm:ExchangedDocumentContext>
                <ram:GuidelineSpecifiedDocumentContextParameter xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
                    <ram:ID>urn:cen.eu:en16931:2017</ram:ID>
                </ram:GuidelineSpecifiedDocumentContextParameter>
            </rsm:ExchangedDocumentContext>
        </rsm:CrossIndustryInvoice>"""

        profile, version = extractor._detect_profile(xml_content)
        assert profile == ZUGFeRDProfile.EN16931

    def test_detect_xrechnung_profile(self) -> None:
        """Test detection of XRechnung profile in ZUGFeRD."""
        extractor = ZUGFeRDExtractor()
        xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100">
            <rsm:ExchangedDocumentContext>
                <ram:GuidelineSpecifiedDocumentContextParameter xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
                    <ram:ID>urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0</ram:ID>
                </ram:GuidelineSpecifiedDocumentContextParameter>
            </rsm:ExchangedDocumentContext>
        </rsm:CrossIndustryInvoice>"""

        profile, version = extractor._detect_profile(xml_content)
        assert profile == ZUGFeRDProfile.XRECHNUNG

    def test_detect_extended_profile(self) -> None:
        """Test detection of EXTENDED profile."""
        extractor = ZUGFeRDExtractor()
        xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100">
            <rsm:ExchangedDocumentContext>
                <ram:GuidelineSpecifiedDocumentContextParameter xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
                    <ram:ID>urn:factur-x.eu:1p0:extended</ram:ID>
                </ram:GuidelineSpecifiedDocumentContextParameter>
            </rsm:ExchangedDocumentContext>
        </rsm:CrossIndustryInvoice>"""

        profile, version = extractor._detect_profile(xml_content)
        assert profile == ZUGFeRDProfile.EXTENDED

    def test_detect_version_21(self) -> None:
        """Test detection of version 2.1."""
        extractor = ZUGFeRDExtractor()
        xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100">
            <rsm:ExchangedDocumentContext>
                <ram:GuidelineSpecifiedDocumentContextParameter xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
                    <ram:ID>urn:zugferd.de:2p1:basic</ram:ID>
                </ram:GuidelineSpecifiedDocumentContextParameter>
            </rsm:ExchangedDocumentContext>
        </rsm:CrossIndustryInvoice>"""

        profile, version = extractor._detect_profile(xml_content)
        assert version == "2.1"

    def test_detect_unknown_profile(self) -> None:
        """Test detection returns UNKNOWN for unrecognized profiles."""
        extractor = ZUGFeRDExtractor()
        xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100">
        </rsm:CrossIndustryInvoice>"""

        profile, version = extractor._detect_profile(xml_content)
        assert profile == ZUGFeRDProfile.UNKNOWN

    def test_detect_invalid_xml(self) -> None:
        """Test detection handles invalid XML gracefully."""
        extractor = ZUGFeRDExtractor()
        xml_content = b"not valid xml at all"

        profile, version = extractor._detect_profile(xml_content)
        assert profile == ZUGFeRDProfile.UNKNOWN
        assert version is None


class TestZUGFeRDExtractor:
    """Tests for ZUGFeRD PDF extraction."""

    def test_is_invoice_xml_positive(self) -> None:
        """Test invoice XML detection for valid content."""
        extractor = ZUGFeRDExtractor()

        # CII format
        assert extractor._is_invoice_xml(b"<CrossIndustryInvoice>content</CrossIndustryInvoice>")

        # Contains invoice marker
        assert extractor._is_invoice_xml(b"<Invoice>content</Invoice>")

        # ZUGFeRD marker
        assert extractor._is_invoice_xml(b"zugferd invoice data")

    def test_is_invoice_xml_negative(self) -> None:
        """Test invoice XML detection for non-invoice content."""
        extractor = ZUGFeRDExtractor()

        # Random XML
        assert not extractor._is_invoice_xml(b"<html><body>Hello</body></html>")

        # Empty
        assert not extractor._is_invoice_xml(b"")

    def test_known_xml_names(self) -> None:
        """Test that known XML attachment names are defined."""
        extractor = ZUGFeRDExtractor()

        assert "factur-x.xml" in extractor.KNOWN_XML_NAMES
        assert "zugferd-invoice.xml" in extractor.KNOWN_XML_NAMES
        assert "xrechnung.xml" in extractor.KNOWN_XML_NAMES


class TestZUGFeRDProfileEnum:
    """Tests for ZUGFeRD profile enumeration."""

    def test_profile_values(self) -> None:
        """Test that all expected profile values exist."""
        assert ZUGFeRDProfile.MINIMUM.value == "MINIMUM"
        assert ZUGFeRDProfile.BASIC_WL.value == "BASIC-WL"
        assert ZUGFeRDProfile.BASIC.value == "BASIC"
        assert ZUGFeRDProfile.EN16931.value == "EN16931"
        assert ZUGFeRDProfile.EXTENDED.value == "EXTENDED"
        assert ZUGFeRDProfile.XRECHNUNG.value == "XRECHNUNG"
        assert ZUGFeRDProfile.UNKNOWN.value == "UNKNOWN"

    def test_profile_string_conversion(self) -> None:
        """Test profile can be used as string."""
        profile = ZUGFeRDProfile.BASIC
        assert str(profile) == "ZUGFeRDProfile.BASIC"
        assert profile.value == "BASIC"
