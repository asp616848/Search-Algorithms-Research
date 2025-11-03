#include "shapeshifter.h"


bool BestFS(const Dungeon& d, State start, vector<tuple<int,int,Form,int>>& solution, int& final_energy) {
    auto cmp = [&](const State& a, const State& b){ return heuristic(a,d) > heuristic(b,d); };
    priority_queue<State, vector<State>, decltype(cmp)> open(cmp);
    set<tuple<int,int,Form>> closed;
    open.push(start);

    bool found = false;
    int best_energy = -1;
    vector<tuple<int,int,Form,int>> best_path;

    while (!open.empty()) {
        State cur = open.top(); open.pop();
        auto key = make_tuple(cur.x, cur.y, cur.form);
        if (closed.count(key)) continue;
        closed.insert(key);

        if (GoalTest(cur, d)) {
            if (!found || cur.energy > best_energy) {
                best_energy = cur.energy;
                best_path = cur.path;
                found = true;
            }
            continue;
        }

        for (auto nxt : MoveGen(cur, d)) {
            auto nkey = make_tuple(nxt.x, nxt.y, nxt.form);
            if (!closed.count(nkey)) {
                open.push(nxt);
            }
        }
    }
    if (found) {
        solution = best_path;
        final_energy = best_energy;
        return true;
    }
    return false;
}