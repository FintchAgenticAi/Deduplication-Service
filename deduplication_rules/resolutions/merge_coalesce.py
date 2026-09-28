def merge_coalesce(records):
    """
    Merge records by keeping the first non-empty value
    for each field.
    """

    if not records:
        return None

    merged = {}

    for record in records:
        for key, value in record.items():

            if key not in merged or merged[key] in (None, ""):
                if value not in (None, ""):
                    merged[key] = value

    return merged