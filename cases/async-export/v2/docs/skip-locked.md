# Why FOR UPDATE SKIP LOCKED?

Two workers can ask PostgreSQL for work at almost the same moment. A normal
SELECT lets both workers see the same pending row. Locking the selected row
prevents that race.

FOR UPDATE reserves the row for the current transaction. SKIP LOCKED tells
another worker not to wait for that row; it may immediately claim the next
pending job instead. Selection and transition to running happen in the same
transaction so the lock protects the complete claim operation.
