from dataclasses import dataclass
@dataclass(frozen=True)
class PostgresMigrationPlan:
    source_engine:str
    target_engine:str
    ordered_steps:tuple[str,...]
def build_postgres_migration_plan():
    return PostgresMigrationPlan('sqlite','postgresql',('freeze-writes','backup-source','create-target-schema','migrate-data','verify-row-counts','verify-foreign-keys','switch-read-traffic','switch-write-traffic','monitor-and-rollback-if-needed'))
def validate_postgres_dsn(dsn):
    if not dsn.startswith(('postgresql://','postgres://')): raise ValueError('Geçerli PostgreSQL DSN gerekli')
    if '@' not in dsn or '/' not in dsn.rsplit('@',1)[-1]: raise ValueError('Eksik PostgreSQL DSN')
