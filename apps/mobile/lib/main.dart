import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api_client.dart';
import 'models.dart';

void main() {
  runApp(const AslanFootballApp());
}

class AslanFootballApp extends StatelessWidget {
  const AslanFootballApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Aslan Football',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1D4ED8),
        ),
        useMaterial3: true,
      ),
      home: const LoginPage(),
    );
  }
}

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final username = TextEditingController(text: 'coach');
  final password = TextEditingController(text: 'coach123');
  bool busy = false;
  String? error;

  AslanApiClient get api => AslanApiClient(
        baseUrl: const String.fromEnvironment(
          'ASLAN_API_URL',
          defaultValue: 'http://10.0.2.2:8000',
        ),
      );

  Future<void> submit() async {
    setState(() {
      busy = true;
      error = null;
    });
    final client = api;
    try {
      final session = await client.login(
        username: username.text.trim(),
        password: password.text,
      );
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('token', session.token);
      if (!mounted) return;
      await Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => HomePage(
            session: session,
            api: api,
          ),
        ),
      );
    } catch (_) {
      setState(() {
        error = 'Giriş başarısız';
      });
    } finally {
      client.close();
      if (mounted) {
        setState(() => busy = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(
                maxWidth: 420,
              ),
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment:
                        CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'Aslan Football',
                        style: Theme.of(context)
                            .textTheme
                            .headlineMedium,
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Mobil teknik ekip çalışma alanı',
                      ),
                      const SizedBox(height: 24),
                      TextField(
                        controller: username,
                        decoration: const InputDecoration(
                          labelText: 'Kullanıcı adı',
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: password,
                        obscureText: true,
                        decoration: const InputDecoration(
                          labelText: 'Parola',
                        ),
                      ),
                      if (error != null) ...[
                        const SizedBox(height: 12),
                        Text(
                          error!,
                          style: const TextStyle(
                            color: Colors.red,
                          ),
                        ),
                      ],
                      const SizedBox(height: 20),
                      FilledButton(
                        onPressed: busy ? null : submit,
                        child: Text(
                          busy
                              ? 'Giriş yapılıyor...'
                              : 'Giriş yap',
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({
    required this.session,
    required this.api,
    super.key,
  });

  final Session session;
  final AslanApiClient api;

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int index = 0;
  List<Club> clubs = const [];
  Club? selectedClub;
  Map<String, dynamic>? dashboard;
  bool busy = true;
  String? error;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final items = await widget.api.clubs();
      if (items.isEmpty) {
        await widget.api.seedDemo();
      }
      final refreshed = await widget.api.clubs();
      final club = selectedClub ?? refreshed.first;
      final data = await widget.api.dashboard(club.id);
      setState(() {
        clubs = refreshed;
        selectedClub = club;
        dashboard = data;
      });
    } catch (_) {
      setState(() {
        error = 'Veriler yüklenemedi';
      });
    } finally {
      if (mounted) {
        setState(() => busy = false);
      }
    }
  }

  @override
  void dispose() {
    widget.api.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final pages = [
      DashboardView(data: dashboard),
      PlayersView(data: dashboard),
      MatchesView(data: dashboard),
    ];

    return Scaffold(
      appBar: AppBar(
        title: Text(
          selectedClub?.name ?? 'Aslan Football',
        ),
        actions: [
          IconButton(
            onPressed: load,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      drawer: NavigationDrawer(
        selectedIndex: index,
        onDestinationSelected: (value) {
          setState(() => index = value);
          Navigator.pop(context);
        },
        children: [
          Padding(
            padding: const EdgeInsets.all(20),
            child: Text(
              '${widget.session.displayName}
'
              '${widget.session.role}',
            ),
          ),
          const NavigationDrawerDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard),
            label: Text('Dashboard'),
          ),
          const NavigationDrawerDestination(
            icon: Icon(Icons.groups_outlined),
            selectedIcon: Icon(Icons.groups),
            label: Text('Oyuncular'),
          ),
          const NavigationDrawerDestination(
            icon: Icon(Icons.sports_soccer_outlined),
            selectedIcon: Icon(Icons.sports_soccer),
            label: Text('Maçlar'),
          ),
        ],
      ),
      body: busy
          ? const Center(
              child: CircularProgressIndicator(),
            )
          : error != null
              ? Center(child: Text(error!))
              : pages[index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (value) {
          setState(() => index = value);
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard),
            label: 'Dashboard',
          ),
          NavigationDestination(
            icon: Icon(Icons.groups_outlined),
            selectedIcon: Icon(Icons.groups),
            label: 'Oyuncular',
          ),
          NavigationDestination(
            icon: Icon(Icons.sports_soccer_outlined),
            selectedIcon: Icon(Icons.sports_soccer),
            label: 'Maçlar',
          ),
        ],
      ),
    );
  }
}

class DashboardView extends StatelessWidget {
  const DashboardView({
    required this.data,
    super.key,
  });

  final Map<String, dynamic>? data;

  @override
  Widget build(BuildContext context) {
    final summary = data?['summary']
        as Map<String, dynamic>?;

    if (summary == null) {
      return const Center(child: Text('Veri yok'));
    }

    final cards = <(String, Object?)>[
      ('Oyuncular', summary['player_count']),
      ('Hazır', summary['available_players']),
      ('Uygun değil', summary['unavailable_players']),
      ('Kadro değeri', '${summary['squad_value']} M€'),
      (
        'Form',
        '${summary['wins']}-'
            '${summary['draws']}-'
            '${summary['losses']}',
      ),
    ];

    return GridView.builder(
      padding: const EdgeInsets.all(16),
      gridDelegate:
          const SliverGridDelegateWithMaxCrossAxisExtent(
        maxCrossAxisExtent: 220,
        childAspectRatio: 1.5,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
      ),
      itemCount: cards.length,
      itemBuilder: (_, i) {
        final item = cards[i];
        return Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,
              children: [
                Text(item.$1),
                const Spacer(),
                Text(
                  '${item.$2}',
                  style: Theme.of(context)
                      .textTheme
                      .headlineMedium,
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class PlayersView extends StatelessWidget {
  const PlayersView({
    required this.data,
    super.key,
  });

  final Map<String, dynamic>? data;

  @override
  Widget build(BuildContext context) {
    final items = (data?['players']
                as List<dynamic>? ??
            const [])
        .map(
          (json) => Player.fromJson(
            json as Map<String, dynamic>,
          ),
        )
        .toList(growable: false);

    return ListView.separated(
      padding: const EdgeInsets.all(12),
      itemCount: items.length,
      separatorBuilder: (_, __) =>
          const SizedBox(height: 8),
      itemBuilder: (_, i) {
        final player = items[i];
        return Card(
          child: ListTile(
            leading: CircleAvatar(
              child: Text(player.position),
            ),
            title: Text(player.name),
            subtitle: Text(
              '${player.availability} · '
              '${player.marketValue} M€',
            ),
          ),
        );
      },
    );
  }
}

class MatchesView extends StatelessWidget {
  const MatchesView({
    required this.data,
    super.key,
  });

  final Map<String, dynamic>? data;

  @override
  Widget build(BuildContext context) {
    final items = (data?['matches']
                as List<dynamic>? ??
            const [])
        .map(
          (json) => MatchItem.fromJson(
            json as Map<String, dynamic>,
          ),
        )
        .toList(growable: false);

    return ListView.separated(
      padding: const EdgeInsets.all(12),
      itemCount: items.length,
      separatorBuilder: (_, __) =>
          const SizedBox(height: 8),
      itemBuilder: (_, i) {
        final match = items[i];
        final score = match.goalsFor == null
            ? '-'
            : '${match.goalsFor} - '
                '${match.goalsAgainst}';
        return Card(
          child: ListTile(
            leading: const Icon(
              Icons.sports_soccer,
            ),
            title: Text(match.opponent),
            subtitle: Text(
              '${match.competition} · '
              '${match.venue} · ${match.status}',
            ),
            trailing: Text(score),
          ),
        );
      },
    );
  }
}
