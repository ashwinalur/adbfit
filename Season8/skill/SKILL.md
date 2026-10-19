# FFC side copy data pull

## Pull the leaderboards read only

- Open the two public Strava club pages in a `browser.browse` task: the Odds club at `https://www.strava.com/clubs/2240003` and the Evens club at `https://www.strava.com/clubs/2240010`.

- Instruct the browser task to stay read only with no login and no state changes, select the Last Week leaderboard tab, and extract every row as `rank | name | athlete profile url | moving time | activities | distance | elev gain`.

- Confirm the Last Week tab covers the expected Monday to Sunday week. Strava does not always print the date range on the page, so infer it from the current date.

- Save the extracted rows as JSON in `~/workspace/ffc-season8/` under the `<Week>_rows.json` name, using the `[rank, name, url, time, acts, dist, elev]` row shape.

## Run the local pipeline

- Run the week builder script in `~/workspace/ffc-season8/`, for example `python3 build_oct12.py`. It rebuilds the Strava export HTML shape from the rows JSON and runs `stravaupdater-alma-fit-8.py`, which dedupes athletes appearing in both clubs and writes the weekly CSV.

- The updater needs `bs4` and `pandas`. Install with `pip install --break-system-packages beautifulsoup4` when the import fails.

- Expect roughly 110 unique athletes after removing about 7 cross club duplicates. Investigate when the count moves far from that.

- The CSV columns are A Athlete, B Time in minutes, C Activities, D Distance, E Elev gain, F Strava URL, G Strava ID, with one header row plus one row per athlete.

## Update the side copy

- Write only to the side copy workbook `1t7ks-KraK3f1i8KAumJc6mnpGE5UpVGVnV1AhzUMnTc`. Never write the main copy `1-_PCB1gXXXyxy6YRhBp90PXeKj3mjMD9Q6d5snjPFSA` or the verification workbook `1yJf-p57m3dYsXkdSYyHfBWCPL8K_yNbDZnPei5c9HcA`. You may read the main copy for comparison, never write it.

- Write the weekly CSV into a new tab named for the week start, for example `Oct12`, covering range A1:G with `values update` and `valueInputOption` `RAW`. RAW matters: Master Tracking looks up the Strava ID as text with `trim($E{row})`, so writing the ID column as numbers breaks every XLOOKUP and zeroes the week. Keep every cell as the CSV string and let the formula `value()` wrapper do the numeric conversion.

- Extend Master Tracking with the new week column. First put the week start date in the header cell, for example V2, because the formulas derive the tab name from it with `text(V$2,"mmmdd")`. Then fill rows 3 to 129 with this pattern, replacing V with the new column letter:
  `=min(1680,value(XLOOKUP(trim($E{row}),INDIRECT("'"&text(V$2,"mmmdd")&"'!$G$1:$G$200"),INDIRECT("'"&text(V$2,"mmmdd")&"'!$B$1:$B$200"),0)))`
  Column E holds the athlete Strava ID, column G of the weekly tab holds Strava IDs, and column B holds minutes, so each cell becomes that athlete's weekly minutes capped at 1680. Use `valueInputOption` `USER_ENTERED` so the formulas parse.

- Do not extend columns past the newest weekly tab. INDIRECT to a missing tab throws #REF! and breaks the SUM base score, so a column for a future week stays empty until that weekly tab exists.

## Verify before finishing

- Read the new formulas back with `valueRenderOption` `FORMULA` on a sample of rows and confirm the tab name resolves.

- Recompute the Solo Leaderboard and Team leaderboard totals independently from Master Tracking and compare with the sheet values. Both tabs are paste values shells whose rank and medal formulas read Master Tracking, so they must match.

- Leave the COTW and Streaks Weekly Tracking tabs alone. They are IMPORTRANGE mirrors of the form responses workbook and stay current on their own.

- Expect Master Tracking row 60 (Milli Seth) to show team "Not Found" with #N/A in the normalized columns. That quirk predates this workflow, so mention it only when it changes.

## Available connectors

- [Google Sheets](/opt/hatch/connectors/google_sheets/CONNECTOR.md) for reading and writing the side copy workbook.

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Websites

- [Strava club leaderboards](https://www.strava.com/clubs/2240003) for the read only pull. Carry the club IDs, the Last Week tab requirement, and the exact row format into the `browser.browse` task, and sanity check the row counts against the prior week before running the pipeline.
