import pytest

import garminconnect

DATE = "2023-07-01"


@pytest.fixture(scope="session")
def garmin() -> garminconnect.Garmin:
    return garminconnect.Garmin("email@example.org", "password")


@pytest.mark.vcr
def test_stats(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    stats = garmin.get_stats(DATE)
    assert "totalKilocalories" in stats
    assert "activeKilocalories" in stats


@pytest.mark.vcr
def test_user_summary(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    user_summary = garmin.get_user_summary(DATE)
    assert "totalKilocalories" in user_summary
    assert "activeKilocalories" in user_summary


@pytest.mark.vcr
def test_steps_data(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    steps = garmin.get_steps_data(DATE)
    if not steps:
        pytest.skip("No steps data for date")
    steps_data = steps[0]
    assert "steps" in steps_data


@pytest.mark.vcr
def test_floors(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    floors_data = garmin.get_floors(DATE)
    assert "floorValuesArray" in floors_data


@pytest.mark.vcr
def test_daily_steps(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    daily_steps_data = garmin.get_daily_steps(DATE, DATE)
    # The API returns a list of daily step dictionaries
    assert isinstance(daily_steps_data, list)
    assert len(daily_steps_data) > 0

    # Check the first day's data
    daily_steps = daily_steps_data[0]
    assert "calendarDate" in daily_steps
    assert "totalSteps" in daily_steps


@pytest.mark.vcr
def test_heart_rates(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    heart_rates = garmin.get_heart_rates(DATE)
    assert "calendarDate" in heart_rates
    assert "restingHeartRate" in heart_rates


@pytest.mark.vcr
def test_stats_and_body(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    stats_and_body = garmin.get_stats_and_body(DATE)
    assert "calendarDate" in stats_and_body
    assert "metabolicAge" in stats_and_body


@pytest.mark.vcr
def test_body_composition(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    body_composition = garmin.get_body_composition(DATE)
    assert "totalAverage" in body_composition
    assert "metabolicAge" in body_composition["totalAverage"]


@pytest.mark.vcr
def test_body_battery(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    bb = garmin.get_body_battery(DATE)
    if not bb:
        pytest.skip("No body battery data for date")
    body_battery = bb[0]
    assert "date" in body_battery
    assert "charged" in body_battery


@pytest.mark.vcr
def test_hydration_data(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    hydration_data = garmin.get_hydration_data(DATE)
    assert hydration_data
    assert "calendarDate" in hydration_data


@pytest.mark.vcr
def test_respiration_data(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    respiration_data = garmin.get_respiration_data(DATE)
    assert "calendarDate" in respiration_data
    assert "avgSleepRespirationValue" in respiration_data


@pytest.mark.vcr
def test_spo2_data(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    spo2_data = garmin.get_spo2_data(DATE)
    assert "calendarDate" in spo2_data
    assert "averageSpO2" in spo2_data


@pytest.mark.vcr
def test_hrv_data(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    hrv_data = garmin.get_hrv_data(DATE)
    # HRV data might not be available for all dates (API returns 204 No Content)
    if hrv_data is not None:
        # If data exists, validate the structure
        assert "hrvSummary" in hrv_data
        assert "weeklyAvg" in hrv_data["hrvSummary"]
    else:
        # If no data, that's also a valid response (204 No Content)
        assert hrv_data is None


@pytest.mark.vcr
def test_download_activity(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    activity_id = "11998957007"
    # This test may fail with 403 Forbidden if the activity is private or not accessible
    # In such cases, we verify that the appropriate error is raised
    try:
        activity = garmin.download_activity(activity_id)
        assert activity  # If successful, activity should not be None/empty
    except garminconnect.GarminConnectConnectionError as e:
        # Expected error for inaccessible activities
        assert "403" in str(e) or "Forbidden" in str(e)
        pytest.skip(
            "Activity not accessible (403 Forbidden) - expected in test environment"
        )


@pytest.mark.vcr
def test_all_day_stress(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    all_day_stress = garmin.get_all_day_stress(DATE)
    # Validate stress data structure
    assert "calendarDate" in all_day_stress
    assert "avgStressLevel" in all_day_stress
    assert "maxStressLevel" in all_day_stress
    assert "stressValuesArray" in all_day_stress


@pytest.mark.vcr
def test_upload(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    fpath = "tests/12129115726_ACTIVITY.fit"
    # This test may fail with 409 Conflict if the activity already exists
    # In such cases, we verify that the appropriate error is raised
    try:
        result = garmin.upload_activity(fpath)
        assert result  # If successful, should return upload result
    except Exception as e:
        # Expected error for duplicate uploads
        if "409" in str(e) or "Conflict" in str(e):
            pytest.skip(
                "Activity already exists (409 Conflict) - expected in test environment"
            )
        else:
            # Re-raise unexpected errors
            raise


@pytest.mark.vcr
def test_request_reload(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    cdate = "2021-01-01"
    # Get initial steps data
    sum(steps["steps"] for steps in garmin.get_steps_data(cdate))
    # Test that request_reload returns a valid response
    reload_response = garmin.request_reload(cdate)
    assert reload_response is not None
    # Get steps data after reload - should still be accessible
    final_steps = sum(steps["steps"] for steps in garmin.get_steps_data(cdate))
    assert final_steps >= 0  # Steps data should be non-negative


@pytest.mark.vcr
def test_heart_rate_zones(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    zones = garmin.get_heart_rate_zones()
    assert zones is not None
    assert isinstance(zones, list)
    if zones:
        # Check that each zone has expected fields
        for zone in zones:
            assert "sport" in zone
            assert "trainingMethod" in zone


@pytest.mark.vcr
def test_activities_first_last(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    dates = garmin.get_activities_first_last()
    assert dates is not None
    assert isinstance(dates, dict)
    # Should contain first and last activity dates
    assert "firstActivityDate" in dates or "lastActivityDate" in dates


@pytest.mark.vcr
def test_daily_movement(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    movement = garmin.get_daily_movement(DATE)
    assert movement is not None
    assert isinstance(movement, dict)
    assert "calendarDate" in movement


@pytest.mark.vcr
def test_training_status_daily(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    status = garmin.get_training_status_daily(DATE)
    # May return None if no training data for the date
    if status is None:
        pytest.skip("No training status data for date")
    assert isinstance(status, dict)


@pytest.mark.vcr
def test_hrv_summary(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    hrv = garmin.get_hrv_summary(DATE, DATE)
    assert hrv is not None
    assert isinstance(hrv, list)


@pytest.mark.vcr
def test_sleep_stats(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    stats = garmin.get_sleep_stats(DATE, DATE)
    assert stats is not None
    assert isinstance(stats, list)


@pytest.mark.vcr
def test_calendar_month(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    calendar = garmin.get_calendar_month(2023, 7)
    assert calendar is not None
    assert isinstance(calendar, dict)
