from math import exp, log
from .domain import LiveProbabilityState
class LiveProbabilityUpdater:
    def update(self, *, previous, current_minute, home_goals, away_goals, home_red_cards, away_red_cards, momentum):
        if not 0 <= current_minute <= 130: raise ValueError('current_minute geçersiz')
        remaining=max(0.0,(90-min(current_minute,90))/90.0)
        score_diff=home_goals-away_goals
        card_diff=away_red_cards-home_red_cards
        home_logit=self._logit(previous.home_probability)+score_diff*(1.4+(1.0-remaining))+card_diff*0.65+momentum.net_momentum*0.08
        away_logit=self._logit(previous.away_probability)-score_diff*(1.4+(1.0-remaining))-card_diff*0.65-momentum.net_momentum*0.08
        draw_score=max(0.01, previous.draw_probability-abs(score_diff)*0.18+remaining*0.08-abs(card_diff)*0.05)
        hs,aws=exp(home_logit),exp(away_logit)
        total=hs+draw_score+aws
        return LiveProbabilityState(current_minute,hs/total,draw_score/total,aws/total,home_goals,away_goals,home_red_cards,away_red_cards)
    def _logit(self,p):
        if not 0 < p < 1: raise ValueError('Olasılıklar açık aralıkta olmalıdır')
        return log(p/(1-p))
