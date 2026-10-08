"""A damaged artifact must fail before joblib deserialization."""

import json
from unittest.mock import Mock

import pytest

from agrointel import inference


def test_integrity_failure_prevents_unpickle(tmp_path, monkeypatch):
    directory = tmp_path / "artifacts"
    directory.mkdir()
    (directory / "metadata.json").write_text(
        json.dumps({"artifact_sha256": {"crop_classifier.joblib": "wrong"}})
    )
    (directory / "crop_classifier.joblib").write_bytes(b"not a trusted model")
    monkeypatch.setattr(inference, "ROOT", tmp_path)
    loader = Mock()
    monkeypatch.setattr(inference.joblib, "load", loader)
    inference.artifacts.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="integrity"):
            inference.artifacts()
        loader.assert_not_called()
    finally:
        inference.artifacts.cache_clear()
