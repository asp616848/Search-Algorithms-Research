/*
 * MyBot.cpp - Elite Othello Bot
 * Advanced AI with Negamax, PVS, Transposition Tables, and comprehensive evaluation
 */

#include "Othello.h"
#include "OthelloBoard.h"
#include "OthelloPlayer.h"
#include <cstdlib>
#include <algorithm>
#include <chrono>
#include <vector>
#include <cstring>
#include <random>
using namespace std;
using namespace Desdemona;

class MyBot: public OthelloPlayer
{
public:
    MyBot(Turn turn);
    ~MyBot();
    virtual Move play(const OthelloBoard& board);

private:
    static const int INF = 100000000;
    static const int WIN_SCORE = 10000000;
    static const int TT_SIZE = (1 << 20);

    struct TTEntry {
        uint64_t hash;
        int depth;
        int value;
        int flag;
        int bestX, bestY;
    };

    TTEntry* transTable;
    uint64_t zobristTable[8][8][3];
    uint64_t zobristBlackTurn;

    int weights[3][8][8];
    int historyTable[2][8][8];
    int killerX[64][2];
    int killerY[64][2];

    chrono::time_point<chrono::high_resolution_clock> startTime;
    double timeLimit;
    bool timeUp;
    int nodesSearched;

    int pvMoveX, pvMoveY;
    bool hasPvMove;

    void initZobrist();
    void initWeights();

    uint64_t computeHash(const OthelloBoard& board, Turn player);
    int negamax(OthelloBoard& board, int depth, int alpha, int beta, Turn player, int ply);
    Move iterativeDeepening(const OthelloBoard& board);

    int evaluate(const OthelloBoard& board, Turn player);
    int evalMobility(const OthelloBoard& board, Turn player);
    int evalCorners(const OthelloBoard& board, Turn player);
    int evalStability(const OthelloBoard& board, Turn player);
    int evalPositional(const OthelloBoard& board, Turn player, int phase);
    int evalFrontier(const OthelloBoard& board, Turn player);

    void sortMoves(vector<Move>& moves, const OthelloBoard& board, Turn player, int ply, int ttX, int ttY);
    int scoreMove(const Move& m, const OthelloBoard& board, Turn player, int ply, int ttX, int ttY);

    bool isTimeUp();
    bool isCorner(int x, int y) { return (x == 0 || x == 7) && (y == 0 || y == 7); }
    bool isXSquare(int x, int y) { return (x == 1 || x == 6) && (y == 1 || y == 6); }
    bool isCSquare(int x, int y) { return ((x == 0 || x == 7) && (y == 1 || y == 6)) || ((x == 1 || x == 6) && (y == 0 || y == 7)); }
    int countDiscs(const OthelloBoard& board, Turn player);
};

MyBot::MyBot(Turn turn) : OthelloPlayer(turn), timeUp(false), hasPvMove(false), pvMoveX(-1), pvMoveY(-1)
{
    transTable = new TTEntry[TT_SIZE];
    memset(transTable, 0, sizeof(TTEntry) * TT_SIZE);
    memset(historyTable, 0, sizeof(historyTable));
    memset(killerX, -1, sizeof(killerX));
    memset(killerY, -1, sizeof(killerY));

    initZobrist();
    initWeights();
    timeLimit = 1.98;
    nodesSearched = 0;
}

MyBot::~MyBot()
{
    delete[] transTable;
}

void MyBot::initZobrist()
{
    mt19937_64 rng(12345);
    for (int i = 0; i < 8; i++) {
        for (int j = 0; j < 8; j++) {
            for (int k = 0; k < 3; k++) {
                zobristTable[i][j][k] = rng();
            }
        }
    }
    zobristBlackTurn = rng();
}

