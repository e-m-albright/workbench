import pytest


@pytest.fixture(autouse=True)
def _personal_profile_by_default(monkeypatch):
    """A work shell exports DOTFILES_PROFILE; tests opt into it explicitly."""
    monkeypatch.delenv("DOTFILES_PROFILE", raising=False)
