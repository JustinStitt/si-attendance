def findCsrfInRawHTML(raw):
    raw = str(raw)
    needle = '"csrf-token" content="'
    needle_idx = raw.find(needle)
    if needle_idx == -1:
        raise Exception("Didn't find csrf token.")
    needle_idx += len(needle)
    slash_idx = raw[needle_idx:-1].find("/>") + needle_idx
    csrf = raw[needle_idx : slash_idx - 2]
    if len(csrf) != 88:
        raise Exception(
            f"Invalid length for csrf token. Got: {len(csrf)} | Expected: 88"
        )
    return csrf
