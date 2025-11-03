include ../Desdemona/Makefile.inc

all: StrongBot.so

StrongBot.so: StrongBot.o
	g++ -shared -o StrongBot.so StrongBot.o

StrongBot.o: StrongBot.cpp
	g++ $(CXXFLAGS) -I../Desdemona/include -c StrongBot.cpp

clean:
	rm -f *.o *.so
