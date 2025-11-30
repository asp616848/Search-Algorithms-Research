#
# Author: Amol Dumrewal <amoldumrewal@gmail.com>
#

ROOTDIR  = ../../
include $(ROOTDIR)Makefile.inc

BOT	= MyBot
OUT = MyBot.so

OBJS = $(BOT).o

all: $(OUT)

$(OUT): $(BOT).o $(ROOTDIR)lib/libOthello.so
	$(CC) $(LDFLAGS) -shared $^ -o $@

${OBJS}: %.o : %.cpp
	$(CC) $(CFLAGS) -c $^ -o $@

.PHONY: clean submission

submission: clean
	zip othello.zip *

clean:
	rm -rf $(OUT)
	rm -rf *.o
