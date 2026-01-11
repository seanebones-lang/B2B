# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - 2026-01-XX

### Security
- **CRITICAL**: Fixed security vulnerability in `utils/secrets_manager.py` - replaced fixed salt with cryptographically secure random salt generation
- **CRITICAL**: Fixed security vulnerability in `utils/database_encryption.py` - replaced fixed salts with cryptographically secure random salt generation
- Added support for `ENCRYPTION_SALT` environment variable for production secrets manager configuration
- Added support for `DB_ENCRYPTION_SALT` environment variable for production database encryption configuration
- Improved error handling for invalid salt values in encryption utilities

### Fixed
- Fixed duplicate `@abstractmethod` decorator in `scraper/base.py`
- Improved exception handling to preserve exception types throughout call stack
- Changed generic `Exception` raises to preserve original exception types for better debugging
- Updated async scraper exception handling to use `RuntimeError` for fallback cases

### Changed
- Encryption salt generation now uses `secrets.token_bytes(16)` for cryptographically secure random salts
- Encryption utilities now log warnings when using auto-generated salts (encourages production configuration)
- Exception handling preserves exception types instead of converting to generic `Exception`

### Added
- Type hints to `cached()` decorator in `utils/cache.py`
- `TypeVar` import for generic type support in cache utilities
- Comprehensive bug report documentation (`BUG_REPORT.md`)
- Fixes summary documentation (`FIXES_SUMMARY.md`)

### Documentation
- Created comprehensive bug report with all identified issues
- Created fixes summary with migration notes
- Updated documentation to reflect security improvements

---

## Migration Guide

### For Existing Deployments

If you have existing encrypted data:

1. **Backup your data** before making changes
2. **Set environment variables** before upgrading:
   ```bash
   export ENCRYPTION_SALT=$(python -c "import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(16)).decode())")
   export DB_ENCRYPTION_SALT=$(python -c "import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(16)).decode())")
   ```
3. **Plan for data migration** - old data encrypted with fixed salts will need re-encryption
4. **Test thoroughly** in staging environment first

### For New Deployments

1. Set `ENCRYPTION_SALT` and `DB_ENCRYPTION_SALT` during initial setup
2. Store salt values securely (e.g., in secrets management system)
3. Document salt values for disaster recovery purposes

---

## Breaking Changes

⚠️ **Encryption Salt Changes**: 
- Data encrypted with the old fixed salt cannot be decrypted with the new random salt system
- If you have encrypted data, you must migrate it before upgrading
- See Migration Guide above

---

## Security Notes

- All encryption now uses cryptographically secure random salts
- Environment variable support allows for production-grade salt management
- Proper error handling prevents encryption failures from causing data loss
- Warning logs encourage proper production configuration

---

**Note:** This changelog follows semantic versioning. Version numbers will be assigned when releases are tagged.
