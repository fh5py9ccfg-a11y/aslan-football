from dataclasses import dataclass
@dataclass(frozen=True)
class TacticalCompatibility:
    lineup_value_component:float; chemistry_component:float; fatigue_component:float; tactical_intensity_component:float; compatibility_score:float
class TacticalCompatibilityEvaluator:
    def evaluate(self,lineup,profile):
        profile.validate(); value=min(lineup.total_value/100,1); chemistry=lineup.chemistry_score; fatigue=max(0,1-lineup.fatigue_penalty); intensity=1-abs(profile.pressing-fatigue)*.5
        score=value*.35+chemistry*.30+fatigue*.20+intensity*.15
        return TacticalCompatibility(value,chemistry,fatigue,intensity,max(0,min(score,1)))
