from modulesim.content import ContentStore


def test_critical_path_search_returns_the_critical_path_note_first():
    results = ContentStore().search("IS3328", "critical path")
    assert results[0]["title"] == "Critical path"


def test_search_finds_tolerances_for_escalation():
    results = ContentStore().search("IS3328", "escalate tolerance board")
    assert results[0]["title"] == "Tolerances and escalation"


def test_quote_check_accepts_real_quotes_and_rejects_made_up_ones():
    store = ContentStore()
    pid = store.search("IS3328", "critical path")[0]["id"]
    real = store.get(pid)["text"].split(". ")[0]
    assert store.quote_matches(pid, real)
    assert store.quote_matches(pid, "  " + real.upper() + " ")   # spacing and case do not matter
    assert not store.quote_matches(pid, "Critical tasks are always the most important ones")
    assert not store.quote_matches("no-such-note#1", real)
    assert not store.quote_matches(pid, "")


def test_unknown_module_has_no_passages():
    assert ContentStore().search("IS9999", "critical path") == []


def test_every_passage_has_an_id_title_and_text():
    store = ContentStore()
    assert store.modules() == ["IS3328"]
    for p in store.search("IS3328", "project", limit=50):
        assert p["id"] and p["title"] and p["text"]
