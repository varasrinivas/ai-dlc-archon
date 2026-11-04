"""Shell commands that write a workspace's team files from scratch (no download, no template repo).

Used by build_setup_page.py (step 2), build_python_page.py (step 1) and to write step 1 of the Java run page.
PowerShell: a single-quoted here-string (no $ or backtick expansion), written by WriteAllText as UTF-8 without a BOM
with LF endings, in Windows PowerShell 5.1 and PowerShell 7 alike. macOS: a quoted heredoc.
"""


def write_win(path, text):
    return (f"[IO.File]::WriteAllText(\"$PWD\\{path.replace('/', chr(92))}\", (@'\n{text.rstrip(chr(10))}\n'@"
            " -replace \"`r\", \"\") + \"`n\")")


def write_mac(path, text):
    return f"cat > {path} <<'EOF'\n{text.rstrip(chr(10))}\nEOF"


def writes(files, mac=False):
    """files: [(path, text)] -> one command per file, joined by newlines."""
    return "\n".join((write_mac if mac else write_win)(p, t.replace("\r\n", "\n")) for p, t in files)
