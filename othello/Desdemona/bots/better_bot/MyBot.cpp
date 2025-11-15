/*
* @file MyBot.cpp
* @author Competitive Othello Bot using Minimax with Alpha-Beta Pruning
* @date 2025-11-03
* Advanced Othello bot with evaluation heuristics and iterative deepening
*/

#include "Othello.h"
#include "OthelloBoard.h"
#include "OthelloPlayer.h"
#include <cstdlib>
#include <algorithm>
#include <limits>
#include <chrono>
#include <vector>
#include <iostream>
using namespace std;
using namespace Desdemona;

class MyBot: public OthelloPlayer
{
    public:
        /**
         * Initialisation routines here
         * This could do anything from open up a cache of "best moves" to
         * spawning a background processing thread. 
         */
        MyBot( Turn turn );

        /**
         * Play something 
         */
        virtual Move play( const OthelloBoard& board );
    
    private:
        // Position weight matrix for strategic evaluation
        static const int BOARD_SIZE = 8;
        int positionWeights[8][8];
        
        // Time management
        chrono::time_point<chrono::high_resolution_clock> startTime;
        double timeLimit;
        
        // Helper functions
        void initializeWeights();
        int evaluateBoard(const OthelloBoard& board, Turn player);
        int minimax(OthelloBoard& board, int depth, int alpha, int beta, bool maximizing);
        Move getBestMove(const OthelloBoard& board);
        bool timeUp();
        int getMobility(const OthelloBoard& board, Turn player);
        int getCornersCaptured(const OthelloBoard& board, Turn player);
        int getStability(const OthelloBoard& board, Turn player);
        int countPieces(const OthelloBoard& board, Turn player);
        vector<Move> orderMoves(const list<Move>& moves, const OthelloBoard& board, Turn player);
};

MyBot::MyBot( Turn turn )
    : OthelloPlayer( turn )
{
    initializeWeights();
    timeLimit = 1.95; // 1.95 seconds to be safe under 2 second limit
}

void MyBot::initializeWeights()
{
    // Strategic position weights for Othello
    // Corners are most valuable, X-squares are dangerous, edges are good
    int weights[8][8] = {
        {100, -20,  10,   5,   5,  10, -20, 100},
        {-20, -50,  -2,  -2,  -2,  -2, -50, -20},
        { 10,  -2,   5,   1,   1,   5,  -2,  10},
        {  5,  -2,   1,   1,   1,   1,  -2,   5},
        {  5,  -2,   1,   1,   1,   1,  -2,   5},
        { 10,  -2,   5,   1,   1,   5,  -2,  10},
        {-20, -50,  -2,  -2,  -2,  -2, -50, -20},
        {100, -20,  10,   5,   5,  10, -20, 100}
    };
    
    for(int i = 0; i < 8; i++) {
        for(int j = 0; j < 8; j++) {
            positionWeights[i][j] = weights[i][j];
        }
    }
}

bool MyBot::timeUp()
{
    auto currentTime = chrono::high_resolution_clock::now();
    chrono::duration<double> elapsed = currentTime - startTime;
    return elapsed.count() > timeLimit;
}

int MyBot::countPieces(const OthelloBoard& board, Turn player)
{
    if(player == BLACK) {
        return board.getBlackCount();
    } else {
        return board.getRedCount();
    }
}

int MyBot::getMobility(const OthelloBoard& board, Turn player)
{
    return board.getValidMoves(player).size();
}

int MyBot::getCornersCaptured(const OthelloBoard& board, Turn player)
{
    int corners = 0;
    int cornerPositions[4][2] = {{0,0}, {0,7}, {7,0}, {7,7}};
    
    for(int i = 0; i < 4; i++) {
        int x = cornerPositions[i][0];
        int y = cornerPositions[i][1];
        if(board.get(x, y) == player) {
            corners++;
        }
    }
    return corners;
}

int MyBot::getStability(const OthelloBoard& board, Turn player)
{
    // Simplified stability - count pieces on edges and corners
    int stability = 0;
    
    // Corners are extremely stable
    stability += getCornersCaptured(board, player) * 25;
    
    // Edges are somewhat stable
    for(int i = 0; i < 8; i++) {
        if(board.get(0, i) == player) stability += 5;
        if(board.get(7, i) == player) stability += 5;
        if(board.get(i, 0) == player) stability += 5;
        if(board.get(i, 7) == player) stability += 5;
    }
    
    return stability;
}

