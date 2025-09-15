#include "shapeshifter.h"

bool isValid(int x, int y, int R, int C) {
    return x >= 0 && y >= 0 && x < R && y < C;
}

bool GoalTest(const State& s, const Dungeon& d) {
    return (s.x == d.exit.first && s.y == d.exit.second && s.energy > 0);
}

bool canMove(Form f, char cell) {
    if (f == HUMAN && cell == 'L') return true;
    if (f == FISH && cell == 'W') return true;
    if (f == BIRD && (cell == 'L' || cell == 'E')) return true;
    if (f == HUMAN && cell == 'E') return true;
    if (f == FISH && cell == 'E') return true;
    return false;
}

vector<State> MoveGen(const State& s, const Dungeon& d) {
    vector<State> successors;
    int dx[4] = {1,-1,0,0};
    int dy[4] = {0,0,1,-1};

    for (int i=0; i<4; i++) {
        int nx = s.x + dx[i], ny = s.y + dy[i];
        if (!isValid(nx, ny, d.rows, d.cols)) continue;
        char cell = d.grid[nx][ny];
        if (canMove(s.form, cell) && s.energy > 1) {
            auto newPath = s.path;
            newPath.push_back({nx, ny});
            successors.push_back(State(nx, ny, s.form, s.energy - 1, newPath));
        }
    }

    for (int f=0; f<3; f++) {
        if (f != s.form && s.energy > 2) {
            auto newPath = s.path;
            newPath.push_back({s.x, s.y});
            successors.push_back(State(s.x, s.y, (Form)f, s.energy - 2, newPath));
        }
    }

    return successors;
}

int heuristic(const State& s, const Dungeon& d) {
    // Lower energy used is better (energy consumed = initial - current)
    // Distance to exit as tiebreaker
    int dist = abs(s.x - d.exit.first) + abs(s.y - d.exit.second);
    int energy_used = d.initial_energy - s.energy;
    return energy_used * 1000 + dist; // Energy takes precedence
}
