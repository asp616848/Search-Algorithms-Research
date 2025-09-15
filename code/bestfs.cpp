#include "shapeshifter.h"

struct Compare {
    bool operator()(const State& a, const State& b) {
        return heuristic(a, *(Dungeon*)nullptr) > heuristic(b, *(Dungeon*)nullptr);
    }
};

bool BestFS(const Dungeon& d, State start, vector<pair<int,int>>& solution, int& final_energy) {
    auto cmp = [&](const State& a, const State& b){ return heuristic(a,d) > heuristic(b,d); };
    priority_queue<State, vector<State>, decltype(cmp)> open(cmp);
    set<tuple<int,int,Form>> closed;
    open.push(start);

    while (!open.empty()) {
        State cur = open.top(); open.pop();
        auto key = make_tuple(cur.x, cur.y, cur.form);
        if (closed.count(key)) continue;
        closed.insert(key);

        if (GoalTest(cur, d)) {
            solution = cur.path;
            final_energy = cur.energy;
            return true;
        }

        for (auto nxt : MoveGen(cur, d)) {
            auto nkey = make_tuple(nxt.x, nxt.y, nxt.form);
            if (!closed.count(nkey)) {
                open.push(nxt);
            }
        }
    }
    return false;
}
