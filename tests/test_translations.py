"""Checks that translations and ``services.yaml`` stay in sync.

These run without Home Assistant, but they guard the same rules hassfest enforces in CI:
every service and field needs a translated name, every selector ``translation_key`` needs
options, and no user-facing text may sit in ``services.yaml`` (which is what caused the
bilingual strings the UI used to show).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

_INTEGRATION = Path(__file__).resolve().parent.parent / "custom_components" / "statistics_toolset"
_TRANSLATIONS = [
    _INTEGRATION / "strings.json",
    _INTEGRATION / "translations" / "en.json",
    _INTEGRATION / "translations" / "de.json",
]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def services() -> dict:
    return yaml.safe_load((_INTEGRATION / "services.yaml").read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", _TRANSLATIONS, ids=lambda p: p.name)
def test_every_service_and_field_is_translated(path: Path, services: dict) -> None:
    translated = _load(path)["services"]
    assert set(translated) == set(services), "service list differs from services.yaml"
    for name, conf in services.items():
        assert translated[name].get("name"), f"{name}: name missing"
        assert translated[name].get("description"), f"{name}: description missing"
        fields = set((conf or {}).get("fields", {}) or {})
        assert set(translated[name].get("fields", {})) == fields, f"{name}: field mismatch"


@pytest.mark.parametrize("path", _TRANSLATIONS, ids=lambda p: p.name)
def test_selector_options_are_translated(path: Path, services: dict) -> None:
    data = _load(path)
    for name, conf in services.items():
        for field, fconf in ((conf or {}).get("fields", {}) or {}).items():
            for sconf in ((fconf or {}).get("selector", {}) or {}).values():
                if not isinstance(sconf, dict) or "translation_key" not in sconf:
                    continue
                options = data["selector"][sconf["translation_key"]]["options"]
                missing = set(sconf.get("options", [])) - set(options)
                assert not missing, f"{name}.{field}: untranslated options {sorted(missing)}"


def test_services_yaml_carries_no_user_facing_text() -> None:
    """Text belongs in the translations; in services.yaml it would show every language."""
    lines = (_INTEGRATION / "services.yaml").read_text(encoding="utf-8").splitlines()
    offenders = [ln for ln in lines if re.match(r"\s*(name|description):", ln)]
    assert not offenders, f"move these into strings.json: {offenders}"


# Words that only ever appear in the other language. An em dash is not a signal — it is
# perfectly normal inside one language; a German word inside en.json is not.
_GERMAN_MARKERS = ("Zähler", "Schreibt", "Muss true", "Quelle", "Sicherung", "nur lesen")
_ENGLISH_MARKERS = ("Counter", "Writes to", "Must be true", "read-only mode", "backup file")


@pytest.mark.parametrize(
    ("path", "forbidden"),
    [
        (_INTEGRATION / "strings.json", _GERMAN_MARKERS),
        (_INTEGRATION / "translations" / "en.json", _GERMAN_MARKERS),
        (_INTEGRATION / "translations" / "de.json", _ENGLISH_MARKERS),
    ],
    ids=["strings.json", "en.json", "de.json"],
)
def test_translations_are_single_language(path: Path, forbidden: tuple[str, ...]) -> None:
    """No entry may pack two languages into one string (the old ``de — en`` pattern)."""
    text = json.dumps(_load(path), ensure_ascii=False)
    found = [marker for marker in forbidden if marker in text]
    assert not found, f"{path.name} contains other-language wording: {found}"


def test_exception_keys_used_in_code_exist() -> None:
    keys: set[str] = set()
    for py in _INTEGRATION.glob("*.py"):
        src = py.read_text(encoding="utf-8")
        keys |= set(re.findall(r'translation_key="([^"]+)"', src))
        keys |= set(re.findall(r'_translated\("([^"]+)"', src))
        # keys chosen by an inline conditional: translation_key=... if ... else "other"
        keys |= set(re.findall(r'translation_key=[^,\n]*?"([a-z_]+)"[^,\n]*?,', src))
    assert keys, "no translation keys found in the code at all"
    for path in _TRANSLATIONS:
        exceptions = set(_load(path)["exceptions"])
        assert keys <= exceptions, f"{path.name}: missing {sorted(keys - exceptions)}"


@pytest.mark.parametrize("path", _TRANSLATIONS, ids=lambda p: p.name)
def test_exception_placeholders_match_english(path: Path) -> None:
    """A translation must use exactly the placeholders the message is called with."""
    reference = _load(_INTEGRATION / "strings.json")["exceptions"]
    for key, entry in _load(path)["exceptions"].items():
        want = set(re.findall(r"\{(\w+)\}", reference[key]["message"]))
        got = set(re.findall(r"\{(\w+)\}", entry["message"]))
        assert got == want, f"{key}: placeholders {sorted(got)} != {sorted(want)}"
