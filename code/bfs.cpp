#include "shapeshifter.h"


bool BFS(const Dungeon& d, State start, vector<tuple<int,int,Form,int>>& solution, int& final_energy) {
    queue<State> open;
    set<tuple<int,int,Form>> closed;
    open.push(start);


    while (!open.empty()) {
        State cur = open.front(); open.pop();
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