#include <dlfcn.h>
#include <stdint.h>
uintptr_t owned_symbol_offset(void *symbol) { Dl_info info; return dladdr(symbol,&info) ? (uintptr_t)symbol-(uintptr_t)info.dli_fbase : UINTPTR_MAX; }
const char *owned_symbol_path(void *symbol) { Dl_info info; return dladdr(symbol,&info) ? info.dli_fname : ""; }

#include <mach-o/dyld.h>
#include <mach-o/loader.h>
unsigned owned_image_count(void) { return _dyld_image_count(); }
const char *owned_image_path(unsigned index) { return _dyld_get_image_name(index); }
const unsigned char *owned_image_uuid(unsigned index) {
 const struct mach_header *head = _dyld_get_image_header(index);
 if (!head || head->magic != MH_MAGIC_64) return 0;
 const struct load_command *command = (const void *)((const struct mach_header_64 *)head + 1);
 for (unsigned i=0;i<head->ncmds;i++) {
  if (command->cmdsize < sizeof(*command)) return 0;
  if (command->cmd == LC_UUID && command->cmdsize >= sizeof(struct uuid_command)) return ((const struct uuid_command *)command)->uuid;
  command=(const void *)((const char *)command+command->cmdsize);
 }
 return 0;
}
