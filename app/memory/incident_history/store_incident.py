import json
import os
from datetime import datetime


INCIDENT_HISTORY_DIR = "app/memory/incident_history/incidents"


def ensure_incident_directory():
    """
    Ensure incident storage directory exists.
    """

    os.makedirs(INCIDENT_HISTORY_DIR, exist_ok=True)


def generate_incident_filename():
    """
    Generate timestamp-based incident filename.
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"incident_{timestamp}.json"


def store_incident(incident_report):
    """
    Persist incident report to disk.
    """

    ensure_incident_directory()

    filename = generate_incident_filename()

    filepath = os.path.join(INCIDENT_HISTORY_DIR, filename)

    with open(filepath, "w") as file:
        json.dump(incident_report, file, indent=2)

    return filepath


if __name__ == "__main__":

    sample_incident = {
        "test": "incident"
    }

    saved_path = store_incident(sample_incident)

    print(f"Incident saved to: {saved_path}")