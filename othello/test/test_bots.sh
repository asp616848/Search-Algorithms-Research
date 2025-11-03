#!/bin/bash

# Simple bot comparison script

DESDEMONA="../Desdemona/bin/Desdemona"
MYBOT="../Desdemona/bots/MyBot/bot.so"
STRONGBOT="StrongBot.so"
RANDOMBOT="../Desdemona/bots/RandomBot/RandomBot.so"
SLOWBOT="../Desdemona/bots/SlowBot/SlowBot.so"

echo "==========================================="
echo "   OTHELLO BOT COMPARISON TEST"
echo "==========================================="
echo ""

# Test MyBot vs StrongBot
echo "Test 1: MyBot vs StrongBot (10 games)"
echo "-------------------------------------------"
mybot_wins=0
strongbot_wins=0
for i in {1..5}; do
    result=$(echo "" | $DESDEMONA "$MYBOT" "$STRONGBOT" 2>/dev/null | grep "Win" | awk '{print $2}')
    if [ "$result" == "Black" ]; then
        ((mybot_wins++))
        echo "  Game $i: MyBot (BLACK) wins"
    else
        ((strongbot_wins++))
        echo "  Game $i: StrongBot (RED) wins"
    fi
done

for i in {6..10}; do
    result=$(echo "" | $DESDEMONA "$STRONGBOT" "$MYBOT" 2>/dev/null | grep "Win" | awk '{print $2}')
    if [ "$result" == "Red" ]; then
        ((mybot_wins++))
        echo "  Game $i: MyBot (RED) wins"
    else
        ((strongbot_wins++))
        echo "  Game $i: StrongBot (BLACK) wins"
    fi
done

echo ""
echo "MyBot: $mybot_wins wins, StrongBot: $strongbot_wins wins"
echo ""

# Test MyBot vs RandomBot
echo "Test 2: MyBot vs RandomBot (5 games)"
echo "-------------------------------------------"
mybot_vs_random=0
for i in {1..5}; do
    result=$(echo "" | $DESDEMONA "$MYBOT" "$RANDOMBOT" 2>/dev/null | grep "Win" | awk '{print $2}')
    if [ "$result" == "Black" ]; then
        ((mybot_vs_random++))
        echo "  Game $i: MyBot wins"
    else
        echo "  Game $i: RandomBot wins"
    fi
done
echo "MyBot wins: $mybot_vs_random/5"
echo ""

# Test StrongBot vs RandomBot
echo "Test 3: StrongBot vs RandomBot (5 games)"
echo "-------------------------------------------"
strongbot_vs_random=0
for i in {1..5}; do
    result=$(echo "" | $DESDEMONA "$STRONGBOT" "$RANDOMBOT" 2>/dev/null | grep "Win" | awk '{print $2}')
    if [ "$result" == "Black" ]; then
        ((strongbot_vs_random++))
        echo "  Game $i: StrongBot wins"
    else
        echo "  Game $i: RandomBot wins"
    fi
done
echo "StrongBot wins: $strongbot_vs_random/5"
echo ""

echo "==========================================="
echo "              SUMMARY"
echo "==========================================="
echo "MyBot vs StrongBot:  $mybot_wins - $strongbot_wins"
echo "MyBot vs RandomBot:  $mybot_vs_random - $((5 - mybot_vs_random))"
echo "StrongBot vs RandomBot: $strongbot_vs_random - $((5 - strongbot_vs_random))"
echo "==========================================="
