# CallHistory.storedata schema reference

`~/Library/Application Support/CallHistoryDB/CallHistory.storedata` is a plain
SQLite database underneath a Core Data `.storedata` extension. This skill opens it
read-only (`file:...?mode=ro`) and never writes to it. Only the columns this skill
actually queries are documented here.

Sources: [Call History Database - The Apple Wiki](https://theapplewiki.com/wiki/Call_History_Database),
[Call History Database (CallHistory.storedata) - DFIR Assist](https://forge-work.com/dfir/knowledge/artifacts/ios-call-history),
cross-checked against two independently-maintained forensics parsers that read this
same table in production:
[ydkhatri/mac_apt's `callhistory.py`](https://github.com/ydkhatri/mac_apt/blob/master/plugins/callhistory.py)
and [abrignoni/iLEAPP's `callHistory.py`](https://github.com/abrignoni/iLEAPP/blob/main/scripts/artifacts/callHistory.py).

## Table

Everything lives in one table, `ZCALLRECORD` — one row per call (phone, FaceTime
Audio, FaceTime Video, or a third-party CallKit-integrated app).

## Key columns

| Column | Meaning |
|---|---|
| `Z_PK` | Core Data internal primary key. Not exposed by this skill. |
| `ZDATE` | Call start time — Core Data reference-date **seconds** (float) since 2001-01-01 (see below). |
| `ZDURATION` | Call length in seconds. |
| `ZADDRESS` | The other party: a phone number or an Apple ID email. |
| `ZORIGINATED` | `0` = incoming, `1` = outgoing. |
| `ZANSWERED` | `0` = not answered (missed, if also incoming), `1` = answered. |
| `ZCALLTYPE` | `0` = third-party app (CallKit), `1` = phone (cellular), `8` = FaceTime Video, `16` = FaceTime Audio. Other values are surfaced as `other_<code>` rather than guessed. |
| `ZSERVICE_PROVIDER` | Freeform, undocumented by Apple — observed to hold things like a carrier name or an app identifier depending on call type. Passed through raw. |
| `ZISO_COUNTRY_CODE`, `ZLOCATION`, `ZFACE_TIME_DATA`, `ZDISCONNECTED_CAUSE`, `ZREAD` | Present in the real schema but not read by this skill — out of scope for what this phase needs (geo/location data in particular is deliberately not surfaced). |

## Core Data timestamp conversion

`ZDATE` is **seconds** (a float) since `2001-01-01T00:00:00Z` — the standard Core
Data / `NSDate` "reference date," used as-is with no additional scaling:

```python
APPLE_EPOCH_OFFSET = 978307200  # 2001-01-01 00:00:00 UTC in Unix seconds
unix_seconds = zdate_value + APPLE_EPOCH_OFFSET
```

**This differs from `chat.db`'s `message.date`,** which the Messages app schema
stores in *nanoseconds* since the same epoch — an iMessage-specific quirk documented
in the imessage skill's own `references/schema.md`. Dividing `ZDATE` by `1_000_000_000`
the way `chat.db` requires would produce a timestamp decades in the past; this
skill's `core_data_ts_to_dt`/`dt_to_core_data_ts` do the plain-seconds conversion
instead. Confirmed against both `mac_apt` and `iLEAPP`'s own conversion code (both
add `978307200` directly to `ZDATE`, no nanosecond scaling) rather than trusting a
single source.

## Example query

```sql
SELECT ZDATE, ZDURATION, ZADDRESS, ZORIGINATED, ZANSWERED, ZCALLTYPE, ZSERVICE_PROVIDER
FROM ZCALLRECORD
ORDER BY ZDATE DESC;
```

No join to another table is needed for the call data itself — contact-name
resolution is a separate join against the local AddressBook (see the imessage
skill's `references/schema.md` for that database's layout; this skill duplicates
the same resolution logic rather than depending on the imessage skill).
