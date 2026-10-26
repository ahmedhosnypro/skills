#!/usr/bin/env python3
"""Endpoint-specific wire rules shared by the parse lanes."""

from __future__ import annotations

import urllib.parse

# NVIDIA-direct invoke URLs reject the model multipart part with
# HTTP 400 'unknown multipart part "model"' — omit the part there.
# The config's model value stays required; it is simply not transmitted.
NO_MODEL_PART_HOSTS = ("ai.api.nvidia.com",)


def sends_model_part(endpoint: str) -> bool:
    """False for endpoints whose contract rejects the model part."""
    host = urllib.parse.urlsplit(endpoint).hostname or ""
    return host not in NO_MODEL_PART_HOSTS
