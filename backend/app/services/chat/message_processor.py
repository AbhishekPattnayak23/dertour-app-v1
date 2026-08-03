import re
import uuid
import logging
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class ProcessedMessage:
    message_id: str
    original_content: str
    sanitized_content: str
    has_pii: bool
    pii_types_detected: list
    is_valid: bool
    validation_errors: list
    timestamp: datetime
    metadata: dict = field(default_factory=dict)


@dataclass
class AuditLog:
    log_id: str
    message_id: str
    action: str
    timestamp: datetime
    details: dict
    user_id: Optional[str] = None


class PIIDetector:
    """
    Detects Personally Identifiable Information (PII) in text content.
    Supports detection of common PII patterns including emails, phone numbers,
    SSNs, credit card numbers, IP addresses, and names.
    """

    PII_PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
        "phone_us": r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "ssn": r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
        "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        "date_of_birth": r"\b(?:0?[1-9]|1[0-2])[\/\-](?:0?[1-9]|[12]\d|3[01])[\/\-](?:19|20)\d{2}\b",
        "zip_code": r"\b\d{5}(?:-\d{4})?\b",
        "passport": r"\b[A-Z]{1,2}\d{6,9}\b",
        "drivers_license": r"\b[A-Z]{1,2}\d{5,8}\b",
    }

    REDACTION_PLACEHOLDER = {
        "email": "[EMAIL REDACTED]",
        "phone_us": "[PHONE REDACTED]",
        "ssn": "[SSN REDACTED]",
        "credit_card": "[CREDIT CARD REDACTED]",
        "ip_address": "[IP REDACTED]",
        "date_of_birth": "[DOB REDACTED]",
        "zip_code": "[ZIP REDACTED]",
        "passport": "[PASSPORT REDACTED]",
        "drivers_license": "[DL REDACTED]",
    }

    def __init__(self, custom_patterns: Optional[dict] = None):
        self.patterns = dict(self.PII_PATTERNS)
        if custom_patterns:
            self.patterns.update(custom_patterns)

        self._compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.patterns.items()
        }

    def detect(self, text: str) -> dict:
        """
        Detect PII in the given text.

        Returns:
            dict with keys:
                - has_pii (bool)
                - detected_types (list of str)
                - matches (dict mapping pii_type -> list of matched strings)
        """
        if not text or not isinstance(text, str):
            return {"has_pii": False, "detected_types": [], "matches": {}}

        detected_types = []
        matches = {}

        for pii_type, compiled_pattern in self._compiled_patterns.items():
            found = compiled_pattern.findall(text)
            if found:
                detected_types.append(pii_type)
                matches[pii_type] = found

        return {
            "has_pii": len(detected_types) > 0,
            "detected_types": detected_types,
            "matches": matches,
        }

    def redact(self, text: str) -> tuple:
        """
        Redact all detected PII from the given text.

        Returns:
            tuple: (redacted_text, list of pii_types_found)
        """
        if not text or not isinstance(text, str):
            return text, []

        redacted_text = text
        detected_types = []

        for pii_type, compiled_pattern in self._compiled_patterns.items():
            placeholder = self.REDACTION_PLACEHOLDER.get(pii_type, f"[{pii_type.upper()} REDACTED]")
            new_text, count = compiled_pattern.subn(placeholder, redacted_text)
            if count > 0:
                detected_types.append(pii_type)
                redacted_text = new_text

        return redacted_text, detected_types

    def add_pattern(self, name: str, pattern: str, placeholder: Optional[str] = None):
        """Add a custom PII pattern at runtime."""
        self.patterns[name] = pattern
        self._compiled_patterns[name] = re.compile(pattern, re.IGNORECASE)
        if placeholder:
            self.REDACTION_PLACEHOLDER[name] = placeholder


