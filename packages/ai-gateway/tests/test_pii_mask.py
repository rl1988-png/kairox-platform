from ai_gateway.utils.pii_mask import mask_pii


def test_mask_email() -> None:
    text = "Contact user@example.com for help"
    assert "[REDACTED]" in mask_pii(text)
    assert "user@example.com" not in mask_pii(text)


def test_mask_phone() -> None:
    text = "Call +49 170 1234567 today"
    masked = mask_pii(text)
    assert "[REDACTED]" in masked
    assert "1234567" not in masked


def test_mask_tron_address() -> None:
    addr = "T" + "A" * 33
    text = f"Send to {addr} please"
    masked = mask_pii(text)
    assert addr not in masked
    assert "[REDACTED]" in masked


def test_mask_nested_dict() -> None:
    payload = {
        "email": "a@test.com",
        "wallet": "T" + "B" * 33,
        "nested": {"phone": "+1 555 123 4567"},
    }
    masked = mask_pii(payload)
    assert masked["email"] == "[REDACTED]"
    assert masked["wallet"] == "[REDACTED]"
    assert masked["nested"]["phone"] == "[REDACTED]"


def test_mask_list() -> None:
    masked = mask_pii(["user@x.com", "plain"])
    assert masked[0] == "[REDACTED]"
    assert masked[1] == "plain"
