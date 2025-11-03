/*
 * StrongBot - Elite Othello Bot with Advanced Techniques
 * Based on tournament-level strategies for comparison testing
 */

#include "Othello.h"
#include "OthelloBoard.h"
#include "OthelloPlayer.h"
#include <cstdlib>
#include <algorithm>
#include <limits>
#include <chrono>
#include <vector>
#include <unordered_map>
using namespace std;
using namespace Desdemona;

class StrongBot: public OthelloPlayer
{
public:
    StrongBot(Turn turn);
    virtual Move play(const OthelloBoard& board);

private:
    static const int INF = 1000000;
    
    // Enhanced position weights based on tournament play
    int positionWeights[8][8];
    
    chrono::time_point<chrono::high_resolution_clock> startTime;
    double timeLimit;
    int nodesSearched;
    
    struct TranspositionEntry {
        int depth;
        int value;
        int flag; // 0=exact, 1=lower, 2=upper
    };
    
    unordered_map<uint64_t, TranspositionEntry> transpositionTable;
    
    void initializeWeights();
    uint64_t hashBoard(const OthelloBoard& board);
    int evaluateBoard(const OthelloBoard& board, Turn player);
    int negamax(OthelloBoard& board, int depth, int alpha, int beta, Turn player);
    Move selectBestMove(const OthelloBoard& board);
    bool timeUp();
    
    // Evaluation components
    int evaluateMobility(const OthelloBoard& board, Turn player);
    int evaluateCorners(const OthelloBoard& board, Turn player);
    int evaluateStability(const OthelloBoard& board, Turn player);
    int evaluatePotentialMobility(const OthelloBoard& board, Turn player);
    int evaluateParity(const OthelloBoard& board, Turn player);
    
    vector<Move> orderMoves(const list<Move>& moves, const OthelloBoard& board, Turn player);
    bool isStable(const OthelloBoard& board, int x, int y, Turn player);
};

StrongBot::StrongBot(Turn turn) : OthelloPlayer(turn)
{
    initializeWeights();
    timeLimit = 1.90; // Conservative time limit
    nodesSearched = 0;
}

void StrongBot::initializeWeights()
{
    // Research-backed position weights
    int weights[8][8] = {
        {120, -20,  20,   5,   5,  20, -20, 120},
        {-20, -40,  -5,  -5,  -5,  -5, -40, -20},
        { 20,  -5,  15,   3,   3,  15,  -5,  20},
        {  5,  -5,   3,   3,   3,   3,  -5,   5},
        {  5,  -5,   3,   3,   3,   3,  -5,   5},
        { 20,  -5,  15,   3,   3,  15,  -5,  20},
        {-20, -40,  -5,  -5,  -5,  -5, -40, -20},
        {120, -20,  20,   5,   5,  20, -20, 120}
    };
    
    for(int i = 0; i < 8; i++) {
        for(int j = 0; j < 8; j++) {
            positionWeights[i][j] = weights[i][j];
        }
    }
}

bool StrongBot::timeUp()
{
    auto currentTime = chrono::high_resolution_clock::now();
    chrono::duration<double> elapsed = currentTime - startTime;
    return elapsed.count() > timeLimit;
}

uint64_t StrongBot::hashBoard(const OthelloBoard& board)
{
    uint64_t hash = 0;
    for(int i = 0; i < 8; i++) {
        for(int j = 0; j < 8; j++) {
            Turn t = board.get(i, j);
            if(t != EMPTY) {
                hash ^= ((uint64_t)(t == BLACK ? 1 : 2)) << (i * 8 + j);
            }
        }
    }
    return hash;
}

int StrongBot::evaluateParity(const OthelloBoard& board, Turn player)
{
    Turn opponent = other(player);
    int myCount = (player == BLACK) ? board.getBlackCount() : board.getRedCount();
    int oppCount = (opponent == BLACK) ? board.getBlackCount() : board.getRedCount();
    
    if(myCount + oppCount == 0) return 0;
    return 100 * (myCount - oppCount) / (myCount + oppCount);
}

int StrongBot::evaluateMobility(const OthelloBoard& board, Turn player)
{
    Turn opponent = other(player);
    int myMobility = board.getValidMoves(player).size();
    int oppMobility = board.getValidMoves(opponent).size();
    
    if(myMobility + oppMobility == 0) return 0;
    return 100 * (myMobility - oppMobility) / (myMobility + oppMobility);
}

bool StrongBot::isStable(const OthelloBoard& board, int x, int y, Turn player)
{
    // Simplified stability: corners and adjacent to corners are stable
    if((x == 0 || x == 7) && (y == 0 || y == 7)) return true;
    
    // Check if adjacent to a corner of same color
    if(x <= 1 || x >= 6) {
        if(y <= 1 || y >= 6) {
            if((x == 0 || x == 7) || (y == 0 || y == 7)) {
                return board.get(x, y) == player;
            }
        }
    }
    return false;
}

