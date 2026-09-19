# CLAIM

Earned claim (and nothing beyond it):

"In the tested reference architecture, an owner-controlled STOP prevented
all seven covered post-stop consequence-survival paths from committing
protected effects. Stale receivers and pre-stop in-flight work were stopped
at a final consequence boundary that serialized effect commitment against
STOP_EFFECTIVE, and a separate auditor verified the resulting evidence."

## What this claim rests on

- 7/7 STOPPED under frozen appraisal rules (attempt + REFUSE +
  independently observed absence, per path).
- P6 closed without changing its semantics: R2's local cache was genuinely
  stale (epoch 0/ACTIVE) and admitted locally; the authoritative final gate
  refused.
- P7 closed without changing its semantics: pre-stop preliminary admission
  existed and was insufficient; finalization re-checked current authority.
- STOP/finalize ordering unambiguous: one serialization boundary,
  monotonic sequence, commit_seq 1 < stop_effective_seq 2 < all post-stop
  attempts; 20 race trials, 0 forbidden orderings.
- Restart and fail-closed checks hold; replays create no post-stop effect;
  recovery requires deliberate owner action.

## Not claimed

Universal AI shutdown; California compliance; regulatory certification;
production readiness; global distributed consensus; arbitrary external
effects always cancellable; protection against bypassing receivers;
protection against owner compromise; that any model stopped; third-party
validation; that OpenLine solved AI control.
