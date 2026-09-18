import pytest

from app.translation.cache import TranslationCache


def test_languages_are_part_of_key():
    cache = TranslationCache()
    cache.put(("auto", "en", "same"), "English")
    cache.put(("auto", "ru", "same"), "Russian")
    assert cache.get(("auto", "en", "same")) == "English"
    assert cache.get(("auto", "ru", "same")) == "Russian"
    assert cache.get(("ja", "en", "same")) is None
    assert (cache.hits, cache.misses) == (2, 1)


def test_lru_hits_refresh_recency_and_evict():
    cache = TranslationCache(2)
    a, b, c = [("auto", "en", text) for text in "abc"]
    cache.put(a, "A")
    cache.put(b, "B")
    assert cache.get(a) == "A"
    cache.put(c, "C")
    assert cache.get(b) is None
    assert cache.get(a) == "A"
    assert len(cache) == 2
    cache.put(a, "updated")
    assert cache.get(a) == "updated"
    assert len(cache) == 2
    cache.clear()
    assert len(cache) == 0


def test_empty_value_is_not_a_miss():
    cache = TranslationCache()
    cache.put(("en", "en", ""), "")
    assert cache.get(("en", "en", "")) == ""


def test_invalid_capacity():
    with pytest.raises(ValueError):
        TranslationCache(0)