int MyBot::evaluateBoard(const OthelloBoard& board, Turn player)
{
    Turn opponent = other(player);
    
    // Coin parity (piece difference)
    int myPieces = countPieces(board, player);
    int oppPieces = countPieces(board, opponent);
    int coinParity = 0;
    if(myPieces + oppPieces != 0) {
        coinParity = 100 * (myPieces - oppPieces) / (myPieces + oppPieces);
    }
    
    // Mobility (number of possible moves)
    int myMobility = getMobility(board, player);
    int oppMobility = getMobility(board, opponent);
    int mobility = 0;
    if(myMobility + oppMobility != 0) {
        mobility = 100 * (myMobility - oppMobility) / (myMobility + oppMobility);
    }
    
    // Corner occupancy
    int myCorners = getCornersCaptured(board, player);
    int oppCorners = getCornersCaptured(board, opponent);
    int cornerScore = 0;
    if(myCorners + oppCorners != 0) {
        cornerScore = 100 * (myCorners - oppCorners) / (myCorners + oppCorners);
    }
    
    // Stability
    int myStability = getStability(board, player);
    int oppStability = getStability(board, opponent);
    int stabilityScore = myStability - oppStability;
    
    // Positional weight score
    int positionalScore = 0;
    for(int i = 0; i < 8; i++) {
        for(int j = 0; j < 8; j++) {
            if(board.get(i, j) == player) {
                positionalScore += positionWeights[i][j];
            } else if(board.get(i, j) == opponent) {
                positionalScore -= positionWeights[i][j];
            }
        }
    }
    
    // Determine game phase
    int totalPieces = myPieces + oppPieces;
    
    // Weights change based on game phase
    if(totalPieces < 20) {
        // Early game: focus on mobility and position, but don't ignore coins completely
        return 2 * coinParity + 10 * mobility + 5 * positionalScore + 50 * cornerScore + 2 * stabilityScore;
    } else if(totalPieces < 50) {
        // Mid game: balance everything
        return 5 * coinParity + 8 * mobility + 8 * positionalScore + 40 * cornerScore + 3 * stabilityScore;
    } else {
        // End game: maximize pieces
        return 20 * coinParity + 3 * mobility + 3 * positionalScore + 30 * cornerScore + 2 * stabilityScore;
    }
}

vector<Move> MyBot::orderMoves(const list<Move>& moves, const OthelloBoard& board, Turn player)
{
    vector<Move> orderedMoves;
    vector<pair<int, Move>> scoredMoves;
    
    for(const Move& move : moves) {
        int score = 0;
        
        // Prioritize corners
        if((move.x == 0 || move.x == 7) && (move.y == 0 || move.y == 7)) {
            score += 10000;
        }
        // Then edges
        else if(move.x == 0 || move.x == 7 || move.y == 0 || move.y == 7) {
            score += 100;
        }
        
        // Add position weight
        score += positionWeights[move.x][move.y];
        
        scoredMoves.push_back({score, move});
    }
    
    // Sort by score descending
    sort(scoredMoves.begin(), scoredMoves.end(), 
         [](const pair<int, Move>& a, const pair<int, Move>& b) {
             return a.first > b.first;
         });
    
    for(const auto& sm : scoredMoves) {
        orderedMoves.push_back(sm.second);
    }
    
    return orderedMoves;
}

int MyBot::minimax(OthelloBoard& board, int depth, int alpha, int beta, bool maximizing)
{
    if(depth == 0 || timeUp()) {
        return evaluateBoard(board, turn);
    }
    
    Turn myTurn = turn;  // Copy to avoid reference issues
    Turn oppTurn = other(myTurn);
    Turn currentPlayer = maximizing ? myTurn : oppTurn;
    list<Move> moves = board.getValidMoves(currentPlayer);
    
    if(moves.empty()) {
        // No valid moves, pass turn
        Turn nextPlayer = maximizing ? oppTurn : myTurn;
        list<Move> nextMoves = board.getValidMoves(nextPlayer);
        if(nextMoves.empty()) {
            // Game over, evaluate final position
            return evaluateBoard(board, turn);
        }
        // Opponent gets to play
        return minimax(board, depth - 1, alpha, beta, !maximizing);
    }
    
    // Order moves for better pruning
    vector<Move> orderedMoves = orderMoves(moves, board, currentPlayer);
    
    if(maximizing) {
        int maxEval = numeric_limits<int>::min();
        for(const Move& move : orderedMoves) {
            OthelloBoard newBoard = board;
            newBoard.makeMove(currentPlayer, move);
            int eval = minimax(newBoard, depth - 1, alpha, beta, false);
            maxEval = max(maxEval, eval);
            alpha = max(alpha, eval);
            if(beta <= alpha) {
                break; // Beta cutoff
            }
            if(timeUp()) break;
        }
        return maxEval;
    } else {
        int minEval = numeric_limits<int>::max();
        for(const Move& move : orderedMoves) {
            OthelloBoard newBoard = board;
            newBoard.makeMove(currentPlayer, move);
            int eval = minimax(newBoard, depth - 1, alpha, beta, true);
            minEval = min(minEval, eval);
            beta = min(beta, eval);
            if(beta <= alpha) {
                break; // Alpha cutoff
            }
            if(timeUp()) break;
        }
        return minEval;
    }
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
    
    // Iterative deepening
    Move bestMove = moves.front();
    int maxDepth = 1;
    
    // Try increasing depths until time runs out
    for(int depth = 1; depth <= 10 && !timeUp(); depth++) {
        Move currentBest = moves.front();
        int bestValue = numeric_limits<int>::min();
        
        vector<Move> orderedMoves = orderMoves(moves, board, turn);
        
        for(const Move& move : orderedMoves) {
            if(timeUp()) break;
            
            OthelloBoard newBoard = board;
            newBoard.makeMove(turn, move);
            
            int value = minimax(newBoard, depth - 1, 
                              numeric_limits<int>::min(), 
                              numeric_limits<int>::max(), 
                              false);
            
            if(value > bestValue) {
                bestValue = value;
                currentBest = move;
            }
        }
        
        if(!timeUp()) {
            bestMove = currentBest;
            maxDepth = depth;
        }
    }
    
    return bestMove;
}

Move MyBot::play( const OthelloBoard& board )
{
    startTime = chrono::high_resolution_clock::now();
    return getBestMove(board);
}

// The following lines are _very_ important to create a bot module for Desdemona

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


