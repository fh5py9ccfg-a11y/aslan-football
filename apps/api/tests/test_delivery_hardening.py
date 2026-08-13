import pytest

from apps.api.app.delivery_hardening import (
    DeliveryHardeningService,
    DeliveryHardeningValidationError,
)


def test_player_csv_quarantines_invalid_rows():
    service = DeliveryHardeningService()
    csv_text = (
        "player_id,name,position,age,market_value\n"
        "p1,Ali,ST,23,5\n"
        "p2,Veli,XYZ,14,-1\n"
    )

    report = service.validate_csv(
        report_id="r1",
        import_type="PLAYERS",
        csv_text=csv_text,
        now=100,
    )

    assert report.total_rows == 2
    assert report.valid_rows == 1
    assert report.invalid_rows == 1
    assert len(report.issues) >= 3
    assert len(report.checksum) == 64


def test_match_csv_validates_headers():
    service = DeliveryHardeningService()

    with pytest.raises(DeliveryHardeningValidationError):
        service.validate_csv(
            report_id="r1",
            import_type="MATCHES",
            csv_text="match_id,opponent\nm1,Rakip\n",
            now=100,
        )
