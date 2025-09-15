#ifndef SHAPESHIFTER_H
#define SHAPESHIFTER_H

#include <bits/stdc++.h>
using namespace std;

enum Form { HUMAN, BIRD, FISH };

struct State {
    int x, y;
    Form form;
    int energy;
    vector<pair<int,int>> path;
    State(int _x, int _y, Form _f, int _e, vector<pair<int,int>> _p)
        : x(_x), y(_y), form(_f), energy(_e), path(_p) {}
};

struct Dungeon {
    vector<string> grid;
    int rows, cols;
    pair<int,int> start, exit;
    int initial_energy;
};

bool isValid(int x, int y, int R, int C);

bool GoalTest(const State& s, const Dungeon& d);

bool canMove(Form f, char cell);

vector<State> MoveGen(const State& s, const Dungeon& d);

int heuristic(const State& s, const Dungeon& d);

bool DFS(const Dungeon& d, State start, vector<pair<int,int>>& solution, int& final_energy);
bool BFS(const Dungeon& d, State start, vector<pair<int,int>>& solution, int& final_energy);
bool BestFS(const Dungeon& d, State start, vector<pair<int,int>>& solution, int& final_energy);

#endif
