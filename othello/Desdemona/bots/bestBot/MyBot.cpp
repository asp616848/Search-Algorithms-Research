/*
* @file MyBot.cpp
* @abhijeet Elite Othello Bot - Advanced Minimax with Enhanced Heuristics
* @date 2025-11-15
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
#include <iostream>
using namespace std;
using namespace Desdemona;

class MyBot: public OthelloPlayer
{
    public:
        MyBot( Turn turn );
        virtual Move play( const OthelloBoard& board );
    
    private:
        static const int BOARD_SIZE = 8;
        static const int INF = 1000000000;
        
        // Position weights
        int positionWeights[8][8];
        int earlyWeights[8][8];
        int lateWeights[8][8];
        
        // Time management
        chrono::time_point<chrono::high_resolution_clock> startTime;
        double timeLimit;
        bool timeLimitReached;
        
        // Transposition table
        struct TTEntry {
            int depth;
            int value;
            int flag; // 0=exact, 1=lowerbound, 2=upperbound
        };
        unordered_map<uint64_t, TTEntry> transTable;
        
        // Killer moves heuristic (store coordinates, -1,-1 for empty)
        int killerMoves[64][2][2]; // [depth][slot][x,y]
        
        void initializeWeights();
        uint64_t hashBoard(const OthelloBoard& board);
        int evaluateBoard(const OthelloBoard& board, Turn player);
        int minimax(OthelloBoard& board, int depth, int alpha, int beta, bool maximizing, int ply);
        Move getBestMove(const OthelloBoard& board);
        bool timeUp();
        
        // Enhanced evaluation functions
        int getMobility(const OthelloBoard& board, Turn player);
        int getPotentialMobility(const OthelloBoard& board, Turn player);
        int getCornersCaptured(const OthelloBoard& board, Turn player);
        int getEdgeStability(const OthelloBoard& board, Turn player);
        int getFrontierDiscs(const OthelloBoard& board, Turn player);
        int getParityScore(const OthelloBoard& board, Turn player);
        int countPieces(const OthelloBoard& board, Turn player);
        
        // Move ordering
        vector<Move> orderMoves(const list<Move>& moves, const OthelloBoard& board, Turn player, int ply);
        int scoreMoveOrdering(const Move& move, const OthelloBoard& board, Turn player, int ply);
        
        // Helper functions
        bool isCorner(int x, int y);
        bool isXSquare(int x, int y);
        bool isCSquare(int x, int y);
        bool isEdge(int x, int y);
        bool adjacentToCorner(int x, int y, const OthelloBoard& board);
};

MyBot::MyBot( Turn turn )
    : OthelloPlayer( turn ), timeLimitReached(false)
{
    initializeWeights();
    timeLimit = 1.98;
    
    // Initialize killer moves with invalid coordinates (-1, -1)
    for(int i = 0; i < 64; i++) {
        killerMoves[i][0][0] = -1;
        killerMoves[i][0][1] = -1;
        killerMoves[i][1][0] = -1;
        killerMoves[i][1][1] = -1;
    }
}

void MyBot::initializeWeights()
{
    if (turn == BLACK) {
        // Use TrainerBot's weights (Aggressive)
        int mid[8][8] = {
            {150, -30,  25,  10,  10,  25, -30, 150},
            {-30, -50,  -5,  -5,  -5,  -5, -50, -30},
            { 25,  -5,  20,   5,   5,  20,  -5,  25},
            { 10,  -5,   5,   5,   5,   5,  -5,  10},
            { 10,  -5,   5,   5,   5,   5,  -5,  10},
            { 25,  -5,  20,   5,   5,  20,  -5,  25},
            {-30, -50,  -5,  -5,  -5,  -5, -50, -30},
            {150, -30,  25,  10,  10,  25, -30, 150}
        };
        
        int early[8][8] = {
            {200, -60,  30,  15,  15,  30, -60, 200},
            {-60, -80, -10, -10, -10, -10, -80, -60},
            { 30, -10,  15,   5,   5,  15, -10,  30},
            { 15, -10,   5,   2,   2,   5, -10,  15},
            { 15, -10,   5,   2,   2,   5, -10,  15},
            { 30, -10,  15,   5,   5,  15, -10,  30},
            {-60, -80, -10, -10, -10, -10, -80, -60},
            {200, -60,  30,  15,  15,  30, -60, 200}
        };
        
        int late[8][8] = {
            {120, -15,  20,  15,  15,  20, -15, 120},
            {-15, -25,  10,  10,  10,  10, -25, -15},
            { 20,  10,  15,  12,  12,  15,  10,  20},
            { 15,  10,  12,  12,  12,  12,  10,  15},
            { 15,  10,  12,  12,  12,  12,  10,  15},
            { 20,  10,  15,  12,  12,  15,  10,  20},
            {-15, -25,  10,  10,  10,  10, -25, -15},
            {120, -15,  20,  15,  15,  20, -15, 120}
        };

        for(int i = 0; i < 8; i++) {
            for(int j = 0; j < 8; j++) {
                positionWeights[i][j] = mid[i][j];
                earlyWeights[i][j] = early[i][j];
                lateWeights[i][j] = late[i][j];
            }
        }
    } else {
        // Use MyBot's original weights (Conservative/Balanced)
        int mid[8][8] = {
            {120, -20,  20,   5,   5,  20, -20, 120},
            {-20, -40,  -5,  -5,  -5,  -5, -40, -20},
            { 20,  -5,  15,   3,   3,  15,  -5,  20},
            {  5,  -5,   3,   3,   3,   3,  -5,   5},
            {  5,  -5,   3,   3,   3,   3,  -5,   5},
            { 20,  -5,  15,   3,   3,  15,  -5,  20},
            {-20, -40,  -5,  -5,  -5,  -5, -40, -20},
            {120, -20,  20,   5,   5,  20, -20, 120}
        };
        
        int early[8][8] = {
            {150, -50,  25,  10,  10,  25, -50, 150},
            {-50, -70,  -8,  -8,  -8,  -8, -70, -50},
            { 25,  -8,  10,   2,   2,  10,  -8,  25},
            { 10,  -8,   2,   1,   1,   2,  -8,  10},
            { 10,  -8,   2,   1,   1,   2,  -8,  10},
            { 25,  -8,  10,   2,   2,  10,  -8,  25},
            {-50, -70,  -8,  -8,  -8,  -8, -70, -50},
            {150, -50,  25,  10,  10,  25, -50, 150}
        };
        
        int late[8][8] = {
            {100, -10,  15,  10,  10,  15, -10, 100},
            {-10, -20,   5,   5,   5,   5, -20, -10},
            { 15,   5,  10,   8,   8,  10,   5,  15},
            { 10,   5,   8,   8,   8,   8,   5,  10},
            { 10,   5,   8,   8,   8,   8,   5,  10},
            { 15,   5,  10,   8,   8,  10,   5,  15},
            {-10, -20,   5,   5,   5,   5, -20, -10},
            {100, -10,  15,  10,  10,  15, -10, 100}
        };

        for(int i = 0; i < 8; i++) {
            for(int j = 0; j < 8; j++) {
                positionWeights[i][j] = mid[i][j];
                earlyWeights[i][j] = early[i][j];
                lateWeights[i][j] = late[i][j];
            }
        }
    }
}

bool MyBot::timeUp()
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

uint64_t MyBot::hashBoard(const OthelloBoard& board)
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

bool MyBot::isCorner(int x, int y) {
    return (x == 0 || x == 7) && (y == 0 || y == 7);
}

bool MyBot::isXSquare(int x, int y) {
    return ((x == 1 || x == 6) && (y == 1 || y == 6));
}

bool MyBot::isCSquare(int x, int y) {
    return ((x == 0 || x == 7) && (y == 1 || y == 6)) ||
           ((x == 1 || x == 6) && (y == 0 || y == 7));
}

bool MyBot::isEdge(int x, int y) {
    return (x == 0 || x == 7 || y == 0 || y == 7) && !isCorner(x, y);
}

bool MyBot::adjacentToCorner(int x, int y, const OthelloBoard& board) {
    if(isCorner(x, y)) return false;
    
    // Check if this is an X or C square and if adjacent corner is occupied
    if(x <= 1 && y <= 1) {
        return board.get(0, 0) != EMPTY;
    }
    if(x <= 1 && y >= 6) {
        return board.get(0, 7) != EMPTY;
    }
    if(x >= 6 && y <= 1) {
        return board.get(7, 0) != EMPTY;
    }
    if(x >= 6 && y >= 6) {
        return board.get(7, 7) != EMPTY;
    }
    return false;
}

int MyBot::countPieces(const OthelloBoard& board, Turn player)
{
    return (player == BLACK) ? board.getBlackCount() : board.getRedCount();
}

int MyBot::getMobility(const OthelloBoard& board, Turn player)
{
    return board.getValidMoves(player).size();
}

int MyBot::getPotentialMobility(const OthelloBoard& board, Turn player)
{
    // Count empty squares adjacent to opponent pieces
    Turn opponent = other(player);
    int potential = 0;
    int dx[] = {-1, -1, -1, 0, 0, 1, 1, 1};
    int dy[] = {-1, 0, 1, -1, 1, -1, 0, 1};
    
    for(int i = 0; i < 8; i++) {
        for(int j = 0; j < 8; j++) {
            if(board.get(i, j) == opponent) {
                for(int k = 0; k < 8; k++) {
                    int ni = i + dx[k];
                    int nj = j + dy[k];
                    if(ni >= 0 && ni < 8 && nj >= 0 && nj < 8 && board.get(ni, nj) == EMPTY) {
                        potential++;
                    }
                }
            }
        }
    }
    return potential;
}

int MyBot::getCornersCaptured(const OthelloBoard& board, Turn player)
{
    int corners = 0;
    if(board.get(0, 0) == player) corners++;
    if(board.get(0, 7) == player) corners++;
    if(board.get(7, 0) == player) corners++;
    if(board.get(7, 7) == player) corners++;
    return corners;
}

int MyBot::getFrontierDiscs(const OthelloBoard& board, Turn player)
{
    // Frontier discs are pieces adjacent to empty squares (less stable)
    int frontier = 0;
    int dx[] = {-1, -1, -1, 0, 0, 1, 1, 1};
    int dy[] = {-1, 0, 1, -1, 1, -1, 0, 1};
    
    for(int i = 0; i < 8; i++) {
        for(int j = 0; j < 8; j++) {
            if(board.get(i, j) == player) {
                for(int k = 0; k < 8; k++) {
                    int ni = i + dx[k];
                    int nj = j + dy[k];
                    if(ni >= 0 && ni < 8 && nj >= 0 && nj < 8 && board.get(ni, nj) == EMPTY) {
                        frontier++;
                        break;
                    }
                }
            }
        }
    }
    return frontier;
}

int MyBot::getEdgeStability(const OthelloBoard& board, Turn player)
{
    int stability = 0;
    
    // Corners are maximally stable
    stability += getCornersCaptured(board, player) * 50;
    
    // Check edge stability based on corner ownership
    Turn opponent = other(player);
    
    // Top edge
    if(board.get(0, 0) == player) {
        for(int j = 1; j < 7; j++) {
            if(board.get(0, j) == player) stability += 8;
            else if(board.get(0, j) == opponent) break;
        }
    }
    if(board.get(0, 7) == player) {
        for(int j = 6; j > 0; j--) {
            if(board.get(0, j) == player) stability += 8;
            else if(board.get(0, j) == opponent) break;
        }
    }
    
    // Bottom edge
    if(board.get(7, 0) == player) {
        for(int j = 1; j < 7; j++) {
            if(board.get(7, j) == player) stability += 8;
            else if(board.get(7, j) == opponent) break;
        }
    }
    if(board.get(7, 7) == player) {
        for(int j = 6; j > 0; j--) {
            if(board.get(7, j) == player) stability += 8;
            else if(board.get(7, j) == opponent) break;
        }
    }
    
    // Left edge
    if(board.get(0, 0) == player) {
        for(int i = 1; i < 7; i++) {
            if(board.get(i, 0) == player) stability += 8;
            else if(board.get(i, 0) == opponent) break;
        }
    }
    if(board.get(7, 0) == player) {
        for(int i = 6; i > 0; i--) {
            if(board.get(i, 0) == player) stability += 8;
            else if(board.get(i, 0) == opponent) break;
        }
    }
    
    // Right edge
    if(board.get(0, 7) == player) {
        for(int i = 1; i < 7; i++) {
            if(board.get(i, 7) == player) stability += 8;
            else if(board.get(i, 7) == opponent) break;
        }
    }
    if(board.get(7, 7) == player) {
        for(int i = 6; i > 0; i--) {
            if(board.get(i, 7) == player) stability += 8;
            else if(board.get(i, 7) == opponent) break;
        }
    }
    
    return stability;
}

int MyBot::getParityScore(const OthelloBoard& board, Turn player)
{
    int emptySquares = 64 - board.getBlackCount() - board.getRedCount();
    // In endgame with odd empty squares, having the last move is valuable
    return (emptySquares % 2 == 1) ? 1 : -1;
}

int MyBot::evaluateBoard(const OthelloBoard& board, Turn player)
{
    Turn opponent = other(player);
    
    int myPieces = countPieces(board, player);
    int oppPieces = countPieces(board, opponent);
    int totalPieces = myPieces + oppPieces;
    int emptySquares = 64 - totalPieces;
    
    // Coin parity
    int coinParity = 0;
    if(totalPieces > 0) {
        coinParity = 100 * (myPieces - oppPieces) / totalPieces;
    }
    
    // Mobility
    int myMobility = getMobility(board, player);
    int oppMobility = getMobility(board, opponent);
    int mobility = 0;
    if(myMobility + oppMobility > 0) {
        mobility = 100 * (myMobility - oppMobility) / (myMobility + oppMobility);
    }
    
    // Potential mobility
    int myPotential = getPotentialMobility(board, player);
    int oppPotential = getPotentialMobility(board, opponent);
    int potentialMobility = myPotential - oppPotential;
    
    // Corners
    int myCorners = getCornersCaptured(board, player);
    int oppCorners = getCornersCaptured(board, opponent);
    int cornerScore = 25 * (myCorners - oppCorners);
    
    // Edge stability
    int myStability = getEdgeStability(board, player);
    int oppStability = getEdgeStability(board, opponent);
    int stabilityScore = myStability - oppStability;
    
    // Frontier discs (fewer is better in early/mid game)
    int myFrontier = getFrontierDiscs(board, player);
    int oppFrontier = getFrontierDiscs(board, opponent);
    int frontierScore = oppFrontier - myFrontier;
    
    // Positional score with phase-appropriate weights
    int (*weights)[8] = positionWeights;
    if(totalPieces < 20) {
        weights = earlyWeights;
    } else if(totalPieces > 52) {
        weights = lateWeights;
    }
    
    int positionalScore = 0;
    for(int i = 0; i < 8; i++) {
        for(int j = 0; j < 8; j++) {
            if(board.get(i, j) == player) {
                positionalScore += weights[i][j];
            } else if(board.get(i, j) == opponent) {
                positionalScore -= weights[i][j];
            }
        }
    }
    
    // Parity (last move advantage)
    int parity = getParityScore(board, player);
    
    // Phase-based weighting
    int score = 0;
    
    if(totalPieces < 20) {
        // Early game: mobility, position, avoid X/C squares
        score = mobility * 15 + 
                potentialMobility * 3 +
                positionalScore * 10 + 
                cornerScore * 60 + 
                stabilityScore * 2 +
                frontierScore * 5;
    } 
    else if(totalPieces < 45) {
        // Mid game: balanced
        score = coinParity * 3 +
                mobility * 12 + 
                potentialMobility * 2 +
                positionalScore * 8 + 
                cornerScore * 50 + 
                stabilityScore * 4 +
                frontierScore * 4;
    } 
    else if(emptySquares > 10) {
        // Late-mid game: coin count matters more
        score = coinParity * 10 +
                mobility * 8 + 
                potentialMobility * 1 +
                positionalScore * 5 + 
                cornerScore * 40 + 
                stabilityScore * 3 +
                frontierScore * 2 +
                parity * 5;
    }
    else {
        // Endgame: maximize pieces, parity matters
        score = coinParity * 50 +
                mobility * 5 + 
                positionalScore * 2 + 
                cornerScore * 25 +
                parity * 20;
    }
    
    return score;
}

int MyBot::scoreMoveOrdering(const Move& move, const OthelloBoard& board, Turn player, int ply)
{
    int score = 0;
    
    // Killer move bonus
    if(ply < 64) {
        if(move.x == killerMoves[ply][0][0] && move.y == killerMoves[ply][0][1]) {
            score += 9000;
        } else if(move.x == killerMoves[ply][1][0] && move.y == killerMoves[ply][1][1]) {
            score += 8000;
        }
    }
    
    // Corner moves are best
    if(isCorner(move.x, move.y)) {
        return score + 10000;
    }
    
    // Avoid X-squares unless corner is already captured
    if(isXSquare(move.x, move.y) && !adjacentToCorner(move.x, move.y, board)) {
        return score - 5000;
    }
    
    // Avoid C-squares unless corner is captured
    if(isCSquare(move.x, move.y) && !adjacentToCorner(move.x, move.y, board)) {
        return score - 3000;
    }
    
    // Edges are good
    if(isEdge(move.x, move.y)) {
        score += 500;
    }
    
    // Positional weight
    score += positionWeights[move.x][move.y];
    
    return score;
}

vector<Move> MyBot::orderMoves(const list<Move>& moves, const OthelloBoard& board, Turn player, int ply)
{
    vector<pair<int, Move>> scoredMoves;
    
    for(const Move& move : moves) {
        int score = scoreMoveOrdering(move, board, player, ply);
        scoredMoves.push_back({score, move});
    }
    
    sort(scoredMoves.begin(), scoredMoves.end(), 
         [](const pair<int, Move>& a, const pair<int, Move>& b) {
             return a.first > b.first;
         });
    
    vector<Move> orderedMoves;
    for(const auto& sm : scoredMoves) {
        orderedMoves.push_back(sm.second);
    }
    
    return orderedMoves;
}

int MyBot::minimax(OthelloBoard& board, int depth, int alpha, int beta, bool maximizing, int ply)
{
    if(depth == 0 || timeUp()) {
        return evaluateBoard(board, turn);
    }
    
    // Check transposition table
    uint64_t hash = hashBoard(board);
    auto it = transTable.find(hash);
    if(it != transTable.end() && it->second.depth >= depth) {
        if(it->second.flag == 0) return it->second.value;
        if(it->second.flag == 1) alpha = max(alpha, it->second.value);
        if(it->second.flag == 2) beta = min(beta, it->second.value);
        if(alpha >= beta) return it->second.value;
    }
    
    Turn currentPlayer = maximizing ? turn : other(turn);
    list<Move> moves = board.getValidMoves(currentPlayer);
    
    if(moves.empty()) {
        Turn nextPlayer = other(currentPlayer);
        list<Move> nextMoves = board.getValidMoves(nextPlayer);
        if(nextMoves.empty()) {
            return evaluateBoard(board, turn);
        }
        return minimax(board, depth - 1, alpha, beta, !maximizing, ply + 1);
    }
    
    vector<Move> orderedMoves = orderMoves(moves, board, currentPlayer, ply);
    
    int bestValue;
    int flag;
    
    if(maximizing) {
        bestValue = -INF;
        Move bestMove = orderedMoves[0];
        
        for(const Move& move : orderedMoves) {
            OthelloBoard newBoard = board;
            newBoard.makeMove(currentPlayer, move);
            int eval = minimax(newBoard, depth - 1, alpha, beta, false, ply + 1);
            
            if(eval > bestValue) {
                bestValue = eval;
                bestMove = move;
            }
            
            alpha = max(alpha, eval);
            if(beta <= alpha) {
                // Store killer move
                if(ply < 64 && !isCorner(move.x, move.y)) {
                    killerMoves[ply][1][0] = killerMoves[ply][0][0];
                    killerMoves[ply][1][1] = killerMoves[ply][0][1];
                    killerMoves[ply][0][0] = move.x;
                    killerMoves[ply][0][1] = move.y;
                }
                break;
            }
            if(timeUp()) break;
        }
        
        flag = (bestValue <= alpha) ? 2 : ((bestValue >= beta) ? 1 : 0);
    } else {
        bestValue = INF;
        
        for(const Move& move : orderedMoves) {
            OthelloBoard newBoard = board;
            newBoard.makeMove(currentPlayer, move);
            int eval = minimax(newBoard, depth - 1, alpha, beta, true, ply + 1);
            
            bestValue = min(bestValue, eval);
            beta = min(beta, eval);
            
            if(beta <= alpha) {
                if(ply < 64 && !isCorner(move.x, move.y)) {
                    killerMoves[ply][1][0] = killerMoves[ply][0][0];
                    killerMoves[ply][1][1] = killerMoves[ply][0][1];
                    killerMoves[ply][0][0] = move.x;
                    killerMoves[ply][0][1] = move.y;
                }
                break;
            }
            if(timeUp()) break;
        }
        
        flag = (bestValue <= alpha) ? 2 : ((bestValue >= beta) ? 1 : 0);
    }
    
    // Store in transposition table
    transTable[hash] = {depth, bestValue, flag};
    
    return bestValue;
}

Move MyBot::getBestMove(const OthelloBoard& board)
{
    list<Move> moves = board.getValidMoves(turn);
    
    if(moves.empty()) {
        return Move::pass();
    }
    
    if(moves.size() == 1) {
        return moves.front();
    }
    
    transTable.clear();
    
    Move bestMove = moves.front();
    
    // Iterative deepening with aspiration windows
    for(int depth = 1; depth <= 20 && !timeUp(); depth++) {
        Move currentBest = moves.front();
        int bestValue = -INF;
        
        vector<Move> orderedMoves = orderMoves(moves, board, turn, 0);
        
        for(const Move& move : orderedMoves) {
            if(timeUp()) break;
            
            OthelloBoard newBoard = board;
            newBoard.makeMove(turn, move);
            
            int value = minimax(newBoard, depth - 1, -INF, INF, false, 1);
            
            if(value > bestValue) {
                bestValue = value;
                currentBest = move;
            }
        }
        
        if(!timeUp()) {
            bestMove = currentBest;
        } else {
            break;
        }
    }
    
    return bestMove;
}

Move MyBot::play( const OthelloBoard& board )
{
    startTime = chrono::high_resolution_clock::now();
    timeLimitReached = false;
    return getBestMove(board);
}

extern "C" {
    OthelloPlayer* createBot( Turn turn )
    {
        return new MyBot( turn );
    }

    void destroyBot( OthelloPlayer* bot )
    {
        delete bot;
    }
}