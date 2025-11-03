#!/bin/bash

# Tournament script to compare Othello bots

GAMES_PER_MATCHUP=10
DESDEMONA="../Desdemona/bin/Desdemona"

declare -a BOTS=(
    "../Desdemona/bots/MyBot/bot.so"
    "StrongBot.so"
    "../Desdemona/bots/RandomBot/RandomBot.so"
    "../Desdemona/bots/SlowBot/SlowBot.so"
)

declare -a BOT_NAMES=(
    "MyBot"
    "StrongBot"
    "RandomBot"
    "SlowBot"
)

# Initialize statistics
declare -A wins
declare -A losses
declare -A draws
declare -A total_score

for name in "${BOT_NAMES[@]}"; do
    wins[$name]=0
    losses[$name]=0
    draws[$name]=0
    total_score[$name]=0
done

echo "================================================"
echo "        OTHELLO BOT TOURNAMENT"
echo "================================================"
echo ""

# Run all matchups
for i in "${!BOTS[@]}"; do
    for j in "${!BOTS[@]}"; do
        if [ $i -ne $j ]; then
            bot1="${BOTS[$i]}"
            bot2="${BOTS[$j]}"
            name1="${BOT_NAMES[$i]}"
            name2="${BOT_NAMES[$j]}"
            
            echo "-------------------------------------------"
            echo "$name1 (BLACK) vs $name2 (RED)"
            echo "-------------------------------------------"
            
            for game in $(seq 1 $GAMES_PER_MATCHUP); do
                result=$($DESDEMONA "$bot1" "$bot2" 2>/dev/null | grep "Result")
                
                # Extract scores
                black_score=$(echo $result | grep -oP 'BLACK: \K\d+')
                red_score=$(echo $result | grep -oP 'RED: \K\d+')
                
                echo "Game $game: BLACK=$black_score RED=$red_score"
                
                total_score[$name1]=$((${total_score[$name1]} + black_score))
                total_score[$name2]=$((${total_score[$name2]} + red_score))
                
                if [ $black_score -gt $red_score ]; then
                    wins[$name1]=$((${wins[$name1]} + 1))
                    losses[$name2]=$((${losses[$name2]} + 1))
                elif [ $black_score -lt $red_score ]; then
                    losses[$name1]=$((${losses[$name1]} + 1))
                    wins[$name2]=$((${wins[$name2]} + 1))
                else
                    draws[$name1]=$((${draws[$name1]} + 1))
                    draws[$name2]=$((${draws[$name2]} + 1))
                fi
            done
            echo ""
        fi
    done
done

# Print final standings
echo "================================================"
echo "        FINAL STANDINGS"
echo "================================================"
printf "%-15s %5s %5s %5s %10s %8s\n" "Bot" "Wins" "Loss" "Draw" "TotalScore" "WinRate"
echo "------------------------------------------------"

for name in "${BOT_NAMES[@]}"; do
    total_games=$((${wins[$name]} + ${losses[$name]} + ${draws[$name]}))
    if [ $total_games -gt 0 ]; then
        win_rate=$(echo "scale=2; ${wins[$name]} * 100 / $total_games" | bc)
    else
        win_rate=0
    fi
    printf "%-15s %5d %5d %5d %10d %7.1f%%\n" \
        "$name" "${wins[$name]}" "${losses[$name]}" "${draws[$name]}" \
        "${total_score[$name]}" "$win_rate"
done
echo "================================================"
