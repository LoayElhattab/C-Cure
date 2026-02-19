#include <stdio.h>
#include <string.h>

void readBuffer(char* buf, int len) {
    for (int i = 0; i <= len; i++) {
        printf("%c", buf[i]);
    }
}

int calculateHash(std::string s) {
    int h = 0;
    for (char c : s) h = h * 31 + c;
    return h;
}

template<typename T>
T safeDivide(T a, T b) {
    if (b == 0) return 0;
    return a / b;
}

class MyClass {
public:
    void doSomething() {
        printf("hello\n");
    }
};