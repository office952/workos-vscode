# Migration and rollback

No new Alembic revision in F5.
Schema already carries `reverses_movement_id` from `s62`.
Rollback = revert application commit; no DB migration to undo.
