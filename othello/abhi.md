 cd /home/abhi/College/SMAI/Search-Algorithms-Research/othello/Desdemona/bots/MyBot && make clean && make

cd /home/abhi/College/SMAI/Search-Algorithms-Research/othello/Desdemona

chmod +x bin/Desdemona

./bin/Desdemona bots/akshat.so bots/bestBot/bot.so 

./bin/Desdemona bots/bestBot/bot.so bots/TrainerBot/bot.so
./bin/Desdemona bots/TrainerBot/bot.so bots/bestBot/bot.so

<!-- By convention, the first bot is BLACK and the second RED. -->

test:
for i in {1..3}; do echo "Game $i:"; ./bin/Desdemona bots/MyBot/bot.so bots/RandomBot/RandomBot.so | tail -4; done

for i in {1..3}; do echo "Game $i:"; ./bin/Desdemona bots/RandomBot/RandomBot.so bots/MyBot/bot.so | tail -4; done
