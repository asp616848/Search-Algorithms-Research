#include "shapeshifter.h"

bool isValid(int x, int y, int R, int C) {
    return x >= 0 && y >= 0 && x < R && y < C;
}

bool GoalTest(const State& s, const Dungeon& d) {
    return (s.x == d.exit.first && s.y == d.exit.second && s.energy > 0);
}

bool canMove(char cell) {
    return (cell == 'L' || cell == 'S' || cell == 'E' || cell == 'W' || cell == 'P');
}

Form requiredForm(char cell) {
    if (cell == 'L' || cell == 'S' || cell == 'E') return HUMAN;
    if (cell == 'W') return FISH;
    if (cell == 'P') return BIRD;
    return HUMAN; // fallback
}

vector<State> MoveGen(const State& s, const Dungeon& d) {
    vector<State> successors;
    int dx[4] = {1,-1,0,0};
    int dy[4] = {0,0,1,-1};

    for (int i=0; i<4; i++) {
        int nx = s.x + dx[i], ny = s.y + dy[i];
        if (!isValid(nx, ny, d.rows, d.cols)) continue;
        char cell = d.grid[nx][ny];
        if (canMove(cell)) {
            Form f = requiredForm(cell);

            int cost = 1;  // base move cost
            if (f != s.form) cost += 2; // extra cost for transformation

            if (s.energy > cost) {
                auto newPath = s.path;
                newPath.push_back({nx, ny, f, s.energy - cost});
                successors.push_back(State(nx, ny, f, s.energy - cost, newPath));
            }
        }
    }
    return successors;
}

int heuristic(const State& s, const Dungeon& d) {
    int dist = abs(s.x - d.exit.first) + abs(s.y - d.exit.second);
    int energy_used = d.initial_energy - s.energy;
    return energy_used * 1000 + dist;
}
