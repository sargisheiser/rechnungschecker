"""KoSIT validator wrapper for XRechnung validation."""

import asyncio
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.core.exceptions import KoSITError

logger = logging.getLogger(__name__)
settings = get_settings()

# KoSIT report namespaces
NAMESPACES = {
    "rep": "http://www.xoev.de/de/validator/varl/1",
    "s": "http://purl.oclc.org/dml/svrl/",
    "in": "http://www.xoev.de/de/validator/framework/1/input",
}


@dataclass
class KoSITMessage:
    """Single validation message from KoSIT."""

    severity: str  # error, warning, info
    code: str
    text: str
    location: str | None = None


@dataclass
class KoSITResult:
    """Result from KoSIT validation."""

    is_valid: bool
    messages: list[KoSITMessage] = field(default_factory=list)
    recommendation: str | None = None  # accept, reject
    xrechnung_version: str | None = None
    raw_report: str | None = None
    processing_time_ms: int = 0


class KoSITValidator:
    """Wrapper for the KoSIT validation tool JAR."""

    VALIDATOR_VERSION = "1.5.0"

    def __init__(
        self,
        jar_path: Path | None = None,
        scenarios_path: Path | None = None,
        timeout: int | None = None,
    ) -> None:
        """Initialize KoSIT validator.

        Args:
            jar_path: Path to KoSIT validator JAR file
            scenarios_path: Path to scenarios.xml configuration
            timeout: Timeout in seconds for validation
        """
        self.jar_path = jar_path or settings.kosit_jar_path
        self.scenarios_path = scenarios_path or settings.kosit_scenarios_path
        self.timeout = timeout or settings.kosit_timeout_seconds

    def _get_java_executable(self) -> str | None:
        """Get path to Java executable."""
        import shutil
        import subprocess

        # Check Homebrew locations first (macOS) - these are more reliable
        homebrew_java_paths = [
            "/opt/homebrew/opt/openjdk/bin/java",  # Apple Silicon
            "/usr/local/opt/openjdk/bin/java",  # Intel Mac
            "/opt/homebrew/bin/java",
            "/usr/local/bin/java",
        ]
        for path in homebrew_java_paths:
            if Path(path).exists():
                return path

        # Fall back to system java in PATH, but verify it works
        # (macOS has a /usr/bin/java stub that doesn't actually work)
        java_path = shutil.which("java")
        if java_path:
            try:
                result = subprocess.run(
                    [java_path, "-version"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return java_path
            except (subprocess.TimeoutExpired, OSError) as e:
                logger.debug(f"Java version check failed: {e}")

        return None

    def _check_java_available(self) -> bool:
        """Check if Java runtime is available."""
        return self._get_java_executable() is not None

    async def validate_file(self, file_path: Path) -> KoSITResult:
        """Validate an XML file using KoSIT validator.

        Args:
            file_path: Path to the XML file to validate

        Returns:
            KoSITResult with validation outcome

        Raises:
            KoSITError: If validation fails to execute
        """
        import time

        start_time = time.time()

        if not self._check_java_available():
            logger.warning("Java not available, using fallback validation")
            return await self._fallback_validation(file_path)

        if not self.jar_path.exists():
            logger.warning(f"KoSIT JAR not found at {self.jar_path}, using fallback")
            return await self._fallback_validation(file_path)

        try:
            result = await self._run_kosit(file_path)
            result.processing_time_ms = int((time.time() - start_time) * 1000)
            return result
        except asyncio.TimeoutError:
            raise KoSITError(f"Validation timed out after {self.timeout} seconds")
        except Exception as e:
            logger.error(f"KoSIT validation failed: {e}")
            raise KoSITError(f"Validation failed: {str(e)}")

    async def _run_kosit(self, file_path: Path) -> KoSITResult:
        """Run KoSIT validator subprocess."""
        # Get Java executable
        java_exe = self._get_java_executable()
        if not java_exe:
            raise KoSITError("Java runtime not found")

        # Build command - use absolute path for repository
        kosit_dir = self.jar_path.parent.resolve()
        cmd = [
            java_exe,
            "-jar",
            str(self.jar_path.resolve()),
            "-s",
            str(self.scenarios_path.resolve()),
            "-r",
            str(kosit_dir),  # Repository is the kosit directory
            "-o",
            str(file_path.parent),  # Output report to same directory
            str(file_path),
        ]

        logger.debug(f"Running KoSIT: {' '.join(cmd)}")

        # Run subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            raise

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"KoSIT failed with code {process.returncode}: {error_msg}")
            # KoSIT returns non-zero for invalid documents, which is expected
            # Only raise if it's a real error (e.g., JAR not found)
            if "Error" in error_msg and "validation" not in error_msg.lower():
                raise KoSITError(f"KoSIT execution error: {error_msg}")

        # Parse the report file
        report_path = file_path.parent / f"{file_path.stem}-report.xml"
        if report_path.exists():
            return self._parse_report(report_path)

        # If no report, check stdout for basic result
        return self._parse_stdout(stdout.decode() if stdout else "")

    def _parse_report(self, report_path: Path) -> KoSITResult:
        """Parse KoSIT XML report file."""
        try:
            tree = ET.parse(report_path)
            root = tree.getroot()
        except ET.ParseError as e:
            logger.error(f"Failed to parse KoSIT report: {e}")
            return KoSITResult(is_valid=False, messages=[
                KoSITMessage(
                    severity="error",
                    code="PARSE-ERROR",
                    text=f"Fehler beim Parsen des Validierungsberichts: {e}",
                )
            ])

        raw_report = ET.tostring(root, encoding="unicode")
        messages: list[KoSITMessage] = []

        # Extract recommendation (accept/reject)
        recommendation = None
        rec_elem = root.find(".//rep:assessment/rep:accept", NAMESPACES)
        if rec_elem is not None:
            recommendation = "accept"
        else:
            rec_elem = root.find(".//rep:assessment/rep:reject", NAMESPACES)
            if rec_elem is not None:
                recommendation = "reject"

        # Extract messages from rep:message elements (KoSIT report format)
        for msg_elem in root.findall(".//rep:message", NAMESPACES):
            level = msg_elem.get("level", "error")
            code = msg_elem.get("code", "UNKNOWN")
            location = msg_elem.get("xpathLocation", "")
            text = msg_elem.text or ""

            # Map level to severity
            severity_map = {
                "error": "error",
                "warning": "warning",
                "info": "info",
                "information": "info",
            }
            severity = severity_map.get(level.lower(), "error")

            messages.append(KoSITMessage(
                severity=severity,
                code=code,
                text=text.strip(),
                location=location if location else None,
            ))

        # Also check for SVRL messages (fallback for different report formats)
        for failed in root.findall(".//s:failed-assert", NAMESPACES):
            messages.append(self._parse_svrl_message(failed, "error"))

        for report in root.findall(".//s:successful-report", NAMESPACES):
            # Successful reports are usually warnings or info
            messages.append(self._parse_svrl_message(report, "warning"))

        # Determine validity
        is_valid = recommendation == "accept" and not any(
            m.severity == "error" for m in messages
        )

        # Extract XRechnung version if present
        xrechnung_version = None
        scenario = root.find(".//rep:scenarioMatched", NAMESPACES)
        if scenario is not None:
            name = scenario.get("name", "")
            if "XRechnung" in name:
                # Extract version from scenario name
                parts = name.split()
                for part in parts:
                    if part[0].isdigit():
                        xrechnung_version = part
                        break

        return KoSITResult(
            is_valid=is_valid,
            messages=messages,
            recommendation=recommendation,
            xrechnung_version=xrechnung_version,
            raw_report=raw_report,
        )

    def _parse_svrl_message(self, elem: ET.Element, default_severity: str) -> KoSITMessage:
        """Parse a single SVRL message element."""
        # Get location
        location = elem.get("location", "")

        # Get message text
        text_elem = elem.find("s:text", NAMESPACES)
        text = text_elem.text if text_elem is not None and text_elem.text else ""

        # Get rule ID
        rule_id = elem.get("id", "UNKNOWN")

        # Determine severity from flag attribute if present
        flag = elem.get("flag", default_severity)
        severity_map = {
            "fatal": "error",
            "error": "error",
            "warning": "warning",
            "info": "info",
            "information": "info",
        }
        severity = severity_map.get(flag.lower(), default_severity)

        return KoSITMessage(
            severity=severity,
            code=rule_id,
            text=text.strip(),
            location=location if location else None,
        )

    def _parse_stdout(self, stdout: str) -> KoSITResult:
        """Parse KoSIT stdout when no report file available."""
        is_valid = "valid" in stdout.lower() and "invalid" not in stdout.lower()
        return KoSITResult(
            is_valid=is_valid,
            messages=[],
        )

    async def _fallback_validation(self, file_path: Path) -> KoSITResult:
        """Fallback validation when KoSIT is not available.

        Performs basic XML structure validation.
        """
        import time

        start_time = time.time()
        messages: list[KoSITMessage] = []

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except ET.ParseError as e:
            return KoSITResult(
                is_valid=False,
                messages=[
                    KoSITMessage(
                        severity="error",
                        code="XML-PARSE",
                        text=f"XML-Parsing fehlgeschlagen: {e}",
                    )
                ],
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

        # Check for XRechnung namespaces
        ns = root.tag.split("}")[0] + "}" if "}" in root.tag else ""
        is_ubl = "oasis" in ns.lower() or "ubl" in ns.lower()
        is_cii = "uncefact" in ns.lower() or "CrossIndustryInvoice" in root.tag

        if not (is_ubl or is_cii):
            messages.append(
                KoSITMessage(
                    severity="warning",
                    code="FORMAT-UNKNOWN",
                    text="Unbekanntes XML-Format. Erwartet: UBL oder CII.",
                )
            )

        # Basic field checks
        xrechnung_version = self._detect_xrechnung_version(root)

        # Add warning that full validation requires KoSIT
        messages.append(
            KoSITMessage(
                severity="info",
                code="FALLBACK-MODE",
                text="Eingeschränkte Validierung. Vollständige KoSIT-Validierung nicht verfügbar.",
            )
        )

        return KoSITResult(
            is_valid=len([m for m in messages if m.severity == "error"]) == 0,
            messages=messages,
            xrechnung_version=xrechnung_version,
            processing_time_ms=int((time.time() - start_time) * 1000),
        )

    def _detect_xrechnung_version(self, root: ET.Element) -> str | None:
        """Attempt to detect XRechnung version from document."""
        # Look for CustomizationID which contains version info
        for elem in root.iter():
            if "CustomizationID" in elem.tag and elem.text:
                if "xrechnung" in elem.text.lower():
                    # Extract version from CustomizationID
                    parts = elem.text.split("#")
                    if len(parts) > 1:
                        return parts[-1]
        return None
