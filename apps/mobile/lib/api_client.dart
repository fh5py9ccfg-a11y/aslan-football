import 'dart:convert';

import 'package:http/http.dart' as http;

import 'models.dart';

class ApiException implements Exception {
  ApiException(this.message);
  final String message;

  @override
  String toString() => message;
}

class AslanApiClient {
  AslanApiClient({
    required this.baseUrl,
    http.Client? client,
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final http.Client _client;

  Uri _uri(String path, [Map<String, String>? query]) {
    return Uri.parse('$baseUrl$path').replace(
      queryParameters: query,
    );
  }

  Future<Map<String, dynamic>> _json(
    http.Response response,
  ) async {
    if (response.statusCode < 200 ||
        response.statusCode >= 300) {
      throw ApiException(
        'API hatası: ${response.statusCode}',
      );
    }
    return jsonDecode(
      utf8.decode(response.bodyBytes),
    ) as Map<String, dynamic>;
  }

  Future<Session> login({
    required String username,
    required String password,
  }) async {
    final response = await _client.post(
      _uri('/mvp/auth/login', {
        'username': username,
        'password': password,
      }),
    );
    return Session.fromJson(
      await _json(response),
    );
  }

  Future<List<Club>> clubs() async {
    final response = await _client.get(
      _uri('/mvp/clubs'),
    );
    final data = await _json(response);
    return (data['items'] as List<dynamic>)
        .map(
          (item) => Club.fromJson(
            item as Map<String, dynamic>,
          ),
        )
        .toList(growable: false);
  }

  Future<Map<String, dynamic>> dashboard(
    String clubId,
  ) async {
    final response = await _client.get(
      _uri('/mvp/clubs/$clubId/dashboard'),
    );
    return _json(response);
  }

  Future<List<Player>> players(
    String clubId,
  ) async {
    final data = await dashboard(clubId);
    return (data['players'] as List<dynamic>)
        .map(
          (item) => Player.fromJson(
            item as Map<String, dynamic>,
          ),
        )
        .toList(growable: false);
  }

  Future<List<MatchItem>> matches(
    String clubId,
  ) async {
    final data = await dashboard(clubId);
    return (data['matches'] as List<dynamic>)
        .map(
          (item) => MatchItem.fromJson(
            item as Map<String, dynamic>,
          ),
        )
        .toList(growable: false);
  }


  Future<List<MatchPredictionSummary>> predictions(
    String clubId,
  ) async {
    final response = await _client.get(
      _uri('/mvp/intelligence/$clubId/predictions'),
    );
    final data = await _json(response);
    return (data['items'] as List<dynamic>)
        .map(
          (item) => MatchPredictionSummary.fromJson(
            item as Map<String, dynamic>,
          ),
        )
        .toList(growable: false);
  }

  Future<void> seedDemo() async {
    final response = await _client.post(
      _uri('/mvp/demo'),
    );
    if (response.statusCode < 200 ||
        response.statusCode >= 300) {
      throw ApiException(
        'Demo verisi kurulamadı',
      );
    }
  }

  void close() => _client.close();
}
