
#include "shapeshifter.h"

int main() {
    vector<vector<string>> test_grids = {
        {"SLW","WLL","ELL"},
        {"SLLW", "LPWL", "LLLE"},
        {"SPWE", "LLLL", "LLLL"},
        {"SLLW", "LPWL", "LLLE"},
        {"SPLLE", "LPPWL", "LLLLE"},
        {"SLLLW", "LPPWL", "LWLWL", "LLLLE"},
        {"SLLWLL", "LPWPWL", "LWLWPL", "LLLPLL", "WWLLPL", "LLLLEL"}
    };

    int energy = 115;
    ofstream fout("results.txt");
    for (size_t t = 0; t < test_grids.size(); ++t) {
        Dungeon d;
        d.grid = test_grids[t];
        d.rows = d.grid.size();
        d.cols = d.grid[0].size();
        d.start = {0,0};
        d.initial_energy = energy;
        // Find exit cell 'E'
        bool found = false;
        for (int i = 0; i < d.rows && !found; ++i) {
            for (int j = 0; j < d.cols && !found; ++j) {
                if (d.grid[i][j] == 'E') {
                    d.exit = {i, j};
                    found = true;
                }
            }
        }
        State start(d.start.first, d.start.second, HUMAN, energy, {make_tuple(d.start.first,d.start.second,HUMAN,energy)});

        vector<tuple<int,int,Form,int>> sol;
        int final_energy;

        fout << "Test Case " << (t+1) << ":\n";
        fout << "Grid:" << endl;
        for (auto& row : d.grid) fout << row << endl;
        fout << endl;

        if (DFS(d, start, sol, final_energy)) {
            fout << "DFS Path: ";
            for (auto p: sol) {
                fout << "(" << get<0>(p) << "," << get<1>(p) << ",";
                if(get<2>(p)==HUMAN) fout << "HUMAN";
                else if(get<2>(p)==BIRD) fout << "BIRD";
                else fout << "FISH";
                fout << "," << get<3>(p) << ") ";
            }
            fout << "\nDFS Path Length: " << sol.size() << endl;
            fout << "DFS Energy Consumed: " << (energy - final_energy) << endl;
            fout << endl;
        } else {
            fout << "DFS: No path found\n";
        }
        if (BFS(d, start, sol, final_energy)) {
            fout << "BFS Path: ";
            for (auto p: sol) {
                fout << "(" << get<0>(p) << "," << get<1>(p) << ",";
                if(get<2>(p)==HUMAN) fout << "HUMAN";
                else if(get<2>(p)==BIRD) fout << "BIRD";
                else fout << "FISH";
                fout << "," << get<3>(p) << ") ";
            }
            fout << "\nBFS Path Length: " << sol.size() << endl;
            fout << "BFS Energy Consumed: " << (energy - final_energy) << endl;
            fout << endl;
        } else {
            fout << "BFS: No path found\n";
        }
        if (BestFS(d, start, sol, final_energy)) {
            fout << "BestFS Path: ";
            for (auto p: sol) {
                fout << "(" << get<0>(p) << "," << get<1>(p) << ",";
                if(get<2>(p)==HUMAN) fout << "HUMAN";
                else if(get<2>(p)==BIRD) fout << "BIRD";
                else fout << "FISH";
                fout << "," << get<3>(p) << ") ";
            }
            fout << "\nBestFS Path Length: " << sol.size() << endl;
            fout << "BestFS Energy Consumed: " << (energy - final_energy) << endl;
            fout << endl;
        } else {
            fout << "BestFS: No path found\n";
        }
        fout << "----------------------------------------\n";
    }
    fout.close();
    return 0;
}
