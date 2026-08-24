"""Configuration for the public DHIDB TileDB array."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

DEFAULT_ARRAY_URI = "s3://dhidb/gpp_global_300m_2014_2025_v1_cv"
DEFAULT_ENDPOINT_URL = "https://vip.s3.ufz.de"
DEFAULT_YEARS = tuple(range(2014, 2026))


@dataclass(frozen=True)
class DHIConfig:
    """Connection settings for a read-only DHIDB array.

    Parameters may be provided directly or through the corresponding
    ``DHIDB_*`` environment variables. Credentials are intentionally absent:
    the published database is expected to permit anonymous reads.
    """

    array_uri: str = field(
        default_factory=lambda: os.getenv("DHIDB_ARRAY_URI", DEFAULT_ARRAY_URI)
    )
    endpoint_url: str | None = field(
        default_factory=lambda: os.getenv("DHIDB_ENDPOINT_URL", DEFAULT_ENDPOINT_URL)
    )
    region: str = field(default_factory=lambda: os.getenv("DHIDB_REGION", "us-east-1"))
    use_virtual_addressing: bool = False
    anonymous: bool = True
    max_cells: int = 50_000_000
    tiledb_config: Mapping[str, str] = field(default_factory=dict)
