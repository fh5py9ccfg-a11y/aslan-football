class Session {
  const Session({
    required this.token,
    required this.displayName,
    required this.role,
  });

  final String token;
  final String displayName;
  final String role;

  factory Session.fromJson(Map<String, dynamic> json) {
    return Session(
      token: json['token'] as String,
      displayName: json['display_name'] as String,
      role: json['role'] as String,
    );
  }
}

class Club {
  const Club({
    required this.id,
    required this.name,
  });

  final String id;
  final String name;

  factory Club.fromJson(Map<String, dynamic> json) {
    return Club(
      id: json['club_id'] as String,
      name: json['name'] as String,
    );
  }
}

class Player {
  const Player({
    required this.id,
    required this.name,
    required this.position,
    required this.availability,
    required this.marketValue,
  });

  final String id;
  final String name;
  final String position;
  final String availability;
  final double marketValue;

  factory Player.fromJson(Map<String, dynamic> json) {
    return Player(
      id: json['player_id'] as String,
      name: json['name'] as String,
      position: json['position'] as String,
      availability: json['availability'] as String? ?? 'AVAILABLE',
      marketValue: (json['market_value'] as num).toDouble(),
    );
  }
}

class MatchItem {
  const MatchItem({
    required this.id,
    required this.opponent,
    required this.competition,
    required this.status,
    required this.venue,
    this.goalsFor,
    this.goalsAgainst,
  });

  final String id;
  final String opponent;
  final String competition;
  final String status;
  final String venue;
  final int? goalsFor;
  final int? goalsAgainst;

  factory MatchItem.fromJson(Map<String, dynamic> json) {
    return MatchItem(
      id: json['match_id'] as String,
      opponent: json['opponent'] as String,
      competition: json['competition'] as String,
      status: json['status'] as String,
      venue: json['venue'] as String,
      goalsFor: json['goals_for'] as int?,
      goalsAgainst: json['goals_against'] as int?,
    );
  }
}


class MatchPredictionSummary {
  const MatchPredictionSummary({
    required this.predictionId,
    required this.homeTeam,
    required this.awayTeam,
    required this.predictedHomeGoals,
    required this.predictedAwayGoals,
    required this.homeWinProbability,
    required this.drawProbability,
    required this.awayWinProbability,
    required this.confidence,
  });

  final String predictionId;
  final String homeTeam;
  final String awayTeam;
  final int predictedHomeGoals;
  final int predictedAwayGoals;
  final double homeWinProbability;
  final double drawProbability;
  final double awayWinProbability;
  final String confidence;

  factory MatchPredictionSummary.fromJson(
    Map<String, dynamic> json,
  ) {
    return MatchPredictionSummary(
      predictionId: json['prediction_id'] as String,
      homeTeam: json['home_team'] as String,
      awayTeam: json['away_team'] as String,
      predictedHomeGoals:
          json['predicted_home_goals'] as int,
      predictedAwayGoals:
          json['predicted_away_goals'] as int,
      homeWinProbability:
          (json['home_win_probability'] as num).toDouble(),
      drawProbability:
          (json['draw_probability'] as num).toDouble(),
      awayWinProbability:
          (json['away_win_probability'] as num).toDouble(),
      confidence: json['confidence'] as String,
    );
  }
}
