from worker_app.comeback_prediction_mapper import (
    sportmonks_predictions_to_comeback_inputs,
)


def test_maps_fulltime_and_first_half_probabilities():
    items = [
        {
            "predictions": {"home": 50, "draw": 30, "away": 20},
            "type": {"developer_name": "FULLTIME_RESULT_PROBABILITY"},
        },
        {
            "predictions": {"home": 40, "draw": 35, "away": 25},
            "type": {"developer_name": "FULLTIME_RESULT_1ST_HALF_PROBABILITY"},
        },
    ]
    result = sportmonks_predictions_to_comeback_inputs(items)

    assert result["home_win_probability"] == 0.5
    assert result["draw_probability"] == 0.3
    assert result["away_win_probability"] == 0.2
    assert result["first_half_home_probability"] == 0.4
    assert result["first_half_draw_probability"] == 0.35
    assert result["first_half_away_probability"] == 0.25


def test_maps_direct_htft_reversal_probabilities_when_present():
    items = [
        {
            "predictions": {"2/1": 8.5, "1/2": 6.25, "X/X": 20},
            "type": {"name": "Half Time Full Time Probability"},
        }
    ]
    result = sportmonks_predictions_to_comeback_inputs(items)

    assert result["direct_2_1_probability"] == 0.085
    assert result["direct_1_2_probability"] == 0.0625
    assert "historical_2_1_rate" not in result
    assert "historical_1_2_rate" not in result


def test_missing_prediction_types_do_not_invent_fields():
    result = sportmonks_predictions_to_comeback_inputs(
        [{"predictions": {"yes": 60, "no": 40}, "type": {"name": "BTTS"}}]
    )
    assert result == {}
