from dataclasses import dataclass
@dataclass(frozen=True)
class TacticalMatchupReport:
    home_team_id:str; away_team_id:str; pressing_edge:float; width_edge:float; midfield_control_edge:float; transition_edge:float; set_piece_edge:float; overall_edge:float; advantage:str; explanations:tuple[str,...]
class TacticalMatchupAnalyzer:
    def analyze(self,home,away):
        home.validate(); away.validate()
        p=home.pressing*(1-away.possession)-away.pressing*(1-home.possession)
        w=home.width-away.width
        m=(home.possession+home.tempo)/2-(away.possession+away.tempo)/2
        t=home.transition_speed*away.defensive_line-away.transition_speed*home.defensive_line
        s=home.set_piece_strength-away.set_piece_strength
        overall=p*.20+w*.15+m*.25+t*.25+s*.15+.05
        advantage='HOME' if overall>.08 else 'AWAY' if overall<-.08 else 'BALANCED'
        exp=(f'Pres eşleşmesi: {p:+.3f}',f'Genişlik farkı: {w:+.3f}',f'Orta saha kontrolü: {m:+.3f}',f'Geçiş oyunu farkı: {t:+.3f}',f'Duran top farkı: {s:+.3f}','Ev sahibi bağlam avantajı: +0.050')
        return TacticalMatchupReport(home.team_id,away.team_id,p,w,m,t,s,overall,advantage,exp)