int StrongBot::evaluateStability(const OthelloBoard& board, Turn player)
{
    Turn opponent = other(player);
    int myStable = 0, oppStable = 0;
    
    for(int i = 0; i < 8; i++) {
        for(int j = 0; j < 8; j++) {
            if(board.get(i, j) == player && isStable(board, i, j, player)) {
                myStable++;
            } else if(board.get(i, j) == opponent && isStable(board, i, j, opponent)) {
                oppStable++;
            }
        }
    }
    
    if(myStable + oppStable == 0) return 0;
    return 100 * (myStable - oppStable) / (myStable + oppStable);
}

int StrongBot::evaluateCorners(const OthelloBoard& board, Turn player)
{
    Turn opponent = other(player);
    int myCorners = 0, oppCorners = 0;
    
    int corners[4][2] = {{0,0}, {0,7}, {7,0}, {7,7}};
    for(int i = 0; i < 4; i++) {
        int x = corners[i][0], y = corners[i][1];
        if(board.get(x, y) == player) myCorners++;
        else if(board.get(x, y) == opponent) oppCorners++;
    }
    
    if(myCorners + oppCorners == 0) return 0;
    return 100 * (myCorners - oppCorners) / (myCorners + oppCorners);
}

int StrongBot::evaluatePotentialMobility(const OthelloBoard& board, Turn player)
{
    // Count empty squares adjacent to opponent pieces
    Turn opponent = other(player);
    int myPotential = 0, oppPotential = 0;
    
    int dx[] = {-1, -1, -1, 0, 0, 1, 1, 1};
    int dy[] = {-1, 0, 1, -1, 1, -1, 0, 1};
    
    for(int i = 0; i < 8; i++) {
        for(int j = 0; j < 8; j++) {
            if(board.get(i, j) == EMPTY) {
                bool adjToMine = false, adjToOpp = false;
                for(int k = 0; k < 8; k++) {
                    int ni = i + dx[k], nj = j + dy[k];
                    if(ni >= 0 && ni < 8 && nj >= 0 && nj < 8) {
                        if(board.get(ni, nj) == player) adjToMine = true;
                        if(board.get(ni, nj) == opponent) adjToOpp = true;
                    }
                }
                if(adjToOpp) myPotential++;
                if(adjToMine) oppPotential++;
            }
        }
    }
    
    if(myPotential + oppPotential == 0) return 0;
    return 100 * (myPotential - oppPotential) / (myPotential + oppPotential);
}

int StrongBot::evaluateBoard(const OthelloBoard& board, Turn player)
{
    int totalPieces = board.getBlackCount() + board.getRedCount();
    
    int parity = evaluateParity(board, player);
    int mobility = evaluateMobility(board, player);
    int corners = evaluateCorners(board, player);
    int stability = evaluateStability(board, player);
    int potential = evaluatePotentialMobility(board, player);
    
    // Position-based evaluation
    int positional = 0;
    Turn opponent = other(player);
    for(int i = 0; i < 8; i++) {
        for(int j = 0; j < 8; j++) {
            if(board.get(i, j) == player) {
                positional += positionWeights[i][j];
            } else if(board.get(i, j) == opponent) {
                positional -= positionWeights[i][j];
            }
        }
    }
    
    // Dynamic weights based on game phase
    if(totalPieces < 20) {
        // Opening: mobility and position
        return 15 * mobility + 10 * positional + 80 * corners + 5 * stability + 8 * potential;
    } else if(totalPieces < 50) {
        // Midgame: balanced
        return 8 * parity + 12 * mobility + 8 * positional + 60 * corners + 8 * stability + 5 * potential;
    } else {
        // Endgame: disc count matters
        return 25 * parity + 5 * mobility + 4 * positional + 40 * corners + 6 * stability;
    }
}

