#ifndef SHAPESHIFTER_H
#define SHAPESHIFTER_H


#include <bits/stdc++.h>
#include <chrono>
using namespace std;


enum Form { HUMAN, BIRD, FISH };


struct AlgorithmMetrics {
    bool success;
    int nodes_explored;
    int path_length;
    int energy_consumed;
    double time_ms;
    string algorithm_name;
};


struct State {
    int x, y;
    Form form;
    int energy;
    vector<tuple<int,int,Form,int>> path;
    State(int _x, int _y, Form _f, int _e, vector<tuple<int,int,Form,int>> _p)
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


bool canMove(char cell);
Form requiredForm(char cell);

vector<State> MoveGen(const State& s, const Dungeon& d);


int heuristic(const State& s, const Dungeon& d);


bool DFS(const Dungeon& d, State start, vector<tuple<int,int,Form,int>>& solution, int& final_energy, int& nodes_explored);
bool BFS(const Dungeon& d, State start, vector<tuple<int,int,Form,int>>& solution, int& final_energy, int& nodes_explored);
bool BestFS(const Dungeon& d, State start, vector<tuple<int,int,Form,int>>& solution, int& final_energy, int& nodes_explored);


#endif