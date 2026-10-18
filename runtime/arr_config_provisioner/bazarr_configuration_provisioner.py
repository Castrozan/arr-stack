import json

from provisioner_logging import log

PAGE_SIZE = 100


def reconcile_profile(profiles, definition):
    matches = [profile for profile in profiles if profile["name"] == definition["name"]]
    if len(matches) > 1:
        raise ValueError("Bazarr has multiple profiles with the declared profile name")
    identifier = (
        matches[0]["profileId"]
        if matches
        else max((profile["profileId"] for profile in profiles), default=0) + 1
    )
    desired = {**definition, "profileId": identifier}
    current = matches[0] if matches else None
    changed = current is None or any(
        current.get(key) != value for key, value in desired.items()
    )
    reconciled = [
        profile for profile in profiles if profile["name"] != definition["name"]
    ]
    return reconciled + [desired], identifier, changed


def settings_changes(client, definition, profiles, identifier, profile_changed):
    settings = client.request("system/settings")["general"]
    languages = client.request("system/languages")
    enabled_languages = {
        language["code2"] for language in languages if language["enabled"]
    }
    changes = {}
    if not set(definition["languages"]).issubset(enabled_languages):
        changes["languages-enabled"] = sorted(
            enabled_languages | set(definition["languages"])
        )
    if profile_changed:
        changes["languages-profiles"] = json.dumps(profiles)
    providers = sorted(
        (set(settings.get("enabled_providers", [])) - {"podnapisi"})
        | set(definition["providers"])
    )
    if set(providers) != set(settings.get("enabled_providers", [])):
        changes["settings-general-enabled_providers"] = providers
    for prefix in ("movie", "serie"):
        if not settings.get(f"{prefix}_default_enabled"):
            changes[f"settings-general-{prefix}_default_enabled"] = True
        if str(settings.get(f"{prefix}_default_profile")) != str(identifier):
            changes[f"settings-general-{prefix}_default_profile"] = str(identifier)
    return changes


def assign_unconfigured_media(
    client, resource, identifier_key, form_key, profile_identifier, dry_run
):
    offset = 0
    assigned = 0
    while True:
        result = client.request(f"{resource}?start={offset}&length={PAGE_SIZE}")
        records = result.get("data", [])
        identifiers = [
            record[identifier_key]
            for record in records
            if record.get("profileId") is None
        ]
        if identifiers and not dry_run:
            client.request(
                resource,
                {
                    form_key: identifiers,
                    "profileid": [str(profile_identifier)] * len(identifiers),
                },
            )
        assigned += len(identifiers)
        offset += len(records)
        if not records or offset >= result.get("total", offset):
            return assigned


def provision_subtitles(client, definition, dry_run=False):
    profiles, identifier, profile_changed = reconcile_profile(
        client.request("system/languages/profiles"), definition["profile"]
    )
    changes = settings_changes(
        client, definition, profiles, identifier, profile_changed
    )
    if changes and not dry_run:
        client.request("system/settings", changes)
    assigned = sum(
        assign_unconfigured_media(
            client, resource, identifier_key, form_key, identifier, dry_run
        )
        for resource, identifier_key, form_key in (
            ("movies", "radarrId", "radarrid"),
            ("series", "sonarrSeriesId", "seriesid"),
        )
    )
    log(
        f"{'[dry-run] ' if dry_run else ''}Bazarr subtitles: {len(changes)} settings, {assigned} unassigned media"
    )
    return {"settings": len(changes), "assigned": assigned}