void MyBot::initWeights()
{
    int early[8][8] = {
        {500, -150,  30,  10,  10,  30, -150, 500},
        {-150, -250,  -5,  -5,  -5,  -5, -250, -150},
        { 30,  -5,   1,   1,   1,   1,  -5,  30},
        { 10,  -5,   1,   1,   1,   1,  -5,  10},
        { 10,  -5,   1,   1,   1,   1,  -5,  10},
        { 30,  -5,   1,   1,   1,   1,  -5,  30},
        {-150, -250,  -5,  -5,  -5,  -5, -250, -150},
        {500, -150,  30,  10,  10,  30, -150, 500}
    };

    int mid[8][8] = {
        {200, -80,  20,   5,   5,  20, -80, 200},
        {-80, -100,  -5,  -5,  -5,  -5, -100, -80},
        { 20,  -5,  15,   3,   3,  15,  -5,  20},
        {  5,  -5,   3,   3,   3,   3,  -5,   5},
        {  5,  -5,   3,   3,   3,   3,  -5,   5},
        { 20,  -5,  15,   3,   3,  15,  -5,  20},
        {-80, -100,  -5,  -5,  -5,  -5, -100, -80},
        {200, -80,  20,   5,   5,  20, -80, 200}
    };

    int late[8][8] = {
        {100, -20,  10,   5,   5,  10, -20, 100},
        {-20, -30,   5,   5,   5,   5, -30, -20},
        { 10,   5,   5,   5,   5,   5,   5,  10},
        {  5,   5,   5,   5,   5,   5,   5,   5},
        {  5,   5,   5,   5,   5,   5,   5,   5},
        { 10,   5,   5,   5,   5,   5,   5,  10},
        {-20, -30,   5,   5,   5,   5, -30, -20},
        {100, -20,  10,   5,   5,  10, -20, 100}
    };

    for (int i = 0; i < 8; i++) {
        for (int j = 0; j < 8; j++) {
            weights[0][i][j] = early[i][j];
            weights[1][i][j] = mid[i][j];
            weights[2][i][j] = late[i][j];
        }
    }
}

uint64_t MyBot::computeHash(const OthelloBoard& board, Turn player)
{
    uint64_t hash = 0;
    for (int i = 0; i < 8; i++) {
        for (int j = 0; j < 8; j++) {
            Turn c = board.get(i, j);
            if (c == BLACK) hash ^= zobristTable[i][j][0];
            else if (c == RED) hash ^= zobristTable[i][j][1];
        }
    }
    if (player == BLACK) hash ^= zobristBlackTurn;
    return hash;
}

bool MyBot::isTimeUp()
{
    if (timeUp) return true;
    if ((nodesSearched & 511) == 0) {
        auto now = chrono::high_resolution_clock::now();
        chrono::duration<double> elapsed = now - startTime;
        if (elapsed.count() > timeLimit) {
            timeUp = true;
            return true;
        }
    }
    return false;
}

int MyBot::countDiscs(const OthelloBoard& board, Turn player)
{
    return (player == BLACK) ? board.getBlackCount() : board.getRedCount();
}

int MyBot::evalMobility(const OthelloBoard& board, Turn player)
{
    int myMoves = board.getValidMoves(player).size();
    int oppMoves = board.getValidMoves(other(player)).size();
    if (myMoves + oppMoves == 0) return 0;
    return 100 * (myMoves - oppMoves) / (myMoves + oppMoves + 1);
}

int MyBot::evalCorners(const OthelloBoard& board, Turn player)
{
    int myCorners = 0, oppCorners = 0;
    Turn opp = other(player);
    int cx[4] = {0, 0, 7, 7};
    int cy[4] = {0, 7, 0, 7};

    for (int i = 0; i < 4; i++) {
        Turn c = board.get(cx[i], cy[i]);
        if (c == player) myCorners++;
        else if (c == opp) oppCorners++;
    }
    return 25 * (myCorners - oppCorners);
}

