"""MQTT topic constants — single source of truth per spec A.4.2 & B.5.1."""

# ── Full-stack (Part A) topics ────────────────────────────────────────────────
INFERENCE_RESULTS = 'visionpulse/inference/results'
SYSTEM_ERRORS = 'visionpulse/system/errors'
SYSTEM_MONITOR = 'visionpulse/system/monitor'
SYSTEM_STATUS = 'visionpulse/system/status'


# ── AI pipeline (Part B) topics — parameterised by line + station ────────────
def ic_inspection_result(line_id: str, station_id: str) -> str:
    return f'ic_inspection/{line_id}/{station_id}/result'


def ic_inspection_defect_area(line_id: str, station_id: str) -> str:
    return f'ic_inspection/{line_id}/{station_id}/defect_area'


def ic_inspection_status(line_id: str, station_id: str) -> str:
    return f'ic_inspection/{line_id}/{station_id}/status'


def ic_inspection_alert(line_id: str, station_id: str) -> str:
    return f'ic_inspection/{line_id}/{station_id}/alert'


def ic_inspection_command(station_id: str) -> str:
    return f'ic_inspection/command/{station_id}'
