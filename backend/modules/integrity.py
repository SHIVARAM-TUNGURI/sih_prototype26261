"""
SHA-256 Integrity Verification Module.

Provides cryptographic hashing to ensure document integrity. Files are
hashed on upload and can be re-verified at any time to detect alterations.
"""
import hashlib
import logging
import os

logger = logging.getLogger(__name__)

# Default buffer size for reading files in chunks (8 KB)
_BUFFER_SIZE = 8192


def compute_hash(file_path: str) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Absolute or relative path to the file.

    Returns:
        Hexadecimal SHA-256 hash string (64 characters).

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    try:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(_BUFFER_SIZE)
                if not chunk:
                    break
                sha256.update(chunk)

        file_hash = sha256.hexdigest()
        logger.debug("Computed SHA-256 for '%s': %s", file_path, file_hash)
        return file_hash

    except FileNotFoundError:
        logger.error("Cannot compute hash — file not found: %s", file_path)
        raise
    except Exception as e:
        logger.error("Error computing hash for '%s': %s", file_path, e)
        raise


def verify_hash(file_path: str, stored_hash: str) -> dict:
    """
    Verify a file's integrity by comparing its current hash to a stored hash.

    Args:
        file_path: Path to the file to verify.
        stored_hash: The previously stored SHA-256 hash string.

    Returns:
        Dictionary with keys:
            - original_hash (str): The stored hash that was provided.
            - current_hash (str): The freshly computed hash.
            - status (str): "verified" if hashes match, "altered" if they differ.
    """
    try:
        current_hash = compute_hash(file_path)
        status = "verified" if current_hash == stored_hash else "altered"

        if status == "altered":
            logger.warning(
                "Hash mismatch for '%s': stored=%s, current=%s",
                file_path,
                stored_hash,
                current_hash,
            )
        else:
            logger.info("Hash verified for '%s'", file_path)

        return {
            "original_hash": stored_hash,
            "current_hash": current_hash,
            "status": status,
        }

    except FileNotFoundError:
        logger.error("Cannot verify hash — file not found: %s", file_path)
        return {
            "original_hash": stored_hash,
            "current_hash": "FILE_NOT_FOUND",
            "status": "altered",
        }
    except Exception as e:
        logger.error("Error verifying hash for '%s': %s", file_path, e)
        return {
            "original_hash": stored_hash,
            "current_hash": f"ERROR: {str(e)}",
            "status": "altered",
        }
