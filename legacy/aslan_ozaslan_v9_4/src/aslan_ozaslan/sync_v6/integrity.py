from dataclasses import dataclass
from datetime import datetime
@dataclass(frozen=True)
class FixtureIntegrityResult:
    valid:bool; errors:tuple[str,...]
class FixtureIntegrityValidator:
    def validate(self,fixture):
        errors=[]
        if fixture.get('id') in (None,''): errors.append('fixture_id_missing')
        parts=fixture.get('participants') or []
        if len(parts)<2: errors.append('participants_missing')
        else:
            ids=[x.get('id') for x in parts if x.get('id') is not None]
            if len(set(ids))!=len(ids): errors.append('duplicate_participant')
        start=fixture.get('starting_at')
        if start:
            try: datetime.fromisoformat(str(start).replace('Z','+00:00'))
            except ValueError: errors.append('starting_at_invalid')
        for score in fixture.get('scores') or []:
            goals=(score.get('score') or {}).get('goals')
            if goals is not None and int(goals)<0: errors.append('negative_score')
        mins=[int(e.get('minute')) for e in fixture.get('events') or [] if e.get('minute') is not None]
        if mins!=sorted(mins): errors.append('event_order_invalid')
        return FixtureIntegrityResult(not errors,tuple(sorted(set(errors))))
