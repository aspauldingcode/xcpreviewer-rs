"""Bounded, non-executing reader for thin little-endian 64-bit Mach-O metadata."""
import base64
import pathlib
import struct
from reloop.core import digest


class MachO:
    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.data = self.path.read_bytes()
        self.sections = []
        self.uuid = None
        if len(self.data) < 32 or self.u32(0) != 0xfeedfacf:
            raise ValueError('Expected thin little-endian Mach-O 64; select a slice first')
        count, size = self.unpack('<II', 16)
        if count > 65536 or 32 + size > len(self.data):
            raise ValueError('Invalid load-command table')
        offset = 32
        for _ in range(count):
            command, length = self.unpack('<II', offset)
            if length < 8 or offset + length > 32 + size:
                raise ValueError('Invalid load command')
            if command == 0x1b:
                if length < 24: raise ValueError('Truncated UUID command')
                self.uuid = self.data[offset + 8:offset + 24].hex()
            if command == 0x19:
                if length < 72: raise ValueError('Truncated segment command')
                nsects = self.u32(offset + 64)
                if 72 + nsects * 80 > length: raise ValueError('Truncated section table')
                for i in range(nsects):
                    p = offset + 72 + i * 80
                    name = self.data[p:p + 16].split(b'\0')[0].decode(errors='replace')
                    segment = self.data[p + 16:p + 32].split(b'\0')[0].decode(errors='replace')
                    addr, extent, fileoff = self.unpack('<QQI', p + 32)
                    flags = self.u32(p + 64)
                    # Zerofill sections have no corresponding on-disk bytes.
                    disk = flags & 0xff not in {1, 0xc, 0x12}
                    if disk and fileoff + extent > len(self.data): raise ValueError('Section outside image')
                    self.sections.append({'name': name, 'segment': segment, 'address': addr,
                                          'size': extent, 'offset': fileoff, 'disk': disk, 'flags':flags,
                                          'reserved1':self.u32(p+68),'reserved2':self.u32(p+72)})
            offset += length

    def unpack(self, fmt, offset):
        extent = struct.calcsize(fmt)
        if offset < 0 or offset + extent > len(self.data): raise ValueError('Read outside image')
        return struct.unpack_from(fmt, self.data, offset)

    def u32(self, offset): return self.unpack('<I', offset)[0]

    def file_offset(self, address):
        for section in self.sections:
            if section['disk'] and section['address'] <= address < section['address'] + section['size']:
                return section['offset'] + address - section['address']
        raise ValueError('Address not mapped to file-backed section')

    def relative(self, field_address, indirect=False):
        value = self.unpack('<i', self.file_offset(field_address))[0]
        if not value: return None
        if indirect and value & 1:
            # Indirect context pointers need runtime relocations. Preserve unknown.
            raise ValueError('Indirect relative pointer requires relocation resolution')
        return field_address + value

    def string(self, address, maximum=512):
        offset = self.file_offset(address)
        end = self.data.find(b'\0', offset, min(offset + maximum, len(self.data)))
        if end < 0: raise ValueError('Unterminated bounded metadata string')
        value = self.data[offset:end]
        # Symbolic mangling references contain control bytes and embedded pointers.
        if any(v < 0x20 for v in value):
            return {'unresolved_symbolic_prefix_base64': base64.b64encode(value).decode()}
        return value.decode('utf-8', errors='replace')

    def context(self, address, seen=()):
        if address in seen or len(seen) >= 8: raise ValueError('Context cycle/depth limit')
        flags = self.u32(self.file_offset(address)); kind = flags & 31
        name = self.string(self.relative(address + 8)) if kind in {0, 3, 16, 17, 18} else None
        parent = self.relative(address + 4, indirect=True)
        result = {'address': hex(address), 'kind': kind, 'flags': hex(flags), 'name': name}
        if parent:
            try: result['parent'] = self.context(parent, seen + (address,))
            except ValueError as error: result['parent_unresolved'] = str(error)
        return result


def inspect(path, maximum=1000):
    if type(maximum) is not int or not 1 <= maximum <= 5000: raise ValueError('Invalid metadata limit')
    image = MachO(path); types = []; errors = []
    for section in image.sections:
        if section['name'] != '__swift5_types': continue
        for i in range(min(section['size'] // 4, maximum)):
            entry = section['address'] + i * 4
            try:
                descriptor = image.relative(entry)
                if descriptor is None: continue
                context = image.context(descriptor)
                if context['kind'] in {16, 17, 18}:
                    fields = image.relative(descriptor + 16)
                    if fields:
                        p = image.file_offset(fields)
                        record_size, count = image.unpack('<HI', p + 10)
                        if record_size < 12 or count > 100000: raise ValueError('Invalid field descriptor')
                        context['field_count'] = count; context['fields'] = []
                        for j in range(min(count, 128)):
                            address = fields + 16 + j * record_size
                            item = {'flags': image.u32(image.file_offset(address))}
                            for label, delta in [('mangled_type', 4), ('name', 8)]:
                                try:
                                    pointer = image.relative(address + delta)
                                    item[label] = image.string(pointer) if pointer else None
                                except ValueError as error: item[label + '_unresolved'] = str(error)
                            context['fields'].append(item)
                types.append(context)
            except (ValueError, TypeError) as error:
                errors.append({'entry': hex(entry), 'error': str(error)})
    return {'image_sha256': digest(path), 'image_uuid': image.uuid,
            'swift_sections': [s for s in image.sections if s['name'].startswith('__swift5')],
            'types': types, 'errors': errors,
            'scope': 'Static nominal descriptors and field names; unresolved symbolic/indirect pointers preserved. Not a Swift calling-convention decoder.'}
