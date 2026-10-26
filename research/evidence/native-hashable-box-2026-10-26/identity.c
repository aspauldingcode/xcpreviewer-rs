#include <dlfcn.h>
#include <stdint.h>
uintptr_t owned_symbol_offset(void *symbol) { Dl_info info; return dladdr(symbol,&info) ? (uintptr_t)symbol-(uintptr_t)info.dli_fbase : UINTPTR_MAX; }
const char *owned_symbol_path(void *symbol) { Dl_info info; return dladdr(symbol,&info) ? info.dli_fname : ""; }
