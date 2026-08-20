from dhidb.config import DHIConfig


def test_environment_configuration(monkeypatch):
    monkeypatch.setenv("DHIDB_ARRAY_URI", "s3://example/array")
    monkeypatch.setenv("DHIDB_ENDPOINT_URL", "https://objects.example.org")
    monkeypatch.setenv("DHIDB_REGION", "test-region")

    config = DHIConfig()

    assert config.array_uri == "s3://example/array"
    assert config.endpoint_url == "https://objects.example.org"
    assert config.region == "test-region"

