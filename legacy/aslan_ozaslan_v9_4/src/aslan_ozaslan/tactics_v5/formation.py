from dataclasses import dataclass
from .domain import Formation
@dataclass(frozen=True)
class FormationValidation:
    valid:bool; issues:tuple[str,...]
class FormationValidator:
    SUPPORTED={'4-3-3':(4,3,3),'4-2-3-1':(4,5,1),'4-4-2':(4,4,2),'3-4-3':(3,4,3),'3-5-2':(3,5,2)}
    def validate(self,f):
        issues=[]
        try: f.validate()
        except ValueError as e: issues.append(str(e))
        expected=self.SUPPORTED.get(f.name)
        if expected is None: issues.append('unsupported_formation')
        elif expected!=(f.defenders,f.midfielders,f.forwards): issues.append('formation_shape_mismatch')
        return FormationValidation(not issues,tuple(issues))
