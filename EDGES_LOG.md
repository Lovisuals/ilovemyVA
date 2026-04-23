# EDGES_LOG.md — MedLocumContentBot v1.3

Append new entries immediately upon discovery. Reference before any change.

## EDGE-001 — Scheduler fires during FSM edit
- Risk: Double-publish / publish of partial content
- Mitigation: Check bucket='scheduled' AND editing_lock=None in publish_job

## EDGE-002 — Media group (album) from owner
- Risk: Duplicate ContentItem rows per album photo
- Mitigation: 1s buffer on media_group_id; unique DB constraint

## EDGE-003 — Gemini returns malformed JSON
- Risk: Crashes tone check; blocks publish
- Mitigation: ToneService try/except ValidationError → fallback ToneResult

## EDGE-004 — Bot downtime causes scheduler misfire
- Risk: Post never sent; item stuck in 'scheduled'
- Mitigation: misfire_grace_time=120s; startup job recovery loop

## EDGE-005 — Bot loses channel admin rights mid-broadcast
- Risk: Partial broadcast; owner unaware
- Mitigation: Catch ChatAdminRequired → log BC-PERM → notify owner → continue other targets

## EDGE-006 — Content hash collision on legitimate re-post
- Risk: Legitimate post skipped as duplicate
- Mitigation: 'Force Broadcast' button bypasses dedup; logged as force=True

## EDGE-007 — DB connection pool exhaustion under burst
- Risk: Paginated list timeouts under load
- Mitigation: pool_timeout=30s; Redis page cache TTL=10s; owner notified DB-POOL