vector<Move> StrongBot::orderMoves(const list<Move>& moves, const OthelloBoard& board, Turn player)
{
    vector<pair<int, Move>> scoredMoves;
    
    for(const Move& move : moves) {
        int score = 0;
        
        // Corner moves are highest priority
        if((move.x == 0 || move.x == 7) && (move.y == 0 || move.y == 7)) {
            score += 100000;
        }
        // Avoid X-squares (diagonal to corners) unless corner is taken
        else if((move.x == 1 && move.y == 1)) {
            if(board.get(0, 0) == EMPTY) score -= 50000;
        }
        else if((move.x == 1 && move.y == 6)) {
            if(board.get(0, 7) == EMPTY) score -= 50000;
        }
        else if((move.x == 6 && move.y == 1)) {
            if(board.get(7, 0) == EMPTY) score -= 50000;
        }
        else if((move.x == 6 && move.y == 6)) {
            if(board.get(7, 7) == EMPTY) score -= 50000;
        }
        // Edge moves are good
        else if(move.x == 0 || move.x == 7 || move.y == 0 || move.y == 7) {
            score += 10000;
        }
        
        score += positionWeights[move.x][move.y] * 100;
        
        // Prefer moves that capture more pieces
        OthelloBoard testBoard = board;
        testBoard.makeMove(player, move);
        int captured = (player == BLACK ? testBoard.getBlackCount() : testBoard.getRedCount()) -
                      (player == BLACK ? board.getBlackCount() : board.getRedCount());
        score += captured * 10;
        
        scoredMoves.push_back({score, move});
    }
    
    sort(scoredMoves.begin(), scoredMoves.end(),
         [](const pair<int, Move>& a, const pair<int, Move>& b) {
             return a.first > b.first;
         });
    
    vector<Move> result;
    for(const auto& sm : scoredMoves) {
        result.push_back(sm.second);
    }
    return result;
}

int StrongBot::negamax(OthelloBoard& board, int depth, int alpha, int beta, Turn player)
{
    nodesSearched++;
    
    if(depth == 0 || timeUp()) {
        return player == turn ? evaluateBoard(board, turn) : -evaluateBoard(board, turn);
    }
    
    uint64_t hash = hashBoard(board);
    auto it = transpositionTable.find(hash);
    if(it != transpositionTable.end() && it->second.depth >= depth) {
        TranspositionEntry& entry = it->second;
        if(entry.flag == 0) return entry.value; // Exact
        if(entry.flag == 1 && entry.value > alpha) alpha = entry.value; // Lower
        if(entry.flag == 2 && entry.value < beta) beta = entry.value;   // Upper
        if(alpha >= beta) return entry.value;
    }
    
    list<Move> moves = board.getValidMoves(player);
    
    if(moves.empty()) {
        Turn opponent = other(player);
        list<Move> oppMoves = board.getValidMoves(opponent);
        if(oppMoves.empty()) {
            int finalScore = evaluateBoard(board, turn);
            return player == turn ? finalScore : -finalScore;
        }
        return -negamax(board, depth - 1, -beta, -alpha, opponent);
    }
    
    vector<Move> orderedMoves = orderMoves(moves, board, player);
    int bestValue = -INF;
    int origAlpha = alpha;
    
    for(const Move& move : orderedMoves) {
        OthelloBoard newBoard = board;
        newBoard.makeMove(player, move);
        int value = -negamax(newBoard, depth - 1, -beta, -alpha, other(player));
        bestValue = max(bestValue, value);
        alpha = max(alpha, value);
        
        if(alpha >= beta) break; // Beta cutoff
        if(timeUp()) break;
    }
    
    // Store in transposition table
    TranspositionEntry entry;
    entry.depth = depth;
    entry.value = bestValue;
    if(bestValue <= origAlpha) entry.flag = 2; // Upper bound
    else if(bestValue >= beta) entry.flag = 1;  // Lower bound
    else entry.flag = 0; // Exact
    transpositionTable[hash] = entry;
    
    return bestValue;
}

Move StrongBot::selectBestMove(const OthelloBoard& board)
{
    list<Move> moves = board.getValidMoves(turn);
    
    if(moves.empty()) return Move::pass();
    if(moves.size() == 1) return moves.front();
    
    Move bestMove = moves.front();
    
    // Iterative deepening with aspiration windows
    for(int depth = 1; depth <= 12 && !timeUp(); depth++) {
        nodesSearched = 0;
        transpositionTable.clear();
        
        Move currentBest = moves.front();
        int bestValue = -INF;
        
        vector<Move> orderedMoves = orderMoves(moves, board, turn);
        
        for(const Move& move : orderedMoves) {
            if(timeUp()) break;
            
            OthelloBoard newBoard = board;
            newBoard.makeMove(turn, move);
            
            int value = -negamax(newBoard, depth - 1, -INF, INF, other(turn));
            
            if(value > bestValue) {
                bestValue = value;
                currentBest = move;
            }
        }
        
        if(!timeUp()) {
            bestMove = currentBest;
        }
    }
    
    return bestMove;
}

Move StrongBot::play(const OthelloBoard& board)
{
    startTime = chrono::high_resolution_clock::now();
    return selectBestMove(board);
}

extern "C" {
    OthelloPlayer* createBot(Turn turn)
    {
        return new StrongBot(turn);
    }

    void destroyBot(OthelloPlayer* bot)
    {
        delete bot;
    }
}