int MyBot::evalStability(const OthelloBoard& board, Turn player)
{
    int stability = 0;
    Turn opp = other(player);

    int cx[4] = {0, 0, 7, 7};
    int cy[4] = {0, 7, 0, 7};
    int dx[4] = {1, 1, -1, -1};
    int dy[4] = {1, -1, 1, -1};

    for (int c = 0; c < 4; c++) {
        Turn owner = board.get(cx[c], cy[c]);
        if (owner == player) {
            stability += 30;
            for (int j = cy[c] + dy[c]; j >= 0 && j < 8; j += dy[c]) {
                if (board.get(cx[c], j) == player) stability += 5;
                else break;
            }
            for (int i = cx[c] + dx[c]; i >= 0 && i < 8; i += dx[c]) {
                if (board.get(i, cy[c]) == player) stability += 5;
                else break;
            }
        } else if (owner == opp) {
            stability -= 30;
            for (int j = cy[c] + dy[c]; j >= 0 && j < 8; j += dy[c]) {
                if (board.get(cx[c], j) == opp) stability -= 5;
                else break;
            }
            for (int i = cx[c] + dx[c]; i >= 0 && i < 8; i += dx[c]) {
                if (board.get(i, cy[c]) == opp) stability -= 5;
                else break;
            }
        }
    }
    return stability;
}

int MyBot::evalPositional(const OthelloBoard& board, Turn player, int phase)
{
    int score = 0;
    Turn opp = other(player);

    for (int i = 0; i < 8; i++) {
        for (int j = 0; j < 8; j++) {
            Turn c = board.get(i, j);
            if (c == player) score += weights[phase][i][j];
            else if (c == opp) score -= weights[phase][i][j];
        }
    }

    int xsq[4][2] = {{1,1}, {1,6}, {6,1}, {6,6}};
    int xcorner[4][2] = {{0,0}, {0,7}, {7,0}, {7,7}};

    for (int i = 0; i < 4; i++) {
        Turn cornerOwner = board.get(xcorner[i][0], xcorner[i][1]);
        if (cornerOwner != EMPTY) {
            Turn xOwner = board.get(xsq[i][0], xsq[i][1]);
            if (xOwner == cornerOwner) {
                if (xOwner == player) score += 50;
                else score -= 50;
            }
        }
    }
    return score;
}

int MyBot::evalFrontier(const OthelloBoard& board, Turn player)
{
    int myFrontier = 0, oppFrontier = 0;
    Turn opp = other(player);
    int dx[] = {-1, -1, -1, 0, 0, 1, 1, 1};
    int dy[] = {-1, 0, 1, -1, 1, -1, 0, 1};

    for (int i = 0; i < 8; i++) {
        for (int j = 0; j < 8; j++) {
            Turn c = board.get(i, j);
            if (c == EMPTY) continue;

            for (int k = 0; k < 8; k++) {
                int ni = i + dx[k], nj = j + dy[k];
                if (ni >= 0 && ni < 8 && nj >= 0 && nj < 8 && board.get(ni, nj) == EMPTY) {
                    if (c == player) myFrontier++;
                    else oppFrontier++;
                    break;
                }
            }
        }
    }

    if (myFrontier + oppFrontier == 0) return 0;
    return -10 * (myFrontier - oppFrontier) / (myFrontier + oppFrontier + 1);
}

int MyBot::evaluate(const OthelloBoard& board, Turn player)
{
    int total = board.getBlackCount() + board.getRedCount();
    int empty = 64 - total;

    int phase = (total < 20) ? 0 : ((total < 50) ? 1 : 2);

    int myDiscs = countDiscs(board, player);
    int oppDiscs = countDiscs(board, other(player));
    int discDiff = (total > 0) ? (100 * (myDiscs - oppDiscs) / total) : 0;

    int mobility = evalMobility(board, player);
    int corners = evalCorners(board, player);
    int stability = evalStability(board, player);
    int positional = evalPositional(board, player, phase);
    int frontier = evalFrontier(board, player);
    int parity = (empty % 2 == 1) ? 3 : -3;

    int score = 0;
    if (phase == 0) {
        score = mobility * 20 + positional * 5 + corners * 100 + stability * 10 + frontier * 8 - discDiff * 2;
    } else if (phase == 1) {
        score = mobility * 15 + positional * 4 + corners * 80 + stability * 15 + frontier * 5 + discDiff * 3;
    } else {
        score = mobility * 8 + positional * 2 + corners * 50 + stability * 20 + discDiff * 25 + parity * 10;
    }
    return score;
}

