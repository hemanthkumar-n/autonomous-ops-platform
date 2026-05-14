import json

from app.tools.kubernetes.incident_context import collect_incident_context
from app.agents.sre.incident_classifier import classify_incident
from app.agents.sre.rca_agent import generate_rca
from app.agents.sre.remediation_agent import generate_all_remediations
from app.memory.incident_history.store_incident import store_incident


def map_incident_context(incident_context):
    """
    Map pod_name -> full incident context.
    """

    context_map = {}

    for incident in incident_context:
        context_map[incident["pod_name"]] = incident

    return context_map


def generate_incident_rcas(classified_incidents, incident_context):
    """
    Generate RCA per incident.
    """

    context_map = map_incident_context(incident_context)

    rca_results = []

    for incident in classified_incidents:
        pod_name = incident["pod_name"]

        relevant_context = context_map.get(pod_name, {})

        print(f"Generating RCA for: {pod_name}")

        rca_output = generate_rca(
            incident_context=relevant_context,
            classified_incidents=[incident]
        )

        rca_results.append({
            "pod_name": pod_name,
            "incident_type": incident["incident_type"],
            "rca": rca_output
        })

    return rca_results


def main():
    """
    Autonomous incident workflow.
    """

    print("\n=== AUTONOMOUS OPS INCIDENT WORKFLOW STARTED ===\n")

    print("Step 1: Collecting unified incident context...\n")

    incident_context = collect_incident_context()

    if not incident_context:
        print("No active incidents detected.")
        return

    print("Step 2: Classifying incidents...\n")

    classified_incidents = classify_incident(incident_context)

    print("Step 3: Generating incident-by-incident RCA...\n")

    rca_results = generate_incident_rcas(
        classified_incidents=classified_incidents,
        incident_context=incident_context
    )

    print("Step 4: Generating incident-by-incident remediation...\n")

    remediation_results = generate_all_remediations(
        classified_incidents=classified_incidents,
        incident_context=incident_context
    )

    workflow_output = {
        "incident_context": incident_context,
        "classified_incidents": classified_incidents,
        "rca_results": rca_results,
        "remediation_results": remediation_results
    }

    print("Step 5: Persisting workflow results...\n")

    saved_path = store_incident(workflow_output)

    print(f"Workflow saved to: {saved_path}\n")

    print("\n=== INCIDENT WORKFLOW COMPLETED ===\n")

    print(json.dumps(workflow_output, indent=2))


if __name__ == "__main__":
    main()