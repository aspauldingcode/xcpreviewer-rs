"""Bounded reader for sanitized Xcode display-state diagnostics, not wire evidence."""
import hashlib
import re


def parse_display_state(text: str) -> dict:
    """Fail closed on unsupported report shapes; never infer rendered from Available."""
    if len(text.encode("utf-8")) > 65536:
        raise ValueError("display-state report exceeds 64 KiB")
    if text.count("providers [") != 1 or text.count("registries [") != 1:
        raise ValueError("expected one providers and registries section")
    depth = []
    for char in text:
        if char in "[{":
            depth.append(char)
            if len(depth) > 16:
                raise ValueError("excessive nesting")
        elif char in "]}":
            if not depth or depth.pop() != {"}": "{", "]": "["}[char]:
                raise ValueError("unbalanced report")
    if depth:
        raise ValueError("unbalanced report")

    def field(name, pattern, body=text):
        matches = re.findall(r"^\s*" + re.escape(name) + r": (" + pattern + r")\s*$", body, re.M)
        if len(matches) != 1:
            raise ValueError("missing or ambiguous " + name)
        return matches[0]

    update = int(field("updateIdentifier", r"[0-9]+"))
    building = field("buildingState", r"[A-Za-z]+")
    updating = field("isUpdateInProgress", r"true|false") == "true"
    registry_section = text.split("registries [", 1)[1]
    blocks = re.findall(r"Registry-([^\n]+) \{(.*?)(?=\n\s*Registry-|\Z)", registry_section, re.S)
    if not blocks or len(blocks) > 32:
        raise ValueError("unsupported registry count")
    registries = []
    ids = set()
    for identifier, body in blocks:
        if identifier in ids:
            raise ValueError("duplicate registry")
        ids.add(identifier)
        status = field("status", r"[^\n]+?", body)
        stale = field("isStale", r"true|false", body) == "true"
        live = field("livePreview", r"[A-Za-z]+", body)
        static = field("staticPreview", r"[A-Za-z]+", body)
        registries.append({"id": identifier, "status": status, "is_stale": stale,
                           "live_preview": live, "static_preview": static,
                           "reports_fresh_live_success": not stale and live == "succeeded"})
    return {"schema_version": 1, "authority": "xcode-ui-diagnostic-report",
            "transport_observed": False, "report_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "update_identifier": update, "building_state": building,
            "is_update_in_progress": updating, "registries": registries}
