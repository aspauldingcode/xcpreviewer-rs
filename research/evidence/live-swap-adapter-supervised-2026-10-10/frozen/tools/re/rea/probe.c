#include <stdint.h>
__attribute__((noinline)) uint64_t reloop_rea_leaf(uint64_t x) { return x ^ UINT64_C(0x12345678); }
__attribute__((noinline)) uint64_t reloop_rea_entry(uint64_t x) { return reloop_rea_leaf(x) + 7; }
int main(void) { return reloop_rea_entry(3) == UINT64_C(0x12345682) ? 0 : 1; }
