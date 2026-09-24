from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.errors import TranslationError
from tools import install_translation_model, translation_smoke


def package_entry(source="en", target="ru", version="1.9", argos_version="1.9"):
    return SimpleNamespace(
        type="translate", from_code=source, to_code=target,
        package_version=version, argos_version=argos_version,
        download=Mock(return_value="/tmp/test.argosmodel"),
    )


def test_explicit_install_updates_index_selects_latest_compatible_and_prepares_auxiliary():
    entries = [package_entry(), package_entry(version="1.8"), package_entry("ru", "en"),
               package_entry(version="2.0", argos_version="99.0")]
    package = Mock(get_installed_packages=Mock(return_value=[]),
                   get_available_packages=Mock(return_value=entries))
    prepare, report = Mock(), Mock()
    install_translation_model.install_model("en", "ru", package, prepare, report)
    package.update_package_index.assert_called_once()
    entries[0].download.assert_called_once()
    for entry in entries[1:]:
        entry.download.assert_not_called()
    package.install_from_path.assert_called_once_with("/tmp/test.argosmodel")
    prepare.assert_called_once_with("en")


def test_existing_model_only_prepares_missing_auxiliary():
    package = Mock(get_installed_packages=Mock(return_value=[package_entry()]))
    prepare = Mock()
    install_translation_model.install_model("en", "ru", package, prepare, Mock())
    package.get_available_packages.assert_not_called()
    package.install_from_path.assert_not_called()
    prepare.assert_called_once_with("en")


def test_unsupported_direct_pair_does_not_download():
    entry = package_entry("ru", "en")
    package = Mock(get_installed_packages=Mock(return_value=[]),
                   get_available_packages=Mock(return_value=[entry]))
    prepare = Mock()
    with pytest.raises(TranslationError, match="No compatible direct Argos package"):
        install_translation_model.install_model("en", "ru", package, prepare, Mock())
    entry.download.assert_not_called()
    prepare.assert_not_called()


def test_invalid_model_install_request_does_not_touch_network():
    package = Mock()
    with pytest.raises(TranslationError):
        install_translation_model.install_model("auto", "ru", package, Mock())
    package.update_package_index.assert_not_called()


def test_installer_dependency_error_is_actionable(monkeypatch, capsys):
    monkeypatch.setattr(install_translation_model, "load_argos", Mock(side_effect=ImportError()))
    assert install_translation_model.main(["en", "ru"]) == 1
    assert "requirements-translation.txt" in capsys.readouterr().err


def test_installer_errors_are_sanitized(monkeypatch, capsys):
    monkeypatch.setattr(install_translation_model, "load_argos",
                        Mock(side_effect=OSError("private payload")))
    assert install_translation_model.main(["en", "ru"]) == 1
    error = capsys.readouterr().err
    assert "private payload" not in error and "Model setup failed" in error


def test_download_failure_never_reports_success():
    entry = package_entry()
    entry.download.side_effect = OSError("network unavailable")
    package = Mock(get_installed_packages=Mock(return_value=[]),
                   get_available_packages=Mock(return_value=[entry]))
    prepare = Mock()
    with pytest.raises(OSError):
        install_translation_model.install_model("en", "ru", package, prepare, Mock())
    package.install_from_path.assert_not_called()
    prepare.assert_not_called()


@pytest.mark.parametrize("result,exit_code", [("Привет мир!", 0), ("Hello world", 1)])
def test_smoke_uses_one_provider_and_checks_russian(monkeypatch, result, exit_code):
    factory = Mock(return_value=Mock(translate=Mock(return_value=result)))
    monkeypatch.setattr(translation_smoke, "ArgosLocalTranslationProvider", factory)
    assert translation_smoke.main() == exit_code
    factory.assert_called_once()


def test_smoke_missing_model_never_downloads(monkeypatch):
    monkeypatch.setattr(translation_smoke, "ArgosLocalTranslationProvider", Mock(
        return_value=Mock(translate=Mock(side_effect=TranslationError("missing model"))),
    ))
    assert translation_smoke.main() == 1
