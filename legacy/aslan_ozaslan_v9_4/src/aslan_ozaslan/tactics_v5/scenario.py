from dataclasses import dataclass
@dataclass(frozen=True)
class MatchScenario:
    minute:int; goal_difference:int; red_card_difference:int; protecting_lead:bool
    def validate(self):
        if not 0<=self.minute<=130: raise ValueError('Dakika değeri geçersiz')
        if not -3<=self.goal_difference<=3: raise ValueError('goal_difference aralık dışında')
        if not -2<=self.red_card_difference<=2: raise ValueError('red_card_difference aralık dışında')
@dataclass(frozen=True)
class ScenarioAdjustment:
    pressing:float; defensive_line:float; tempo:float; transition_speed:float; risk_level:str; explanation:tuple[str,...]
class TacticalScenarioEngine:
    def adjust(self,profile,scenario):
        profile.validate(); scenario.validate(); p=profile.pressing; l=profile.defensive_line; tempo=profile.tempo; tr=profile.transition_speed; reasons=[]
        if scenario.goal_difference<0:
            p=min(1,p+.15); l=min(1,l+.10); tempo=min(1,tempo+.12); reasons.append('Geriye düşüldüğü için risk artırıldı')
        elif scenario.goal_difference>0 and scenario.protecting_lead:
            p=max(0,p-.10); l=max(0,l-.15); tempo=max(0,tempo-.10); tr=min(1,tr+.08); reasons.append('Skor korunurken blok derinliği azaltıldı')
        if scenario.red_card_difference<0:
            p=max(0,p-.18); reasons.append('Eksik oyuncu nedeniyle merkez kompaktlığı önceliklendirildi')
        if scenario.minute>=75 and scenario.goal_difference<0:
            tempo=min(1,tempo+.10); tr=min(1,tr+.10); reasons.append('Son bölümde hücum temposu yükseltildi')
        risk=(p+l+tempo)/3; label='HIGH' if risk>=.72 else 'MEDIUM' if risk>=.45 else 'LOW'
        return ScenarioAdjustment(p,l,tempo,tr,label,tuple(reasons or ['Temel taktik profil korundu']))
