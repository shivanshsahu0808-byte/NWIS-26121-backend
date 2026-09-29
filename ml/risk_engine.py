from .test_data import load_historical_events


def calculate_risk(current_depth, upcoming_depth):
    """
    Calculate drilling risk based on historical events
    falling inside the upcoming drilling interval.
    """

    events = load_historical_events()

    matched_events = []

    for event in events:

        event_name = event[0]
        event_depth = event[1]
        well_id = event[2]
        severity = event[3]

        # Check whether historical event falls
        # inside the upcoming drilling interval
        if current_depth <= event_depth <= upcoming_depth:

            matched_events.append({
                "event": event_name,
                "depth": event_depth,
                "well_id": well_id,
                "severity": severity
            })

    # -------------------------------------------------
    # Calculate risk score
    # -------------------------------------------------

    risk_score = 0

    for event in matched_events:

        if event["severity"] == "HIGH":
            risk_score += 70

        elif event["severity"] == "MEDIUM":
            risk_score += 40

        elif event["severity"] == "LOW":
            risk_score += 20

    # Keep score between 0 and 100
    risk_score = min(risk_score, 100)

    # -------------------------------------------------
    # Risk level
    # -------------------------------------------------

    if risk_score >= 70:
        risk_level = "HIGH"

    elif risk_score >= 40:
        risk_level = "MEDIUM"

    elif risk_score > 0:
        risk_level = "LOW"

    else:
        risk_level = "SAFE"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "matched_events": matched_events
    }


# -----------------------------------------------------
# Test
# -----------------------------------------------------

if __name__ == "__main__":

    current_depth = 2820
    upcoming_depth = 2920

    result = calculate_risk(
        current_depth,
        upcoming_depth
    )

    print("\n===================================")
    print("        NWIS RISK ENGINE")
    print("===================================\n")

    print("Current Depth:", current_depth, "m")
    print("Upcoming Depth:", upcoming_depth, "m")

    print("\nRisk Score:", result["risk_score"])
    print("Risk Level:", result["risk_level"])

    print("\nMatched Historical Events:")

    for event in result["matched_events"]:

        print(
            f"- {event['event']} | "
            f"{event['depth']} m | "
            f"{event['well_id']} | "
            f"{event['severity']}"
        )

    print("\n===================================")