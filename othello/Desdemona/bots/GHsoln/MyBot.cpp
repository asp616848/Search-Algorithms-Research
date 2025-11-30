/*
* @author Amol Dumrewal <amoldumrewal@gmail.com>
*/

#include "Othello.h"
#include "OthelloBoard.h"
#include "OthelloPlayer.h"
#include <cstdlib>
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
        virtual int beta(const OthelloBoard& board, int depth, int alpha_min, int beta_max);
        virtual int alpha(const OthelloBoard& board, int depth, int alpha_min, int beta_max);
        virtual int heuristic(const OthelloBoard& board, Turn turn);
        virtual int heu_brute(const OthelloBoard& board, Turn turn);
        virtual int heu_stat(const OthelloBoard& board, Turn turn);
        int move_num = 0;
        Turn my_color;
    private:
};

MyBot::MyBot( Turn turn )
    : OthelloPlayer( turn )
{
}

Move MyBot::play( const OthelloBoard& board )
{
  move_num++;
  int depth=2;
  if(move_num==1)my_color = turn;
    list<Move> moves = board.getValidMoves( turn );
    list<Move>::iterator it = moves.begin();
    int max_a = -400;
    int a;
    Move next_move = *it;
    for(int i=1; i < moves.size(); it++, i++){
      Turn trn = turn;
      OthelloBoard my_board = board;
      my_board.makeMove(trn,*it);
      a = beta(my_board,depth,max_a,400);
      if(a>max_a){
        max_a = a;
        next_move = *it;
      }
    }
    return next_move;
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

int MyBot::beta(const OthelloBoard& board, int depth, int alpha_min, int beta_max){
  Turn turn_b = (turn==RED)?BLACK:RED;
  list<Move> moves = board.getValidMoves( turn_b );
  list<Move>::iterator it = moves.begin();
  int min_b = beta_max;
  int b;
  for(int i=0; i < moves.size(); it++, i++){
    Turn trn_b = turn_b;
    OthelloBoard my_board = board;
    my_board.makeMove(trn_b,*it);
    b = alpha(my_board,depth-1,alpha_min,min_b);
    if(b<min_b){
      min_b = b;
      if(min_b<alpha_min)return alpha_min;
    }
  }
  return min_b;
}

int MyBot::alpha(const OthelloBoard& board, int depth, int alpha_min, int beta_max){
  if(depth == 0){
    OthelloBoard my_board = board;
    return heuristic(my_board,turn);
  }
  list<Move> moves = board.getValidMoves( turn );
  list<Move>::iterator it = moves.begin();
  int max_a = alpha_min;
  int a;
  for(int i=0; i < moves.size(); it++, i++){
    Turn trn = turn;
    OthelloBoard my_board = board;
    my_board.makeMove(trn,*it);
    a = beta(my_board,depth,max_a,beta_max);
    if(a>max_a){
      max_a = a;
      if(max_a>beta_max)return beta_max;
    }
  }
  return max_a;
}

int MyBot::heuristic(const OthelloBoard& board, Turn turn){
  int randNo = rand() % 50;
  if(move_num <25)return heu_stat(board,turn);
  else return heu_brute(board,turn);
  return randNo;
}

int MyBot::heu_stat(const OthelloBoard& board, Turn turn){
  Turn turn_b = other(turn);
  int i,j;
/*  int ar[8][8]={ 10,-3,2,2,2,2,-3,10
                ,-3,-4,-1,-1,-1,-1,-4,-3
                ,2,-1,1,0,0,1,-1,-2
                ,2,-1,0,1,1,0,-1,2
                ,2,-1,0,1,1,0,-1,2
                ,2,-1,1,0,0,1,1,-2
                ,-3,-4,-1,-1,-1,1,-4,-3
                ,10,-3,2,2,2,2,-3,10 };*/
  int ar[8][8]={8,-7, 3, 3, 3, 3,-5, 8,
               -7, -4, 2, 2, 2, 2, -4,-5,
                3, 2, 1, 1, 1, 1, 2, 3,
                3, 2, 1, 1, 1, 1, 2, 3,
                3, 2, 1, 1, 1, 1, 2, 3,
                3, 2, 1, 1, 1, 1, 2, 3,
               -2, -2, 2, 2, 2, 2, -2,-2,
               8,-2, 3, 3, 3, 3,-2, 8};
  int sum =0;
  for(i=0;i<8;i++){
    for(j=0;j<8;j++){
      if(board.get(i,j)==turn)sum = sum+ar[i][j];
      if(board.get(i,j)==turn_b)sum = sum-ar[i][j];
    }
  }
  return sum;
}

int MyBot::heu_brute(const OthelloBoard& board, Turn turn){
  Turn turn_b = other(turn);
  int i,j;
  int ar[8][8];
  for(i=0;i<8;i++){
    for(j=0;j<8;j++){
      ar[i][j]=1;
    }
  }
  ar[6][6]=0;
  ar[6][1]=0;
    ar[7][7]=16;
    ar[0][7]=10;
    ar[7][0]=16;
    ar[0][0]=10;
  int sum =0;
  for(i=0;i<8;i++){
    for(j=0;j<8;j++){
      if(board.get(i,j)==turn)sum = sum+ar[i][j];
      if(board.get(i,j)==turn_b)sum = sum-ar[i][j];
    }
  }
  return sum;
}
