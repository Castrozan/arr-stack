import copy
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "runtime/arr_config_provisioner"))

from bazarr_configuration_provisioner import provision_subtitles, reconcile_profile


class BazarrServer:
    def __init__(self):
        self.profiles = []
        self.languages = [{"code2": "ja", "enabled": True}]
        self.settings = {"enabled_providers": ["custom"]}
        self.media = {
            "movies": [
                {"radarrId": 4, "profileId": None},
                {"radarrId": 5, "profileId": 9},
            ],
            "series": [{"sonarrSeriesId": 6, "profileId": None}],
        }
        self.writes = []

    def request(self, path, form=None):
        if form is not None:
            self.writes.append((path, copy.deepcopy(form)))
            if path == "system/settings":
                if "languages-profiles" in form:
                    self.profiles = json.loads(form["languages-profiles"])
                if "languages-enabled" in form:
                    self.languages = [
                        {"code2": value, "enabled": True}
                        for value in form["languages-enabled"]
                    ]
                for key, value in form.items():
                    if key.startswith("settings-general-"):
                        self.settings[key.removeprefix("settings-general-")] = value
            else:
                identifier_key, form_key = (
                    ("radarrId", "radarrid")
                    if path == "movies"
                    else ("sonarrSeriesId", "seriesid")
                )
                for record in self.media[path]:
                    if record[identifier_key] in form[form_key]:
                        record["profileId"] = int(form["profileid"][0])
            return None
        if path == "system/languages/profiles":
            return copy.deepcopy(self.profiles)
        if path == "system/languages":
            return copy.deepcopy(self.languages)
        if path == "system/settings":
            return {"general": copy.deepcopy(self.settings)}
        resource = path.split("?")[0]
        parameters = parse_qs(path.split("?", 1)[1])
        start = int(parameters["start"][0])
        length = int(parameters["length"][0])
        return {
            "data": copy.deepcopy(self.media[resource][start : start + length]),
            "total": len(self.media[resource]),
        }


def definition():
    return json.loads((ROOT / "defaults/bazarr/subtitles.json").read_text())


def test_bootstraps_subtitles_without_overwriting_other_choices():
    server = BazarrServer()
    server.profiles = [{"profileId": 9, "name": "Custom profile", "items": []}]
    result = provision_subtitles(server, definition())
    assert result["assigned"] == 2
    assert server.profiles[0]["name"] == "Custom profile"
    assert server.profiles[1]["profileId"] == 10
    assert {language["code2"] for language in server.languages} == {"en", "pb", "ja"}
    assert set(server.settings["enabled_providers"]) == {
        "custom",
        "embeddedsubtitles",
        "podnapisi",
    }
    assert server.settings["movie_default_enabled"] is True
    assert server.settings["serie_default_profile"] == "10"
    assert [record["profileId"] for record in server.media["movies"]] == [10, 9]


def test_repeated_provisioning_does_not_rewrite_or_reassign():
    server = BazarrServer()
    provision_subtitles(server, definition())
    server.writes.clear()
    assert provision_subtitles(server, definition()) == {"settings": 0, "assigned": 0}
    assert server.writes == []


def test_dry_run_does_not_change_bazarr():
    server = BazarrServer()
    assert provision_subtitles(server, definition(), dry_run=True)["assigned"] == 2
    assert server.writes == []
    assert server.profiles == []


def test_duplicate_managed_profile_name_is_rejected():
    profile = definition()["profile"]
    with pytest.raises(ValueError, match="multiple profiles"):
        reconcile_profile(
            [{"profileId": 1, **profile}, {"profileId": 2, **profile}], profile
        )


def test_assignments_follow_bounded_library_pages():
    server = BazarrServer()
    server.media["series"] = [
        {"sonarrSeriesId": index, "profileId": None} for index in range(101)
    ]
    assert provision_subtitles(server, definition())["assigned"] == 102
    assignments = [form for path, form in server.writes if path == "series"]
    assert [len(form["seriesid"]) for form in assignments] == [100, 1]
