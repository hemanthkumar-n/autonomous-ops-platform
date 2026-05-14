import json

from app.tools.kubernetes.incident_context import collect_incident_context
from app.agents.sre.incident_classifier import classify_incident
from app.agents.sre.rca_agent import generate_rca
from app.agents.sre.remediation_agent import generate_remediation_plan
from app.memory.incident_history.store_incident import store_incident


def run_incident_workflow():
    """
    Full autonomous incident response workflow.

    Steps:
    1. Collect incident context
    2. Classify incidents
    3. Generate RCA
    4. Generate remediation plan
    5. Persist incident report
    """

    print("\n=== AUTONOMOUS OPS INCIDENT WORKFLOW STARTED ===\n")

    # Step 1
    print("Step 1: Collecting incident context...\n")

    incident_context = collect_incident_context()

    if not incident_context:
        print("No problematic incidents detected.")
        return None

    # Step 2
    print("Step 2: Classifying incidents...\n")

    classified_incidents = classify_incident(incident_context)

    # Step 3
    print("Step 3: Generating AI RCA...\n")

    rca_output = generate_rca(
        incident_context=incident_context,
        classified_incidents=classified_incidents
    )

    # Step 4
    print("Step 4: Generating remediation plan...\n")

    remediation_output = generate_remediation_plan(
        incident_context=incident_context,
        classified_incidents=classified_incidents,
        rca_output=rca_output
    )

    # Consolidated report
    incident_report = {
        "incident_context": incident_context,
        "classified_incidents": classified_incidents,
        "rca_analysis": rca_output,
        "remediation_plan": remediation_output
    }

    # Step 5
    print("Step 5: Persisting incident report...\n")

    saved_path = store_incident(incident_report)

    print(f"Incident report saved to: {saved_path}\n")

    print("=== INCIDENT WORKFLOW COMPLETED ===\n")

    print(json.dumps(incident_report, indent=2))

    return incident_report


if __name__ == "__main__":
    run_incident_workflow()