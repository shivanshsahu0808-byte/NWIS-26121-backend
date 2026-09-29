from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import get_connection
from ml.risk_engine import calculate_risk
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


app = FastAPI(
    title="NWIS API",
    description="Nearby Wells Intelligence System",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# BASIC ROUTES
# =========================================================

@app.get("/")
def root():
    return {
        "message": "NWIS API is running",
        "status": "success"
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "service": "NWIS Backend"
    }
    
    # =========================================================
# AUTHENTICATION
# =========================================================

class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/login")
def login(request: LoginRequest):

    VALID_USERNAME = "admin"
    VALID_PASSWORD = "nwis123"

    if (
        request.username == VALID_USERNAME
        and request.password == VALID_PASSWORD
    ):
        return {
            "success": True,
            "message": "Login successful",
            "user": {
                "username": "admin",
                "role": "Drilling Engineer"
            }
        }

    return {
        "success": False,
        "message": "Invalid username or password"
    }


# =========================================================
# GET ALL WELLS
# PostgreSQL → FastAPI → React
# =========================================================

@app.get("/api/wells")
def get_wells():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            name,
            latitude,
            longitude,
            depth,
            formation,
            status
        FROM wells
        ORDER BY id;
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    wells_data = []

    for row in rows:

        wells_data.append({
            "id": row[0],
            "name": row[1],
            "latitude": float(row[2]),
            "longitude": float(row[3]),
            "depth": row[4],
            "formation": row[5],
            "status": row[6]
        })

    return {
        "count": len(wells_data),
        "wells": wells_data
    }


# =========================================================
# GET SINGLE WELL
# PostgreSQL → FastAPI
# =========================================================

@app.get("/api/wells/{well_id}")
def get_well(well_id: str):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            name,
            latitude,
            longitude,
            depth,
            formation,
            status
        FROM wells
        WHERE id = %s;
    """, (well_id,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if row is None:

        return {
            "error": "Well not found"
        }

    return {
        "id": row[0],
        "name": row[1],
        "latitude": float(row[2]),
        "longitude": float(row[3]),
        "depth": row[4],
        "formation": row[5],
        "status": row[6]
    }


# =========================================================
# WELL INTELLIGENCE
# PostgreSQL wells + historical_events
# =========================================================

@app.get("/api/wells/{well_id}/intelligence")
def get_well_intelligence(well_id: str):

    conn = get_connection()
    cur = conn.cursor()


    # -----------------------------------------------------
    # 1. Get current well from PostgreSQL
    # -----------------------------------------------------

    cur.execute("""
        SELECT
            id,
            name,
            depth,
            formation
        FROM wells
        WHERE id = %s;
    """, (well_id,))

    well = cur.fetchone()


    # Well not found
    if well is None:

        cur.close()
        conn.close()

        return {
            "error": "Well not found"
        }


    current_well_id = well[0]
    current_well_name = well[1]
    current_depth = well[2]
    formation = well[3]


    # -----------------------------------------------------
    # 2. Calculate upcoming drilling interval
    # -----------------------------------------------------

    upcoming_depth = current_depth + 100


    # -----------------------------------------------------
    # 3. Get historical events from PostgreSQL
    # -----------------------------------------------------

    cur.execute("""
        SELECT
            event,
            depth,
            well_id,
            severity
        FROM historical_events
        WHERE depth >= %s
        AND depth <= %s
        ORDER BY depth;
    """, (
        current_depth,
        upcoming_depth
    ))

    rows = cur.fetchall()


    cur.close()
    conn.close()


    # -----------------------------------------------------
    # 4. Convert database rows into API response
    # -----------------------------------------------------

    relevant_events = []

    for row in rows:

        relevant_events.append({
            "event": row[0],
            "depth": row[1],
            "well_id": row[2],
            "severity": row[3]
        })


    # -----------------------------------------------------
    # 5. Generate recommendation
    # -----------------------------------------------------

    if relevant_events:

        historical_match = True

        recommendation = (
            "Historical events detected in the upcoming "
            "drilling interval. Monitor relevant risks."
        )

    else:

        historical_match = False

        recommendation = (
            "No major historical event found in "
            "the upcoming drilling interval."
        )


    # -----------------------------------------------------
    # 6. Final intelligence response
    # -----------------------------------------------------

    return {

        "well_id": current_well_id,

        "well_name": current_well_name,

        "formation": formation,

        "current_depth": current_depth,

        "upcoming_interval":
            f"{current_depth} - {upcoming_depth} m",

        "historical_match":
            historical_match,

        "nearby_events":
            relevant_events,

        "recommendation":
            recommendation
    }
    
    # =========================================================
# ML RISK SCORE
# =========================================================

@app.get("/api/wells/{well_id}/risk")
def get_well_risk(well_id: str):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            depth
        FROM wells
        WHERE id = %s;
    """, (well_id,))

    well = cur.fetchone()

    cur.close()
    conn.close()

    if well is None:
        return {
            "error": "Well not found"
        }

    current_depth = well[1]

    upcoming_depth = current_depth + 100

    risk = calculate_risk(
        current_depth,
        upcoming_depth
    )

    return {
        "well_id": well_id,
        "current_depth": current_depth,
        "upcoming_interval":
            f"{current_depth} - {upcoming_depth} m",
        "risk_score": risk["risk_score"],
        "risk_level": risk["risk_level"],
        "matched_events": risk["matched_events"]
    }
    
    # =========================================================
