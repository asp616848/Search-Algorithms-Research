
#include "shapeshifter.h"
#include <iomanip>

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
    
    // Store all metrics for final comparison table
    vector<vector<AlgorithmMetrics>> all_metrics;
    
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
        int nodes_explored;
        vector<AlgorithmMetrics> test_metrics;

        fout << "Test Case " << (t+1) << ":\n";
        fout << "Grid:" << endl;
        for (auto& row : d.grid) fout << row << endl;
        fout << endl;

        // DFS Algorithm
        AlgorithmMetrics dfs_metrics;
        dfs_metrics.algorithm_name = "DFS";
        auto start_time = chrono::high_resolution_clock::now();
        dfs_metrics.success = DFS(d, start, sol, final_energy, nodes_explored);
        auto end_time = chrono::high_resolution_clock::now();
        dfs_metrics.time_ms = chrono::duration<double, milli>(end_time - start_time).count();
        dfs_metrics.nodes_explored = nodes_explored;
        
        if (dfs_metrics.success) {
            dfs_metrics.path_length = sol.size();
            dfs_metrics.energy_consumed = energy - final_energy;
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
            fout << "DFS Nodes Explored: " << nodes_explored << endl;
            fout << "DFS Time: " << dfs_metrics.time_ms << " ms" << endl;
            fout << endl;
        } else {
            dfs_metrics.path_length = 0;
            dfs_metrics.energy_consumed = 0;
            fout << "DFS: No path found\n";
            fout << "DFS Nodes Explored: " << nodes_explored << endl;
            fout << "DFS Time: " << dfs_metrics.time_ms << " ms" << endl;
        }
        test_metrics.push_back(dfs_metrics);
        // BFS Algorithm
        AlgorithmMetrics bfs_metrics;
        bfs_metrics.algorithm_name = "BFS";
        start_time = chrono::high_resolution_clock::now();
        bfs_metrics.success = BFS(d, start, sol, final_energy, nodes_explored);
        end_time = chrono::high_resolution_clock::now();
        bfs_metrics.time_ms = chrono::duration<double, milli>(end_time - start_time).count();
        bfs_metrics.nodes_explored = nodes_explored;
        
        if (bfs_metrics.success) {
            bfs_metrics.path_length = sol.size();
            bfs_metrics.energy_consumed = energy - final_energy;
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
            fout << "BFS Nodes Explored: " << nodes_explored << endl;
            fout << "BFS Time: " << bfs_metrics.time_ms << " ms" << endl;
            fout << endl;
        } else {
            bfs_metrics.path_length = 0;
            bfs_metrics.energy_consumed = 0;
            fout << "BFS: No path found\n";
            fout << "BFS Nodes Explored: " << nodes_explored << endl;
            fout << "BFS Time: " << bfs_metrics.time_ms << " ms" << endl;
        }
        test_metrics.push_back(bfs_metrics);
        // BestFS Algorithm
        AlgorithmMetrics bestfs_metrics;
        bestfs_metrics.algorithm_name = "BestFS";
        start_time = chrono::high_resolution_clock::now();
        bestfs_metrics.success = BestFS(d, start, sol, final_energy, nodes_explored);
        end_time = chrono::high_resolution_clock::now();
        bestfs_metrics.time_ms = chrono::duration<double, milli>(end_time - start_time).count();
        bestfs_metrics.nodes_explored = nodes_explored;
        
        if (bestfs_metrics.success) {
            bestfs_metrics.path_length = sol.size();
            bestfs_metrics.energy_consumed = energy - final_energy;
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
            fout << "BestFS Nodes Explored: " << nodes_explored << endl;
            fout << "BestFS Time: " << bestfs_metrics.time_ms << " ms" << endl;
            fout << endl;
        } else {
            bestfs_metrics.path_length = 0;
            bestfs_metrics.energy_consumed = 0;
            fout << "BestFS: No path found\n";
            fout << "BestFS Nodes Explored: " << nodes_explored << endl;
            fout << "BestFS Time: " << bestfs_metrics.time_ms << " ms" << endl;
        }
        test_metrics.push_back(bestfs_metrics);
        
        // Add test case comparison table
        fout << "\nComparison Table for Test Case " << (t+1) << ":\n";
        fout << "+-----------+----------+---------------+--------+----------+----------+\n";
        fout << "| Algorithm | Success  | Nodes Explrd  | Length | Energy   | Time(ms) |\n";
        fout << "+-----------+----------+---------------+--------+----------+----------+\n";
        for (auto& metric : test_metrics) {
            fout << "| " << setw(9) << left << metric.algorithm_name 
                 << " | " << setw(8) << (metric.success ? "Success" : "Failed")
                 << " | " << setw(13) << metric.nodes_explored
                 << " | " << setw(6) << metric.path_length
                 << " | " << setw(8) << metric.energy_consumed
                 << " | " << setw(8) << fixed << setprecision(2) << metric.time_ms << " |\n";
        }
        fout << "+-----------+----------+---------------+--------+----------+----------+\n";
        
        all_metrics.push_back(test_metrics);
        fout << "----------------------------------------\n";
    }
    
    // Overall summary table
    fout << "\n" << string(80, '=') << "\n";
    fout << "OVERALL ALGORITHM COMPARISON SUMMARY\n";
    fout << string(80, '=') << "\n\n";
    
    // Calculate averages and totals
    map<string, vector<double>> algo_stats;
    map<string, int> success_count;
    
    for (const auto& test_metrics : all_metrics) {
        for (const auto& metric : test_metrics) {
            algo_stats[metric.algorithm_name].push_back(metric.nodes_explored);
            algo_stats[metric.algorithm_name].push_back(metric.path_length);
            algo_stats[metric.algorithm_name].push_back(metric.energy_consumed);
            algo_stats[metric.algorithm_name].push_back(metric.time_ms);
            if (metric.success) success_count[metric.algorithm_name]++;
        }
    }
    
    fout << "Algorithm Performance Summary (Averages across all test cases):\n";
    fout << "+----------+------------+---------------+--------+----------+----------+\n";
    fout << "| Algo     | Success    | Avg Nodes     | Avg    | Avg      | Avg      |\n";
    fout << "| Name     | Rate       | Explored      | Length | Energy   | Time(ms) |\n";
    fout << "+----------+------------+---------------+--------+----------+----------+\n";
    
    for (const auto& algo : {"DFS", "BFS", "BestFS"}) {
        if (algo_stats.find(algo) != algo_stats.end()) {
            auto& stats = algo_stats[algo];
            int total_tests = test_grids.size();
            double success_rate = (double)success_count[algo] / total_tests * 100;
            
            // Calculate averages (every 4th element corresponds to nodes, length, energy, time)
            double avg_nodes = 0, avg_length = 0, avg_energy = 0, avg_time = 0;
            for (size_t i = 0; i < stats.size(); i += 4) {
                avg_nodes += stats[i];
                avg_length += stats[i+1];
                avg_energy += stats[i+2];
                avg_time += stats[i+3];
            }
            avg_nodes /= total_tests;
            avg_length /= total_tests;
            avg_energy /= total_tests;
            avg_time /= total_tests;
            
            fout << "| " << setw(8) << left << algo
                 << " | " << setw(10) << fixed << setprecision(1) << success_rate << "%"
                 << " | " << setw(13) << fixed << setprecision(1) << avg_nodes
                 << " | " << setw(6) << fixed << setprecision(1) << avg_length
                 << " | " << setw(8) << fixed << setprecision(1) << avg_energy
                 << " | " << setw(8) << fixed << setprecision(3) << avg_time << " |\n";
        }
    }
    fout << "+----------+------------+---------------+--------+----------+----------+\n";
    
    fout.close();
    return 0;
}
