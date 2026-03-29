"""
Security Manager for BillGenerator Unified
Handles file validation, input sanitization, and security checks
"""
import os
import hashlib
import magic
import tempfile
import secrets
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
import logging
import re
import mimetypes

logger = logging.getLogger(__name__)

@dataclass
class SecurityConfig:
    """Security configuration"""
    max_file_size_mb: int = 50
    max_total_size_mb: int = 500
    allowed_extensions: List[str] = None
    allowed_mime_types: List[str] = None
    blocked_patterns: List[str] = None
    scan_for_malware: bool = False
    validate_content: bool = True
    temp_dir: Optional[str] = None
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = ['.xlsx', '.xls', '.csv', '.txt', '.html', '.pdf', '.doc', '.docx']
        
        if self.allowed_mime_types is None:
            self.allowed_mime_types = [
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-excel',
                'text/csv',
                'text/plain',
                'text/html',
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]
        
        if self.blocked_patterns is None:
            self.blocked_patterns = [
                r'<script[^>]*>.*?</script>',  # Scripts
                r'javascript:',                    # JavaScript URLs
                r'vbscript:',                     # VBScript URLs
                r'onload=',                       # Event handlers
                r'onerror=',                       # Event handlers
                r'eval\s*\(',                    # eval() function
                r'document\.cookie',              # Cookie access
            ]

@dataclass
class ValidationResult:
    """Result of security validation"""
    is_valid: bool
    error_message: str = ""
    file_size: int = 0
    file_type: str = ""
    mime_type: str = ""
    checksum: str = ""
    risk_score: float = 0.0

