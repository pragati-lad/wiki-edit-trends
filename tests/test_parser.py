from ingestion.parser import is_anonymous, parse_event
from tests.conftest import SAMPLE_SSE_EVENT, SAMPLE_SSE_EVENT_ANON, SAMPLE_SSE_EVENT_BOT


class TestIsAnonymous:
    def test_ipv4(self):
        assert is_anonymous("192.168.1.1") is True

    def test_ipv6(self):
        assert is_anonymous("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True

    def test_username(self):
        assert is_anonymous("ExampleUser") is False

    def test_empty(self):
        assert is_anonymous("") is False

    def test_ipv4_like_but_not(self):
        assert is_anonymous("999.999.999.999") is True  # regex matches the pattern

    def test_short_ipv6(self):
        assert is_anonymous("::1") is True


class TestParseEvent:
    def test_basic_edit(self):
        edit = parse_event(SAMPLE_SSE_EVENT)
        assert edit is not None
        assert edit.wiki == "enwiki"
        assert edit.title == "Python (programming language)"
        assert edit.edit_type == "edit"
        assert edit.user == "ExampleUser"
        assert edit.is_bot is False
        assert edit.is_anonymous is False
        assert edit.comment == "Fixed typo in introduction"
        assert edit.comment_length == len("Fixed typo in introduction")
        assert edit.length_old == 5000
        assert edit.length_new == 5020
        assert edit.edit_size_delta == 20
        assert edit.revision_old == 12345
        assert edit.revision_new == 12346

    def test_anonymous_edit(self):
        edit = parse_event(SAMPLE_SSE_EVENT_ANON)
        assert edit is not None
        assert edit.is_anonymous is True
        assert edit.comment == ""
        assert edit.comment_length == 0
        assert edit.edit_size_delta == -2000

    def test_bot_edit(self):
        edit = parse_event(SAMPLE_SSE_EVENT_BOT)
        assert edit is not None
        assert edit.is_bot is True

    def test_missing_type(self):
        data = {**SAMPLE_SSE_EVENT}
        del data["type"]
        assert parse_event(data) is None

    def test_unknown_type(self):
        data = {**SAMPLE_SSE_EVENT, "type": "categorize"}
        assert parse_event(data) is None

    def test_missing_wiki(self):
        data = {**SAMPLE_SSE_EVENT}
        del data["wiki"]
        assert parse_event(data) is None

    def test_missing_timestamp(self):
        data = {**SAMPLE_SSE_EVENT, "meta": {}}
        assert parse_event(data) is None

    def test_new_page_event(self):
        data = {**SAMPLE_SSE_EVENT, "type": "new", "length": {"old": 0, "new": 500}}
        edit = parse_event(data)
        assert edit is not None
        assert edit.edit_type == "new"
        assert edit.length_old == 0
        assert edit.edit_size_delta == 500
