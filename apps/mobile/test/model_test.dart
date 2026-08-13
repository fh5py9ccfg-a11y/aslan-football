import 'package:flutter_test/flutter_test.dart';
import 'package:aslan_football_mobile/models.dart';

void main() {
  test('player parses availability', () {
    final player = Player.fromJson({
      'player_id': 'p1',
      'name': 'Oyuncu',
      'position': 'ST',
      'availability': 'AVAILABLE',
      'market_value': 3.5,
    });

    expect(player.availability, 'AVAILABLE');
    expect(player.marketValue, 3.5);
  });

  test('match parses nullable score', () {
    final match = MatchItem.fromJson({
      'match_id': 'm1',
      'opponent': 'Rakip',
      'competition': 'Lig',
      'status': 'SCHEDULED',
      'venue': 'HOME',
      'goals_for': null,
      'goals_against': null,
    });

    expect(match.goalsFor, isNull);
  });
}