class SecurityManager:
    """Advanced security management for file operations"""
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self._blocked_files: Dict[str, str] = {}  # checksum -> reason
        self._scanned_files: Dict[str, ValidationResult] = {}
        
        # Compile regex patterns for performance
        self._compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                for pattern in self.config.blocked_patterns]
    
    def validate_file(self, file_path: Union[str, Path], file_content: Optional[bytes] = None) -> ValidationResult:
        """Comprehensive file validation"""
        file_path = Path(file_path)
        
        try:
            # Basic checks
            if not file_path.exists():
                return ValidationResult(False, "File does not exist")
            
            # Get file info
            file_size = file_path.stat().st_size
            checksum = self._calculate_checksum(file_path)
            
            # Check if already blocked
            if checksum in self._blocked_files:
                return ValidationResult(False, f"File blocked: {self._blocked_files[checksum]}")
            
            # Check cached result
            if checksum in self._scanned_files:
                return self._scanned_files[checksum]
            
            # Size validation
            if file_size > self.config.max_file_size_mb * 1024 * 1024:
                return ValidationResult(False, f"File too large: {file_size / (1024*1024):.1f}MB")
            
            # Extension validation
            if file_path.suffix.lower() not in self.config.allowed_extensions:
                return ValidationResult(False, f"File type not allowed: {file_path.suffix}")
            
            # MIME type validation
            mime_type = self._get_mime_type(file_path, file_content)
            if mime_type not in self.config.allowed_mime_types:
                return ValidationResult(False, f"MIME type not allowed: {mime_type}")
            
            # Content validation
            risk_score = 0.0
            if self.config.validate_content and file_content is None:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
            
            if self.config.validate_content and file_content:
                content_validation = self._validate_content(file_content, file_path.suffix)
                if not content_validation[0]:
                    return ValidationResult(False, content_validation[1])
                risk_score += content_validation[2]
            
            # Create result
            result = ValidationResult(
                is_valid=True,
                file_size=file_size,
                file_type=file_path.suffix.lower(),
                mime_type=mime_type,
                checksum=checksum,
                risk_score=risk_score
            )
            
            # Cache result
            self._scanned_files[checksum] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Security validation error for {file_path}: {e}")
            return ValidationResult(False, f"Validation error: {str(e)}")
    
    def validate_uploaded_file(self, uploaded_file, max_total_size: Optional[int] = None) -> ValidationResult:
        """Validate Streamlit uploaded file"""
        try:
            # Get file info
            file_size = uploaded_file.size if hasattr(uploaded_file, 'size') else 0
            filename = uploaded_file.name if hasattr(uploaded_file, 'name') else 'unknown'
            
            # Check total size limit
            if max_total_size:
                current_total = sum(result.file_size for result in self._scanned_files.values())
                if current_total + file_size > max_total_size:
                    return ValidationResult(False, f"Total size limit exceeded: {current_total + file_size}MB")
            
            # Read content for validation
            content = uploaded_file.read()
            uploaded_file.seek(0)  # Reset file pointer
            
            # Create temporary file for validation
            with self._secure_temp_file(suffix=Path(filename).suffix) as temp_path:
                with open(temp_path, 'wb') as f:
                    f.write(content)
                
                # Validate the temporary file
                result = self.validate_file(temp_path, content)
                result.file_size = file_size
                
                return result
                
        except Exception as e:
            logger.error(f"Uploaded file validation error: {e}")
            return ValidationResult(False, f"Upload validation error: {str(e)}")
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _get_mime_type(self, file_path: Path, file_content: Optional[bytes] = None) -> str:
        """Get MIME type of file"""
        try:
            # Try python-magic first (more accurate)
            if file_content:
                mime_type = magic.from_buffer(file_content, mime=True)
            else:
                mime_type = magic.from_file(str(file_path), mime=True)
            
            if mime_type:
                return mime_type
        except:
            pass
        
        # Fallback to mimetypes
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or 'application/octet-stream'
    
    def _validate_content(self, content: bytes, file_extension: str) -> Tuple[bool, str, float]:
        """Validate file content for security threats"""
        try:
            # Convert to string for text-based validation
            try:
                content_str = content.decode('utf-8', errors='ignore')
            except:
                # Binary file, skip content validation
                return True, "", 0.0
            
            risk_score = 0.0
            
            # Check for blocked patterns
            for pattern in self._compiled_patterns:
                matches = pattern.findall(content_str)
                if matches:
                    risk_score += len(matches) * 10
                    logger.warning(f"Blocked pattern found in {file_extension}: {len(matches)} matches")
            
            # Additional checks for HTML files
            if file_extension.lower() in ['.html', '.htm']:
                html_risks = self._validate_html_content(content_str)
                risk_score += html_risks[1]
                if not html_risks[0]:
                    return False, html_risks[2], risk_score
            
            # Check for suspicious content
            suspicious_indicators = [
                'base64_decode',
                'eval(',
                'exec(',
                'system(',
                'shell_exec',
                'passthru',
                '<?php',
                '<%',
                '<script',
                'javascript:',
            ]
            
            content_lower = content_str.lower()
            for indicator in suspicious_indicators:
                if indicator in content_lower:
                    risk_score += 5
            
            # Determine if content is safe
            if risk_score > 50:  # High risk threshold
                return False, f"Content risk score too high: {risk_score}", risk_score
            elif risk_score > 20:  # Medium risk
                logger.warning(f"Medium risk content detected: {risk_score}")
            
            return True, "", risk_score
            
        except Exception as e:
            logger.error(f"Content validation error: {e}")
            return False, f"Content validation error: {str(e)}", 100.0
    
    def _validate_html_content(self, content: str) -> Tuple[bool, float, str]:
        """Specific validation for HTML content"""
        try:
            # Check for dangerous HTML elements
            dangerous_tags = [
                '<script',
                '<iframe',
                '<object',
                '<embed',
                '<form',
                '<input',
                '<link',
                '<meta'
            ]
            
            content_lower = content.lower()
            risk_score = 0.0
            
            for tag in dangerous_tags:
                count = content_lower.count(tag)
                if count > 0:
                    risk_score += count * 5
            
            # Check for dangerous attributes
            dangerous_attrs = [
                'onload=',
                'onerror=',
                'onclick=',
                'onmouseover=',
                'javascript:',
                'vbscript:',
                'data:text/html'
            ]
            
            for attr in dangerous_attrs:
                if attr in content_lower:
                    risk_score += 10
            
            # Check for external resources
            external_patterns = [
                r'http[s]?://[^"\s>]+',
                r'href\s*=\s*["\']?http',
                r'src\s*=\s*["\']?http'
            ]
            
            for pattern in external_patterns:
                if re.search(pattern, content_lower):
                    risk_score += 3
            
            if risk_score > 30:
                return False, risk_score, f"HTML content too risky: {risk_score}"
            
            return True, risk_score, ""
            
        except Exception as e:
            return False, 100.0, f"HTML validation error: {str(e)}"
    
    def _secure_temp_file(self, suffix: str = ''):
        """Context manager for secure temporary file creation"""
        class SecureTempFile:
            def __init__(self, suffix: str):
                self.suffix = suffix
                self.temp_path = None
                
            def __enter__(self):
                # Create secure temporary file
                if self.config.temp_dir:
                    temp_dir = Path(self.config.temp_dir)
                    temp_dir.mkdir(parents=True, exist_ok=True)
                else:
                    temp_dir = Path(tempfile.gettempdir())
                
                # Use cryptographically secure random name
                filename = f"secure_{secrets.token_urlsafe(16)}{self.suffix}"
                self.temp_path = temp_dir / filename
                return str(self.temp_path)
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.temp_path and self.temp_path.exists():
                    try:
                        self.temp_path.unlink()
                    except Exception as e:
                        logger.error(f"Failed to cleanup temp file {self.temp_path}: {e}")
        
        return SecureTempFile(suffix)
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for security"""
        # Remove path traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        # Ensure it's not empty
        if not filename or filename in ['.', '']:
            filename = 'unnamed_file'
        
        return filename
    
    def block_file(self, checksum: str, reason: str):
        """Block a file by checksum"""
        self._blocked_files[checksum] = reason
        logger.warning(f"File blocked: {reason} (checksum: {checksum[:16]}...)")
    
    def unblock_file(self, checksum: str):
        """Unblock a file by checksum"""
        if checksum in self._blocked_files:
            del self._blocked_files[checksum]
            logger.info(f"File unblocked: {checksum[:16]}...")
    
    def get_security_stats(self) -> Dict:
        """Get security statistics"""
        return {
            'blocked_files': len(self._blocked_files),
            'scanned_files': len(self._scanned_files),
            'high_risk_files': len([r for r in self._scanned_files.values() if r.risk_score > 20]),
            'avg_risk_score': sum(r.risk_score for r in self._scanned_files.values()) / len(self._scanned_files) if self._scanned_files else 0
        }

# Global security manager
_global_security_manager: Optional[SecurityManager] = None

def get_security_manager() -> SecurityManager:
    """Get or create global security manager"""
    global _global_security_manager
    if _global_security_manager is None:
        _global_security_manager = SecurityManager()
    return _global_security_manager

def secure_file_upload(uploaded_file, max_size_mb: int = 50) -> ValidationResult:
    """Secure file upload validation"""
    security_manager = get_security_manager()
    return security_manager.validate_uploaded_file(uploaded_file, max_size_mb * 1024 * 1024)

def sanitize_user_input(input_string: str) -> str:
    """Sanitize user input for security"""
    if not input_string:
        return ""
    
    # Remove HTML tags
    sanitized = re.sub(r'<[^>]+>', '', input_string)
    
    # Remove dangerous patterns
    dangerous_patterns = [
        r'javascript:',
        r'vbscript:',
        r'on\w+\s*=',
        r'eval\s*\(',
        r'exec\s*\(',
    ]
    
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    # Limit length
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000]
    
    return sanitized.strip()