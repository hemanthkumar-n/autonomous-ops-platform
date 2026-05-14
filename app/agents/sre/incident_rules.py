INCIDENT_RULES = {
    "OOMKilled": {
        "incident_type": "MemoryExhaustion",
        "severity": "Critical",
        "confidence": 99,
        "recommended_team": "Application / Platform Engineering",
    },
    "CrashLoopBackOff": {
        "incident_type": "ApplicationCrashLoop",
        "severity": "High",
        "confidence": 95,
        "recommended_team": "Application Team",
    },
    "ImagePullBackOff": {
        "incident_type": "ImagePullFailure",
        "severity": "High",
        "confidence": 98,
        "recommended_team": "Platform Engineering",
    },
    "ErrImagePull": {
        "incident_type": "ImagePullFailure",
        "severity": "High",
        "confidence": 96,
        "recommended_team": "Platform Engineering",
    },
    "CreateContainerConfigError": {
        "incident_type": "ContainerConfigurationFailure",
        "severity": "High",
        "confidence": 95,
        "recommended_team": "Platform Engineering",
    },
    "CreateContainerError": {
        "incident_type": "ContainerStartupFailure",
        "severity": "High",
        "confidence": 94,
        "recommended_team": "Platform Engineering",
    },
    "FailedScheduling": {
        "incident_type": "SchedulingFailure",
        "severity": "Critical",
        "confidence": 93,
        "recommended_team": "Cluster Operations",
    },
}