int MyBot::scoreMove(const Move& m, const OthelloBoard& board, Turn player, int ply, int ttX, int ttY)
{
    if (m.x == ttX && m.y == ttY) return 100000;
    if (hasPvMove && m.x == pvMoveX && m.y == pvMoveY) return 90000;
    if (isCorner(m.x, m.y)) return 80000;

    if (ply < 64) {
        if (m.x == killerX[ply][0] && m.y == killerY[ply][0]) return 70000;
        if (m.x == killerX[ply][1] && m.y == killerY[ply][1]) return 60000;
    }

    int score = 0;

    if (isXSquare(m.x, m.y)) {
        int cornerX = (m.x < 4) ? 0 : 7;
        int cornerY = (m.y < 4) ? 0 : 7;
        if (board.get(cornerX, cornerY) == EMPTY) return -10000;
        score += 1000;
    }

    if (isCSquare(m.x, m.y)) {
        int cornerX = (m.x == 0 || m.x == 1) ? 0 : 7;
        int cornerY = (m.y == 0 || m.y == 1) ? 0 : 7;
        if (board.get(cornerX, cornerY) == EMPTY) return -5000;
        score += 500;
    }

    if (m.x == 0 || m.x == 7 || m.y == 0 || m.y == 7) score += 2000;

    int colorIdx = (player == BLACK) ? 0 : 1;
    score += historyTable[colorIdx][m.x][m.y];

    return score;
}

void MyBot::sortMoves(vector<Move>& moves, const OthelloBoard& board, Turn player, int ply, int ttX, int ttY)
{
    vector<pair<int, Move>> scored;
    scored.reserve(moves.size());

    for (const Move& m : moves) {
        scored.push_back({scoreMove(m, board, player, ply, ttX, ttY), m});
    }

    sort(scored.begin(), scored.end(), [](const auto& a, const auto& b) {
        return a.first > b.first;
    });

    for (size_t i = 0; i < moves.size(); i++) {
        moves[i] = scored[i].second;
    }
}

int MyBot::negamax(OthelloBoard& board, int depth, int alpha, int beta, Turn player, int ply)
{
    nodesSearched++;
    if (isTimeUp()) return 0;

    int alphaOrig = alpha;

    uint64_t hash = computeHash(board, player);
    int ttIdx = hash % TT_SIZE;
    TTEntry& tt = transTable[ttIdx];
    int ttX = -1, ttY = -1;

    if (tt.hash == hash && tt.depth >= depth) {
        if (tt.flag == 0) return tt.value;
        if (tt.flag == 1) alpha = max(alpha, tt.value);
        if (tt.flag == 2) beta = min(beta, tt.value);
        if (alpha >= beta) return tt.value;
        ttX = tt.bestX;
        ttY = tt.bestY;
    } else if (tt.hash == hash) {
        ttX = tt.bestX;
        ttY = tt.bestY;
    }

    list<Move> moveList = board.getValidMoves(player);

    if (moveList.empty()) {
        list<Move> oppMoves = board.getValidMoves(other(player));
        if (oppMoves.empty()) {
            int myDiscs = countDiscs(board, player);
            int oppDiscs = countDiscs(board, other(player));
            if (myDiscs > oppDiscs) return WIN_SCORE - ply;
            if (myDiscs < oppDiscs) return -WIN_SCORE + ply;
            return 0;
        }
        return -negamax(board, depth, -beta, -alpha, other(player), ply + 1);
    }

    if (depth <= 0) {
        return evaluate(board, player);
    }

    vector<Move> moves(moveList.begin(), moveList.end());
    sortMoves(moves, board, player, ply, ttX, ttY);

    int bestValue = -INF;
    int bestX = moves[0].x, bestY = moves[0].y;

    for (size_t i = 0; i < moves.size(); i++) {
        const Move& m = moves[i];

        OthelloBoard newBoard = board;
        newBoard.makeMove(player, m);

        int value;
        if (i == 0) {
            value = -negamax(newBoard, depth - 1, -beta, -alpha, other(player), ply + 1);
        } else {
            value = -negamax(newBoard, depth - 1, -alpha - 1, -alpha, other(player), ply + 1);
            if (value > alpha && value < beta) {
                value = -negamax(newBoard, depth - 1, -beta, -alpha, other(player), ply + 1);
            }
        }

        if (isTimeUp()) return 0;

        if (value > bestValue) {
            bestValue = value;
            bestX = m.x;
            bestY = m.y;
        }

        alpha = max(alpha, value);

        if (alpha >= beta) {
            if (!isCorner(m.x, m.y) && ply < 64) {
                if (killerX[ply][0] != m.x || killerY[ply][0] != m.y) {
                    killerX[ply][1] = killerX[ply][0];
                    killerY[ply][1] = killerY[ply][0];
                    killerX[ply][0] = m.x;
                    killerY[ply][0] = m.y;
                }
            }
            int colorIdx = (player == BLACK) ? 0 : 1;
            historyTable[colorIdx][m.x][m.y] += depth * depth;
            break;
        }
    }

    tt.hash = hash;
    tt.depth = depth;
    tt.value = bestValue;
    tt.bestX = bestX;
    tt.bestY = bestY;

    if (bestValue <= alphaOrig) tt.flag = 2;
    else if (bestValue >= beta) tt.flag = 1;
    else tt.flag = 0;

    return bestValue;
}

