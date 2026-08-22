from app.comeback_detector import ComebackDetector, ComebackInputs


def test_detects_home_2_1_profile():
    detector = ComebackDetector(alert_threshold=70)
    signal = detector.evaluate(
        ComebackInputs(
            home_win_probability=0.64,
            draw_probability=0.21,
            away_win_probability=0.15,
            first_half_home_probability=0.34,
            first_half_draw_probability=0.40,
            first_half_away_probability=0.26,
            home_comeback_rate_when_behind=0.60,
            away_comeback_rate_when_behind=0.14,
            home_loss_rate_when_ahead=0.08,
            away_loss_rate_when_ahead=0.46,
            home_second_half_goal_share=0.70,
            away_second_half_goal_share=0.46,
            historical_2_1_rate=0.14,
            historical_1_2_rate=0.02,
            similar_matches=48,
            similar_2_1_rate=0.17,
            similar_1_2_rate=0.02,
            home_ft_shortening=0.09,
        )
    )

    assert signal.score_2_1 >= 70
    assert signal.score_2_1 > signal.score_1_2
    assert signal.preferred_market == "2/1"
    assert signal.label in {"WATCH", "STRONG", "VERY_STRONG"}


def test_detects_away_1_2_profile():
    detector = ComebackDetector(alert_threshold=70)
    signal = detector.evaluate(
        ComebackInputs(
            home_win_probability=0.18,
            draw_probability=0.22,
            away_win_probability=0.60,
            first_half_home_probability=0.27,
            first_half_draw_probability=0.40,
            first_half_away_probability=0.33,
            home_comeback_rate_when_behind=0.11,
            away_comeback_rate_when_behind=0.55,
            home_loss_rate_when_ahead=0.44,
            away_loss_rate_when_ahead=0.09,
            home_second_half_goal_share=0.45,
            away_second_half_goal_share=0.69,
            historical_2_1_rate=0.02,
            historical_1_2_rate=0.13,
            similar_matches=37,
            similar_2_1_rate=0.02,
            similar_1_2_rate=0.16,
            away_ft_shortening=0.07,
        )
    )

    assert signal.score_1_2 > signal.score_2_1
    assert signal.preferred_market == "1/2"
    assert signal.label in {"WATCH", "STRONG", "VERY_STRONG"}


def test_small_neighbour_sample_does_not_overpower_model():
    detector = ComebackDetector(alert_threshold=75, min_similar_matches=20)
    signal = detector.evaluate(
        ComebackInputs(
            home_win_probability=0.40,
            draw_probability=0.30,
            away_win_probability=0.30,
            first_half_home_probability=0.36,
            first_half_draw_probability=0.37,
            first_half_away_probability=0.27,
            similar_matches=3,
            similar_2_1_rate=1.0,
            similar_1_2_rate=0.0,
        )
    )

    assert signal.preferred_market is None
    assert any("sample is small" in warning for warning in signal.warnings)
