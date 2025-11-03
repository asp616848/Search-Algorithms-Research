#!/bin/bash

# Quick comparison script for MyBot vs StrongBot

DESDEMONA="../Desdemona/bin/Desdemona"
MYBOT="../Desdemona/bots/MyBot/bot.so"
STRONGBOT="StrongBot.so"
GAMES=5

echo "========================================"
echo "   MyBot vs StrongBot Quick Test"
echo "========================================"
echo ""

# Test MyBot as BLACK
echo "Round 1: MyBot (BLACK) vs StrongBot (RED)"
echo "----------------------------------------"
mybot_wins_black=0
strongbot_wins_black=0
for i in $(seq 1 $GAMES); do
    result=$($DESDEMONA "$MYBOT" "$STRONGBOT" 2>/dev/null | grep "Result")
    black_score=$(echo $result | grep -oP 'BLACK: \K\d+')
    red_score=$(echo $result | grep -oP 'RED: \K\d+')
    echo "Game $i: MyBot=$black_score StrongBot=$red_score"
    if [ $black_score -gt $red_score ]; then
        mybot_wins_black=$((mybot_wins_black + 1))
    elif [ $red_score -gt $black_score ]; then
        strongbot_wins_black=$((strongbot_wins_black + 1))
    fi
done
echo ""

# Test MyBot as RED
echo "Round 2: StrongBot (BLACK) vs MyBot (RED)"
echo "----------------------------------------"
mybot_wins_red=0
strongbot_wins_red=0
for i in $(seq 1 $GAMES); do
    result=$($DESDEMONA "$STRONGBOT" "$MYBOT" 2>/dev/null | grep "Result")
    black_score=$(echo $result | grep -oP 'BLACK: \K\d+')
    red_score=$(echo $result | grep -oP 'RED: \K\d+')
    echo "Game $i: StrongBot=$black_score MyBot=$red_score"
    if [ $red_score -gt $black_score ]; then
        mybot_wins_red=$((mybot_wins_red + 1))
    elif [ $black_score -gt $red_score ]; then
        strongbot_wins_red=$((strongbot_wins_red + 1))
    fi
done
echo ""

# Summary
echo "========================================"
echo "            SUMMARY"
echo "========================================"
mybot_total_wins=$((mybot_wins_black + mybot_wins_red))
strongbot_total_wins=$((strongbot_wins_black + strongbot_wins_red))
total_games=$((GAMES * 2))

echo "Total games: $total_games"
echo "MyBot wins: $mybot_total_wins"
echo "StrongBot wins: $strongbot_total_wins"
echo ""

if [ $mybot_total_wins -gt $strongbot_total_wins ]; then
    echo "🏆 MyBot is STRONGER!"
elif [ $strongbot_total_wins -gt $mybot_total_wins ]; then
    echo "🏆 StrongBot is STRONGER!"
else
    echo "🤝 It's a TIE!"
fi
echo "========================================"
