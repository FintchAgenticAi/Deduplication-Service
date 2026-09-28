def keep_first(records):
    """
    Keep the first record and discard subsequent duplicates.
    """

    if not records:
        return None

    return records[0]