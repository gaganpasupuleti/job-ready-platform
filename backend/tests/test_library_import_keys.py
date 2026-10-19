from app.library.import_keys import metadata_from_import_key


def test_metadata_from_import_key():
    title, category, _desc = metadata_from_import_key("library/import/Python/beginner-guide.pdf")
    assert title == "beginner guide"
    assert category == "Python"
