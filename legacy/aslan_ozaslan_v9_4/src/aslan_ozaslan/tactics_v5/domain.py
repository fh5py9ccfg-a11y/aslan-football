from dataclasses import dataclass
@dataclass(frozen=True)
class Formation:
    name:str; defenders:int; midfielders:int; forwards:int
    def validate(self):
        if not self.name.strip(): raise ValueError('Formasyon adı boş olamaz')
        if self.defenders<2 or self.midfielders<1 or self.forwards<1: raise ValueError('Geçersiz formasyon dağılımı')
        if self.defenders+self.midfielders+self.forwards!=10: raise ValueError('Kaleci hariç toplam 10 olmalıdır')
@dataclass(frozen=True)
class TacticalProfile:
    team_id:str; pressing:float; defensive_line:float; width:float; tempo:float; possession:float; transition_speed:float; directness:float; set_piece_strength:float
    def validate(self):
        if not self.team_id.strip(): raise ValueError('team_id boş olamaz')
        vals=(self.pressing,self.defensive_line,self.width,self.tempo,self.possession,self.transition_speed,self.directness,self.set_piece_strength)
        if any(v<0 or v>1 for v in vals): raise ValueError('Taktik metrikler 0 ile 1 arasında olmalıdır')