Move MyBot::iterativeDeepening(const OthelloBoard& board)
{
    list<Move> moveList = board.getValidMoves(turn);

    if (moveList.empty()) return Move::pass();
    if (moveList.size() == 1) return moveList.front();

    vector<Move> moves(moveList.begin(), moveList.end());

    Move bestMove = moves[0];
    int bestValue = -INF;
    hasPvMove = false;

    int emptySquares = 64 - board.getBlackCount() - board.getRedCount();
    int maxDepth = (emptySquares <= 12) ? emptySquares + 2 : 20;

    memset(historyTable, 0, sizeof(historyTable));

    for (int depth = 1; depth <= maxDepth && !timeUp; depth++) {
        int alpha = -INF;
        int beta = INF;

        if (depth >= 4 && bestValue != -INF && bestValue != INF) {
            alpha = bestValue - 50;
            beta = bestValue + 50;
        }

        sortMoves(moves, board, turn, 0, pvMoveX, pvMoveY);

        int currentBest = -INF;
        Move currentBestMove = moves[0];
        bool needResearch = false;

        for (size_t i = 0; i < moves.size() && !timeUp; i++) {
            const Move& m = moves[i];

            OthelloBoard newBoard = board;
            newBoard.makeMove(turn, m);

            int value;
            if (i == 0) {
                value = -negamax(newBoard, depth - 1, -beta, -alpha, other(turn), 1);
            } else {
                value = -negamax(newBoard, depth - 1, -alpha - 1, -alpha, other(turn), 1);
                if (value > alpha && value < beta && !timeUp) {
                    value = -negamax(newBoard, depth - 1, -beta, -alpha, other(turn), 1);
                }
            }

            if (timeUp) break;

            if (value <= alpha || value >= beta) needResearch = true;

            if (value > currentBest) {
                currentBest = value;
                currentBestMove = m;
            }
            alpha = max(alpha, value);
        }

        if (needResearch && !timeUp) {
            alpha = -INF;
            beta = INF;
            currentBest = -INF;

            for (const Move& m : moves) {
                if (timeUp) break;

                OthelloBoard newBoard = board;
                newBoard.makeMove(turn, m);

                int value = -negamax(newBoard, depth - 1, -beta, -alpha, other(turn), 1);

                if (value > currentBest) {
                    currentBest = value;
                    currentBestMove = m;
                }
                alpha = max(alpha, value);
            }
        }

        if (!timeUp) {
            bestMove = currentBestMove;
            bestValue = currentBest;
            pvMoveX = bestMove.x;
            pvMoveY = bestMove.y;
            hasPvMove = true;

            if (bestValue >= WIN_SCORE - 100) break;
        }
    }

    return bestMove;
}

Move MyBot::play(const OthelloBoard& board)
{
    startTime = chrono::high_resolution_clock::now();
    timeUp = false;
    nodesSearched = 0;

    return iterativeDeepening(board);
}

extern "C" {
    OthelloPlayer* createBot(Turn turn)
    {
        return new MyBot(turn);
    }

    void destroyBot(OthelloPlayer* bot)
    {
        delete bot;
    }
}
