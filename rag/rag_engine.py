def generate_rag_analysis(
    risk_score,
    risk_level,
    historical_events,
    current_depth,
    upcoming_interval
):
    """
    Simple RAG-style reasoning engine.
    Uses historical drilling events as evidence
    for the current risk assessment.
    """

    # -----------------------------------------
    # 1. Retrieve relevant historical events
    # -----------------------------------------

    relevant_events = []

    for event in historical_events:

        event_depth = event.get("depth", 0)

        if (
            event_depth >= current_depth - 200
            and event_depth <= current_depth + 200
        ):
            relevant_events.append(event)

    # If no nearby events are found,
    # use all available historical events
    if not relevant_events:
        relevant_events = historical_events

    # -----------------------------------------
    # 2. Generate explanation
    # -----------------------------------------

    if risk_level == "HIGH":

        explanation = (
            f"The current drilling operation has a HIGH risk score "
            f"of {risk_score}/100. Historical offset-well events "
            f"indicate potentially similar drilling conditions "
            f"around the upcoming interval of {upcoming_interval}."
        )

    elif risk_level == "MEDIUM":

        explanation = (
            f"The current drilling operation has a MEDIUM risk score "
            f"of {risk_score}/100. Historical events suggest that "
            f"the upcoming interval should be monitored carefully."
        )

    else:

        explanation = (
            f"The current drilling operation has a LOW risk score "
            f"of {risk_score}/100. No significant historical pattern "
            f"indicates elevated risk in the current interval."
        )

    # -----------------------------------------
    # 3. Generate evidence
    # -----------------------------------------

    evidence = []

    for event in relevant_events:

        evidence.append({
            "event": event.get("event"),
            "well_id": event.get("well_id"),
            "depth": event.get("depth"),
            "severity": event.get("severity")
        })

    # -----------------------------------------
    # 4. Generate recommendation
    # -----------------------------------------

    if risk_level == "HIGH":

        recommendation = (
            "Closely monitor drilling parameters during the upcoming "
            "interval. Pay particular attention to historical event "
            "patterns and be prepared to adjust drilling operations "
            "if similar indicators appear."
        )

    elif risk_level == "MEDIUM":

        recommendation = (
            "Continue drilling with increased monitoring of relevant "
            "drilling parameters and compare live observations with "
            "historical offset-well behaviour."
        )

    else:

        recommendation = (
            "Continue normal drilling operations while maintaining "
            "standard monitoring procedures."
        )

    # -----------------------------------------
    # 5. Final RAG response
    # -----------------------------------------

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "current_depth": current_depth,
        "upcoming_interval": upcoming_interval,

        "explanation": explanation,

        "evidence": evidence,

        "recommendation": recommendation,

        "evidence_count": len(evidence)
    }