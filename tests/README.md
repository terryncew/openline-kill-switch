# tests/

`test_packaging.py` — stdlib-only hermeticity checks for the publication
candidate. These verify the standalone-clone properties, not the
kill-switch mechanism (the mechanism is exercised by the probe suite in
`src/`, via `./RUN.sh`):

- no absolute host paths (`/home/`, `/workspace/`, `~`) in `src/`
- no network imports anywhere in `src/`
- the receiver import closure contains no `stop_authority` import and no
  `OWNER_KEY` material (the D3 property, mechanically checked)
- `OWNER_KEY` is defined in exactly one module (`stop_authority.py`)
- the vendored durable-store bytes match the sha256 pinned in
  `src/vendor/VENDORING.md`

Run: `python3 -m unittest discover -s tests` from the repo root.
