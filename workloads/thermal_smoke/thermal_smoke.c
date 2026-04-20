#include <stdint.h>

extern void printstr(const char *s);

int main(void) {
  volatile uint64_t acc = 0;
  for (int i = 0; i < 8; ++i) {
    acc += (uint64_t)i;
  }

  printstr("thermal-smoke-ok\n");
  return acc == 28 ? 0 : 1;
}