# AI DRILLING INSIGHT
# RAG-STYLE GROUNDED ANALYSIS
# PostgreSQL historical data + ML risk + LLM
# =========================================================

class AIInsightRequest(BaseModel):
    well_id: str

@app.post("/api/ai/insight")
def generate_ai_insight(request: AIInsightRequest):

    conn = get_connection()
    cur = conn.cursor()

    # =====================================================
    # 1. GET CURRENT WELL
    # =====================================================

    cur.execute("""
        SELECT
            id,
            name,
            depth,
            formation,
            status
        FROM wells
        WHERE id = %s;
    """, (request.well_id,))

    well = cur.fetchone()

    if well is None:

        cur.close()
        conn.close()

        return {
            "success": False,
            "message": "Well not found"
        }

    well_id = well[0]
    well_name = well[1]
    current_depth = well[2]
    formation = well[3]
    status = well[4]

    upcoming_depth = current_depth + 100


    # =====================================================
    # 2. GET HISTORICAL EVENTS
    # =====================================================

    cur.execute("""
        SELECT
            event,
            depth,
            well_id,
            severity
        FROM historical_events
        WHERE depth >= %s
        AND depth <= %s
        ORDER BY depth;
    """, (
        current_depth,
        upcoming_depth
    ))

    rows = cur.fetchall()

    cur.close()
    conn.close()


    historical_events = []

    for row in rows:

        historical_events.append({
            "event": row[0],
            "depth": row[1],
            "well_id": row[2],
            "severity": row[3]
        })


    # =====================================================
    # 3. GET ML RISK
    # =====================================================

    risk = calculate_risk(
        current_depth,
        upcoming_depth
    )

    risk_score = risk["risk_score"]
    risk_level = risk["risk_level"]


    # =====================================================
    # 4. BUILD GROUNDED CONTEXT
    # =====================================================

    context = f"""
NWIS DRILLING DATA

Current Well:
- Well ID: {well_id}
- Well Name: {well_name}
- Formation: {formation}
- Current Depth: {current_depth} m
- Upcoming Interval: {current_depth} - {upcoming_depth} m
- Status: {status}

ML RISK ASSESSMENT:
- Risk Score: {risk_score}
- Risk Level: {risk_level}

HISTORICAL EVENTS:
"""

    if historical_events:

        for event in historical_events:

            context += f"""
- Event: {event["event"]}
- Offset Well: {event["well_id"]}
- Depth: {event["depth"]} m
- Severity: {event["severity"]}
"""

    else:

        context += """
- No historical events found in this drilling interval.
"""


    # =====================================================
    # 5. TRY AI INSIGHT
    # =====================================================

    prompt = f"""
You are an AI assistant inside NWIS
(Nearby Wells Intelligence System).

Provide a concise drilling-risk insight.

Use ONLY the provided database and ML information.

Do not invent geological facts or historical events.

Provide:

1. Risk Summary
2. Historical Evidence
3. Recommended Monitoring
4. One-line Operational Insight

DATA:

{context}
"""

    try:

        response = client.responses.create(
            model="gpt-5.6-luna",
            input=prompt
        )

        ai_text = response.output_text

        return {
            "success": True,
            "source": "AI",
            "well_id": well_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "historical_events": historical_events,
            "insight": ai_text
        }


    # =====================================================
    # 6. SAFE FALLBACK
    # =====================================================

    except Exception:

        # -----------------------------------------------
        # Determine monitoring recommendation
        # -----------------------------------------------

        if risk_level == "HIGH":

            monitoring = (
                "Increase monitoring of drilling parameters "
                "and review historical high-severity events "
                "before entering the upcoming interval."
            )

        elif risk_level == "MEDIUM":

            monitoring = (
                "Maintain increased monitoring of drilling "
                "parameters and compare observations with "
                "historical offset-well events."
            )

        else:

            monitoring = (
                "Continue routine monitoring of drilling "
                "parameters while tracking the upcoming interval."
            )


        # -----------------------------------------------
        # Historical evidence
        # -----------------------------------------------

        if historical_events:

            evidence_lines = []

            for event in historical_events:

                evidence_lines.append(
                    f'{event["event"]} was recorded in '
                    f'offset well {event["well_id"]} at '
                    f'{event["depth"]} m '
                    f'({event["severity"]} severity).'
                )

            historical_evidence = " ".join(evidence_lines)

        else:

            historical_evidence = (
                "No historical events were found in "
                "the current upcoming drilling interval."
            )


        # -----------------------------------------------
        # Operational insight
        # -----------------------------------------------

        if historical_events:

            operational_insight = (
                f"Historical evidence is present in the "
                f"{current_depth}-{upcoming_depth} m interval; "
                f"monitor relevant drilling parameters closely."
            )

        else:

            operational_insight = (
                f"No matching historical events were found "
                f"for the {current_depth}-{upcoming_depth} m interval."
            )


        fallback_text = f"""
RISK SUMMARY

The ML risk assessment for {well_name} indicates a
{risk_level} risk level with a risk score of {risk_score}.

HISTORICAL EVIDENCE

{historical_evidence}

RECOMMENDED MONITORING

{monitoring}

OPERATIONAL INSIGHT

{operational_insight}
"""


        return {
            "success": True,
            "source": "NWIS_FALLBACK",
            "well_id": well_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "historical_events": historical_events,
            "insight": fallback_text.strip()
        }