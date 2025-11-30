/*
 * @file SuperiorBot.cpp
 * @description Elite Othello Bot - Defeats MyBot by large margins
 * @optimizations Advanced evaluation, proper TT, better search
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
#include <cstring>

using namespace std;
using namespace Desdemona;

class SuperiorBot: public OthelloPlayer
{
public:
    SuperiorBot(Turn turn);
    virtual Move play(const OthelloBoard& board);
    
private:
    static const int INF = 1000000000;
    
    // Transposition table
    struct TTEntry {
        uint64_t hash;
        int depth;
        int value;
        int alpha;
        int beta;
        Move bestMove;
    };
    unordered_map<uint64_t, TTEntry> transTable;
    
    // Time management
    chrono::time_point<chrono::high_resolution_clock> startTime;
    double timeLimit;
    bool timeLimitReached;
    
    // Move ordering
    Move killerMoves[64][2];
    int historyTable[8][8];
    Move pvMove;
    bool hasPvMove;
    
    // Position evaluation weights - optimized for dominance
    int earlyWeights[8][8];
    int midWeights[8][8];
    int lateWeights[8][8];
    
    void initializeWeights();
    uint64_t hashBoard(const OthelloBoard& board);
    bool timeUp();
    
    // Core search
    int negamax(OthelloBoard& board, int depth, int alpha, int beta, Turn player, int ply);
    Move getBestMove(const OthelloBoard& board);
    
    // Evaluation
    int evaluateBoard(const OthelloBoard& board, Turn player);
    int getCornerControl(const OthelloBoard& board, Turn player);
    int getMobilityScore(const OthelloBoard& board, Turn player);
    int getStabilityScore(const OthelloBoard& board, Turn player);
    int getEdgeControl(const OthelloBoard& board, Turn player);
    int getPotentialMobility(const OthelloBoard& board, Turn player);
    int getFrontierScore(const OthelloBoard& board, Turn player);
    bool isStableDisc(const OthelloBoard& board, int x, int y, Turn player);
    
    // Move ordering
    vector<Move> orderMoves(const list<Move>& moves, const OthelloBoard& board, Turn player, int ply);
    int scoreMoveOrdering(const Move& move, const OthelloBoard& board, Turn player, int ply);
    
    // Helpers
    bool isCorner(int x, int y);
    bool isXSquare(int x, int y);
    bool isCSquare(int x, int y);
    bool isEdge(int x, int y);
    bool cornerCaptured(int x, int y, const OthelloBoard& board);
};

SuperiorBot::SuperiorBot(Turn turn)
    : OthelloPlayer(turn), timeLimitReached(false), hasPvMove(false)
{
    initializeWeights();
    timeLimit = 1.90;
    
    for(int i = 0; i < 64; i++) {
        killerMoves[i][0] = Move::pass();
        killerMoves[i][1] = Move::pass();
    }
    
    memset(historyTable, 0, sizeof(historyTable));
}

void SuperiorBot::initializeWeights()
{
    // Aggressive early game - mobility and avoiding bad squares
    int early[8][8] = {
        {200, -80,  40,  20,  20,  40, -80, 200},
        {-80,-100, -20, -10, -10, -20,-100, -80},
        { 40, -20,  20,   5,   5,  20, -20,  40},
        { 20, -10,   5,   3,   3,   5, -10,  20},
        { 20, -10,   5,   3,   3,   5, -10,  20},
        { 40, -20,  20,   5,   5,  20, -20,  40},
        {-80,-100, -20, -10, -10, -20,-100, -80},
        {200, -80,  40,  20,  20,  40, -80, 200}
    };
    
    // Balanced mid game
    int mid[8][8] = {
        {180, -40,  30,  15,  15,  30, -40, 180},
        {-40, -60,  -5,  -3,  -3,  -5, -60, -40},
        { 30,  -5,  25,   8,   8,  25,  -5,  30},
        { 15,  -3,   8,   5,   5,   8,  -3,  15},
        { 15,  -3,   8,   5,   5,   8,  -3,  15},
        { 30,  -5,  25,   8,   8,  25,  -5,  30},
        {-40, -60,  -5,  -3,  -3,  -5, -60, -40},
        {180, -40,  30,  15,  15,  30, -40, 180}
    };
    
    // Late game - disc count matters more
    int late[8][8] = {
        {150, -20,  25,  18,  18,  25, -20, 150},
        {-20, -30,  10,   8,   8,  10, -30, -20},
        { 25,  10,  20,  15,  15,  20,  10,  25},
        { 18,   8,  15,  12,  12,  15,   8,  18},
        { 18,   8,  15,  12,  12,  15,   8,  18},
        { 25,  10,  20,  15,  15,  20,  10,  25},
        {-20, -30,  10,   8,   8,  10, -30, -20},
        {150, -20,  25,  18,  18,  25, -20, 150}
    };
    
    memcpy(earlyWeights, early, sizeof(early));
    memcpy(midWeights, mid, sizeof(mid));
    memcpy(lateWeights, late, sizeof(late));
}

bool SuperiorBot::timeUp()
{
    if(timeLimitReached) return true;
    
    auto currentTime = chrono::high_resolution_clock::now();
    chrono::duration<double> elapsed = currentTime - startTime;
    if(elapsed.count() > timeLimit) {
        timeLimitReached = true;
        return true;
    }
    return false;
}

uint64_t SuperiorBot::hashBoard(const OthelloBoard& board)
{
    uint64_t hash = 0;
    for(int i = 0; i < 8; i++) {
        for(int j = 0; j < 8; j++) {
            Turn cell = board.get(i, j);
            hash = hash * 3 + (cell == BLACK ? 1 : (cell == RED ? 2 : 0));
        }
    }
    return hash;
}

bool SuperiorBot::isCorner(int x, int y) {
    return (x == 0 || x == 7) && (y == 0 || y == 7);
}

bool SuperiorBot::isXSquare(int x, int y) {
    return ((x == 1 || x == 6) && (y == 1 || y == 6));
}

bool SuperiorBot::isCSquare(int x, int y) {
    return ((x == 0 || x == 7) && (y == 1 || y == 6)) ||
           ((x == 1 || x == 6) && (y == 0 || y == 7));
}

bool SuperiorBot::isEdge(int x, int y) {
    return (x == 0 || x == 7 || y == 0 || y == 7) && !isCorner(x, y);
}

bool SuperiorBot::cornerCaptured(int x, int y, const OthelloBoard& board) {
    if(x <= 1 && y <= 1) return board.get(0, 0) != EMPTY;
    if(x <= 1 && y >= 6) return board.get(0, 7) != EMPTY;
    if(x >= 6 && y <= 1) return board.get(7, 0) != EMPTY;
    if(x >= 6 && y >= 6) return board.get(7, 7) != EMPTY;
    return false;
}

int SuperiorBot::getCornerControl(const OthelloBoard& board, Turn player)
{
    int score = 0;
    Turn opp = other(player);
    
    if(board.get(0, 0) == player) score += 100;
    else if(board.get(0, 0) == opp) score -= 100;
    
    if(board.get(0, 7) == player) score += 100;
    else if(board.get(0, 7) == opp) score -= 100;
    
    if(board.get(7, 0) == player) score += 100;
    else if(board.get(7, 0) == opp) score -= 100;
    
    if(board.get(7, 7) == player) score += 100;
    else if(board.get(7, 7) == opp) score -= 100;
    
    return score;
}

int SuperiorBot::getMobilityScore(const OthelloBoard& board, Turn player)
{
    int myMoves = board.getValidMoves(player).size();
    int oppMoves = board.getValidMoves(other(player)).size();
    
    if(myMoves + oppMoves == 0) return 0;
    return 100 * (myMoves - oppMoves) / (myMoves + oppMoves + 1);
}

int SuperiorBot::getPotentialMobility(const OthelloBoard& board, Turn player)
{
    Turn opp = other(player);
    int potential = 0;
    int dx[] = {-1, -1, -1, 0, 0, 1, 1, 1};
    int dy[] = {-1, 0, 1, -1, 1, -1, 0, 1};
    
    for(int i = 0; i < 8; i++) {
        for(int j = 0; j < 8; j++) {
            if(board.get(i, j) == opp) {
                for(int k = 0; k < 8; k++) {
                    int ni = i + dx[k];
                    int nj = j + dy[k];
                    if(ni >= 0 && ni < 8 && nj >= 0 && nj < 8 && board.get(ni, nj) == EMPTY) {
                        potential++;
                        break;
                    }
                }
            }
        }
    }
    return potential;
}

bool SuperiorBot::isStableDisc(const OthelloBoard& board, int x, int y, Turn player)
{
    if(board.get(x, y) != player) return false;
    
    // Corners are always stable
    if(isCorner(x, y)) return true;
    
    // Check if disc is stable along all 4 directions
    int dx[] = {0, 1, 1, 1};
    int dy[] = {1, 1, 0, -1};
    
    for(int dir = 0; dir < 4; dir++) {
        bool stable1 = false, stable2 = false;
        
        // Check positive direction
        int nx = x + dx[dir], ny = y + dy[dir];
        while(nx >= 0 && nx < 8 && ny >= 0 && ny < 8) {
            if(board.get(nx, ny) != player) break;
            if(isCorner(nx, ny)) { stable1 = true; break; }
            nx += dx[dir]; ny += dy[dir];
        }
        if(nx < 0 || nx >= 8 || ny < 0 || ny >= 8) stable1 = true;
        
        // Check negative direction
        nx = x - dx[dir]; ny = y - dy[dir];
        while(nx >= 0 && nx < 8 && ny >= 0 && ny < 8) {
            if(board.get(nx, ny) != player) break;
            if(isCorner(nx, ny)) { stable2 = true; break; }
            nx -= dx[dir]; ny -= dy[dir];
        }
        if(nx < 0 || nx >= 8 || ny < 0 || ny >= 8) stable2 = true;
        
        if(!stable1 && !stable2) return false;
    }
    
    return true;
}

int SuperiorBot::getStabilityScore(const OthelloBoard& board, Turn player)
{
    int myStable = 0, oppStable = 0;
    Turn opp = other(player);
    
    for(int i = 0; i < 8; i++) {
        for(int j = 0; j < 8; j++) {
            if(isStableDisc(board, i, j, player)) myStable++;
            if(isStableDisc(board, i, j, opp)) oppStable++;
        }
    }
    
    return myStable - oppStable;
}

int SuperiorBot::getEdgeControl(const OthelloBoard& board, Turn player)
{
    int score = 0;
    Turn opp = other(player);
    
    // Check all edges
    for(int i = 0; i < 8; i++) {
        if(board.get(0, i) == player) score += 5;
        else if(board.get(0, i) == opp) score -= 5;
        
        if(board.get(7, i) == player) score += 5;
        else if(board.get(7, i) == opp) score -= 5;
        
        if(board.get(i, 0) == player) score += 5;
        else if(board.get(i, 0) == opp) score -= 5;
        
        if(board.get(i, 7) == player) score += 5;
        else if(board.get(i, 7) == opp) score -= 5;
    }
    
    return score;
}

int SuperiorBot::getFrontierScore(const OthelloBoard& board, Turn player)
{
    int myFrontier = 0, oppFrontier = 0;
    Turn opp = other(player);
    int dx[] = {-1, -1, -1, 0, 0, 1, 1, 1};
    int dy[] = {-1, 0, 1, -1, 1, -1, 0, 1};
    
    for(int i = 0; i < 8; i++) {
        for(int j = 0; j < 8; j++) {
            if(board.get(i, j) == player) {
                for(int k = 0; k < 8; k++) {
                    int ni = i + dx[k];
                    int nj = j + dy[k];
                    if(ni >= 0 && ni < 8 && nj >= 0 && nj < 8 && board.get(ni, nj) == EMPTY) {
                        myFrontier++;
                        break;
                    }
                }
            } else if(board.get(i, j) == opp) {
                for(int k = 0; k < 8; k++) {
                    int ni = i + dx[k];
                    int nj = j + dy[k];
                    if(ni >= 0 && ni < 8 && nj >= 0 && nj < 8 && board.get(ni, nj) == EMPTY) {
                        oppFrontier++;
                        break;
                    }
                }
            }
        }
    }
    
    return oppFrontier - myFrontier;
}

int SuperiorBot::evaluateBoard(const OthelloBoard& board, Turn player)
{
    int myPieces = (player == BLACK) ? board.getBlackCount() : board.getRedCount();
    int oppPieces = (player == BLACK) ? board.getRedCount() : board.getBlackCount();
    int totalPieces = myPieces + oppPieces;
    int emptySquares = 64 - totalPieces;
    
    // Piece differential
    int pieceDiff = 0;
    if(totalPieces > 0) {
        pieceDiff = 100 * (myPieces - oppPieces) / totalPieces;
    }
    
    // Mobility
    int mobility = getMobilityScore(board, player);
    
    // Potential mobility
    int potentialMob = getPotentialMobility(board, player);
    
    // Corner control
    int corners = getCornerControl(board, player);
    
    // Stability
    int stability = getStabilityScore(board, player);
    
    // Edge control
    int edges = getEdgeControl(board, player);
    
    // Frontier discs
    int frontier = getFrontierScore(board, player);
    
    // Positional score
    int (*weights)[8] = midWeights;
    if(totalPieces < 20) weights = earlyWeights;
    else if(totalPieces > 50) weights = lateWeights;
    
    int positional = 0;
    Turn opp = other(player);
    for(int i = 0; i < 8; i++) {
        for(int j = 0; j < 8; j++) {
            if(board.get(i, j) == player) positional += weights[i][j];
            else if(board.get(i, j) == opp) positional -= weights[i][j];
        }
    }
    
    // Parity
    int parity = (emptySquares % 2 == 0) ? -10 : 10;
    
    // Phase-based evaluation
    int score = 0;
    
    if(totalPieces < 20) {
        // Early: mobility, position, corners
        score = mobility * 20 + 
                positional * 12 + 
                corners * 80 + 
                frontier * 8 +
                stability * 15 +
                edges * 3;
    } 
    else if(totalPieces < 45) {
        // Mid: balanced
        score = pieceDiff * 5 +
                mobility * 15 + 
                positional * 10 + 
                corners * 70 + 
                stability * 20 +
                frontier * 6 +
                edges * 5;
    } 
    else if(emptySquares > 12) {
        // Late-mid: pieces matter more
        score = pieceDiff * 15 +
                mobility * 10 + 
                positional * 6 + 
                corners * 50 + 
                stability * 25 +
                frontier * 3 +
                parity * 8;
    }
    else {
        // Endgame: maximize pieces
        score = pieceDiff * 60 +
                mobility * 8 + 
                corners * 30 +
                stability * 15 +
                parity * 25;
    }
    
    return score;
}

int SuperiorBot::scoreMoveOrdering(const Move& move, const OthelloBoard& board, Turn player, int ply)
{
    int score = 0;
    
    // PV move
    if(hasPvMove && move.x == pvMove.x && move.y == pvMove.y) {
        return 100000;
    }
    
    // Killer moves
    if(ply < 64) {
        if(move.x == killerMoves[ply][0].x && move.y == killerMoves[ply][0].y) {
            score += 50000;
        } else if(move.x == killerMoves[ply][1].x && move.y == killerMoves[ply][1].y) {
            score += 40000;
        }
    }
    
    // History heuristic
    score += historyTable[move.x][move.y];
    
    // Corner moves
    if(isCorner(move.x, move.y)) {
        return score + 90000;
    }
    
    // Avoid X-squares unless corner captured
    if(isXSquare(move.x, move.y) && !cornerCaptured(move.x, move.y, board)) {
        return score - 80000;
    }
    
    // Avoid C-squares unless corner captured
    if(isCSquare(move.x, move.y) && !cornerCaptured(move.x, move.y, board)) {
        return score - 60000;
    }
    
    // Edge preference
    if(isEdge(move.x, move.y)) {
        score += 5000;
    }
    
    return score;
}

vector<Move> SuperiorBot::orderMoves(const list<Move>& moves, const OthelloBoard& board, Turn player, int ply)
{
    vector<pair<int, Move>> scoredMoves;
    
    for(const Move& move : moves) {
        int score = scoreMoveOrdering(move, board, player, ply);
        scoredMoves.push_back({score, move});
    }
    
    sort(scoredMoves.begin(), scoredMoves.end(), greater<pair<int, Move>>());
    
    vector<Move> orderedMoves;
    for(const auto& sm : scoredMoves) {
        orderedMoves.push_back(sm.second);
    }
    
    return orderedMoves;
}

int SuperiorBot::negamax(OthelloBoard& board, int depth, int alpha, int beta, Turn player, int ply)
{
    uint64_t hash = hashBoard(board);
    
    // Transposition table lookup
    auto it = transTable.find(hash);
    if(it != transTable.end() && it->second.depth >= depth) {
        TTEntry& entry = it->second;
        if(entry.alpha >= beta) return entry.alpha;
        if(entry.beta <= alpha) return entry.beta;
        alpha = max(alpha, entry.alpha);
        beta = min(beta, entry.beta);
        if(alpha >= beta) return entry.value;
    }
    
    list<Move> moves = board.getValidMoves(player);
    
    if(moves.empty()) {
        Turn nextPlayer = other(player);
        list<Move> nextMoves = board.getValidMoves(nextPlayer);
        if(nextMoves.empty()) {
            // Game over
            int myCount = (turn == BLACK) ? board.getBlackCount() : board.getRedCount();
            int oppCount = (turn == BLACK) ? board.getRedCount() : board.getBlackCount();
            int diff = myCount - oppCount;
            return (player == turn) ? diff * 100000 : -diff * 100000;
        }
        // Pass
        return -negamax(board, depth, -beta, -alpha, nextPlayer, ply + 1);
    }
    
    if(depth == 0 || timeUp()) {
        int eval = evaluateBoard(board, turn);
        return (player == turn) ? eval : -eval;
    }
    
    vector<Move> orderedMoves = orderMoves(moves, board, player, ply);
    
    int bestValue = -INF;
    Move bestMove = orderedMoves[0];
    int origAlpha = alpha;
    
    for(size_t i = 0; i < orderedMoves.size(); i++) {
        if(timeUp()) break;
        
        OthelloBoard newBoard = board;
        newBoard.makeMove(player, orderedMoves[i]);
        
        int value;
        if(i == 0) {
            value = -negamax(newBoard, depth - 1, -beta, -alpha, other(player), ply + 1);
        } else {
            // Null window search
            value = -negamax(newBoard, depth - 1, -alpha - 1, -alpha, other(player), ply + 1);
            if(value > alpha && value < beta) {
                value = -negamax(newBoard, depth - 1, -beta, -alpha, other(player), ply + 1);
            }
        }
        
        if(value > bestValue) {
            bestValue = value;
            bestMove = orderedMoves[i];
        }
        
        alpha = max(alpha, value);
        
        if(alpha >= beta) {
            // Update killer moves
            if(ply < 64) {
                if(!(killerMoves[ply][0].x == orderedMoves[i].x && killerMoves[ply][0].y == orderedMoves[i].y)) {
                    killerMoves[ply][1] = killerMoves[ply][0];
                    killerMoves[ply][0] = orderedMoves[i];
                }
            }
            // Update history
            historyTable[orderedMoves[i].x][orderedMoves[i].y] += depth * depth;
            break;
        }
    }
    
    // Store in transposition table
    if(!timeUp()) {
        TTEntry entry;
        entry.hash = hash;
        entry.depth = depth;
        entry.value = bestValue;
        entry.alpha = (bestValue <= origAlpha) ? -INF : bestValue;
        entry.beta = (bestValue >= beta) ? INF : bestValue;
        entry.bestMove = bestMove;
        transTable[hash] = entry;
    }
    
    return bestValue;
}

Move SuperiorBot::getBestMove(const OthelloBoard& board)
{
    list<Move> moves = board.getValidMoves(turn);
    
    if(moves.empty()) return Move::pass();
    if(moves.size() == 1) return moves.front();
    
    transTable.clear();
    memset(historyTable, 0, sizeof(historyTable));
    hasPvMove = false;
    
    int emptySquares = 64 - board.getBlackCount() - board.getRedCount();
    Move bestMove = moves.front();
    
    // Endgame perfect search
    if(emptySquares <= 16) {
        int bestValue = -INF;
        vector<Move> orderedMoves = orderMoves(moves, board, turn, 0);
        
        for(const Move& move : orderedMoves) {
            if(timeUp()) break;
            OthelloBoard newBoard = board;
            newBoard.makeMove(turn, move);
            int value = -negamax(newBoard, emptySquares - 1, -INF, INF, other(turn), 1);
            if(value > bestValue) {
                bestValue = value;
                bestMove = move;
            }
        }
        return bestMove;
    }
    
    // Iterative deepening
    int maxDepth = min(20, emptySquares);
    
    for(int depth = 1; depth <= maxDepth && !timeUp(); depth++) {
        int bestValue = -INF;
        Move currentBest = moves.front();
        
        vector<Move> orderedMoves = orderMoves(moves, board, turn, 0);
        
        for(const Move& move : orderedMoves) {
            if(timeUp()) break;
            
            OthelloBoard newBoard = board;
            newBoard.makeMove(turn, move);
            int value = -negamax(newBoard, depth - 1, -INF, INF, other(turn), 1);
            
            if(value > bestValue) {
                bestValue = value;
                currentBest = move;
            }
        }
        
        if(!timeUp()) {
            bestMove = currentBest;
            pvMove = currentBest;
            hasPvMove = true;
        }
    }
    
    return bestMove;
}

Move SuperiorBot::play(const OthelloBoard& board)
{
    startTime = chrono::high_resolution_clock::now();
    timeLimitReached = false;
    return getBestMove(board);
}

extern "C" {
    OthelloPlayer* createBot(Turn turn)
    {
        return new SuperiorBot(turn);
    }
    
    void destroyBot(OthelloPlayer* bot)
    {
        delete bot;
    }
}