class MessageValidator:
    """
    Validates chat messages against configurable rules.
    """

    DEFAULT_MAX_LENGTH = 10000
    DEFAULT_MIN_LENGTH = 1

    def __init__(
        self,
        max_length: int = DEFAULT_MAX_LENGTH,
        min_length: int = DEFAULT_MIN_LENGTH,
        forbidden_patterns: Optional[list] = None,
        allowed_content_types: Optional[list] = None,
    ):
        self.max_length = max_length
        self.min_length = min_length
        self.forbidden_patterns = forbidden_patterns or []
        self.allowed_content_types = allowed_content_types or ["text"]

        self._compiled_forbidden = [
            re.compile(p, re.IGNORECASE) for p in self.forbidden_patterns
        ]

    def validate(self, content: str, content_type: str = "text") -> tuple:
        """
        Validate the message content.

        Returns:
            tuple: (is_valid: bool, errors: list of str)
        """
        errors = []

        if not isinstance(content, str):
            errors.append("Message content must be a string.")
            return False, errors

        if len(content) < self.min_length:
            errors.append(
                f"Message too short. Minimum length is {self.min_length} characters."
            )

        if len(content) > self.max_length:
            errors.append(
                f"Message too long. Maximum length is {self.max_length} characters."
            )

        if content_type not in self.allowed_content_types:
            errors.append(
                f"Content type '{content_type}' is not allowed. "
                f"Allowed types: {self.allowed_content_types}"
            )

        for pattern in self._compiled_forbidden:
            if pattern.search(content):
                errors.append(f"Message contains forbidden content.")
                break

        stripped = content.strip()
        if not stripped:
            errors.append("Message content cannot be empty or whitespace only.")

        is_valid = len(errors) == 0
        return is_valid, errors


class AuditLogger:
    """
    Records audit logs for message processing events.
    In production, this should be backed by a persistent store (DB, log aggregator, etc.).
    """

    def __init__(self):
        self._logs: list = []

    def log(
        self,
        message_id: str,
        action: str,
        details: dict,
        user_id: Optional[str] = None,
    ) -> AuditLog:
        log_entry = AuditLog(
            log_id=str(uuid.uuid4()),
            message_id=message_id,
            action=action,
            timestamp=datetime.utcnow(),
            details=details,
            user_id=user_id,
        )
        self._logs.append(log_entry)
        logger.info(
            "AUDIT | log_id=%s | message_id=%s | action=%s | user_id=%s | details=%s",
            log_entry.log_id,
            log_entry.message_id,
            log_entry.action,
            log_entry.user_id,
            log_entry.details,
        )
        return log_entry

    def get_logs_for_message(self, message_id: str) -> list:
        return [log for log in self._logs if log.message_id == message_id]

    def get_all_logs(self) -> list:
        return list(self._logs)


class MessageProcessor:
    """
    Orchestrates message validation, PII detection/redaction, and audit logging.

    Usage:
        processor = MessageProcessor()
        result = processor.process("Hello, my email is test@example.com", user_id="user_123")
        print(result.sanitized_content)  # "Hello, my email is [EMAIL REDACTED]"
    """

    def __init__(
        self,
        pii_detector: Optional[PIIDetector] = None,
        validator: Optional[MessageValidator] = None,
        audit_logger: Optional[AuditLogger] = None,
        redact_pii: bool = True,
        reject_on_pii: bool = False,
        max_message_length: int = MessageValidator.DEFAULT_MAX_LENGTH,
        min_message_length: int = MessageValidator.DEFAULT_MIN_LENGTH,
        forbidden_patterns: Optional[list] = None,
    ):
        self.pii_detector = pii_detector or PIIDetector()
        self.validator = validator or MessageValidator(
            max_length=max_message_length,
            min_length=min_message_length,
            forbidden_patterns=forbidden_patterns or [],
        )
        self.audit_logger = audit_logger or AuditLogger()
        self.redact_pii = redact_pii
        self.reject_on_pii = reject_on_pii

    def process(
        self,
        content: str,
        user_id: Optional[str] = None,
        content_type: str = "text",
        metadata: Optional[dict] = None,
    ) -> ProcessedMessage:
        """
        Process a single message through the full pipeline:
          1. Generate a unique message ID.
          2. Validate the message.
          3. Detect (and optionally redact) PII.
          4. Emit audit log entries.
          5. Return a ProcessedMessage result.

        Args:
            content:      Raw message content.
            user_id:      Optional identifier of the message sender.
            content_type: Content type of the message (default "text").
            metadata:     Optional arbitrary metadata to attach to the result.

        Returns:
            ProcessedMessage
        """
        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        metadata = metadata or {}

        self.audit_logger.log(
            message_id=message_id,
            action="message_received",
            details={"content_length": len(content) if content else 0, "content_type": content_type},
            user_id=user_id,
        )

        is_valid, validation_errors = self.validator.validate(content, content_type)

        if not is_valid:
            self.audit_logger.log(
                message_id=message_id,
                action="validation_failed",
                details={"errors": validation_errors},
                user_id=user_id,
            )
            return ProcessedMessage(
                message_id=message_id,
                original_content=content,
                sanitized_content=content,
                has_pii=False,
                pii_types_detected=[],
                is_valid=False,
                validation_errors=validation_errors,
                timestamp=timestamp,
                metadata=metadata,
            )

        detection_result = self.pii_detector.detect(content)
        has_pii = detection_result["has_pii"]
        pii_types_detected = detection_result["detected_types"]

        if has_pii:
            self.audit_logger.log(
                message_id=message_id,
                action="pii_detected",
                details={"pii_types": pii_types_detected},
                user_id=user_id,
            )

        if has_pii and self.reject_on_pii:
            rejection_error = "Message rejected: contains PII."
            self.audit_logger.log(
                message_id=message_id,
                action="message_rejected",
                details={"reason": rejection_error, "pii_types": pii_types_detected},
                user_id=user_id,
            )
            return ProcessedMessage(
                message_id=message_id,
                original_content=content,
                sanitized_content=content,
                has_pii=has_pii,
                pii_types_detected=pii_types_detected,
                is_valid=False,
                validation_errors=[rejection_error],
                timestamp=timestamp,
                metadata=metadata,
            )

        if has_pii and self.redact_pii:
            sanitized_content, _ = self.pii_detector.redact(content)
            self.audit_logger.log(
                message_id=message_id,
                action="pii_redacted",
                details={"pii_types": pii_types_detected},
                user_id=user_id,
            )
        else:
            sanitized_content = content

        self.audit_logger.log(
            message_id=message_id,
            action="message_processed",
            details={
                "has_pii": has_pii,
                "pii_types": pii_types_detected,
                "redacted": has_pii and self.redact_pii,
            },
            user_id=user_id,
        )

        return ProcessedMessage(
            message_id=message_id,
            original_content=content,
            sanitized_content=sanitized_content,
            has_pii=has_pii,
            pii_types_detected=pii_types_detected,
            is_valid=True,
            validation_errors=[],
            timestamp=timestamp,
            metadata=metadata,
        )

    def process_batch(
        self,
        messages: list,
        user_id: Optional[str] = None,
        content_type: str = "text",
    ) -> list:
        """
        Process a batch of messages.

        Args:
            messages:     List of raw message strings or dicts with 'content' key.
            user_id:      Optional sender identifier.
            content_type: Default content type for all messages.

        Returns:
            List of ProcessedMessage results.
        """
        results = []
        for item in messages:
            if isinstance(item, dict):
                content = item.get("content", "")
                ct = item.get("content_type", content_type)
                meta = item.get("metadata", {})
                uid = item.get("user_id", user_id)
            else:
                content = item
                ct = content_type
                meta = {}
                uid = user_id

            result = self.process(content, user_id=uid, content_type=ct, metadata=meta)
            results.append(result)

        return results

    def get_audit_logs(self, message_id: Optional[str] = None) -> list:
        """
        Retrieve audit logs, optionally filtered by message_id.
        """
        if message_id:
            return self.audit_logger.get_logs_for_message(message_id)
        return self.audit_logger.get_all_logs()