import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from reloop.core import load,digest,atomic
from reloop.sourcecache import build,lock
from reloop.primarysource import expression

class SourceCacheTests(unittest.TestCase):
    def fixture(self,tmp):
        root=Path(tmp);clang=root/'clang';ld=root/'ld';clang.write_bytes(b'owned compiler');ld.write_bytes(b'owned linker')
        return root/'cache',root/'published',clang,ld
    def compiler(self,args,**kwargs):
        out=Path(args[args.index('-o')+1])
        if '-emit-llvm' in args:out.write_text("; ModuleID = 'owned'\nsource_filename = \"owned\"\nowned IR\n")
        else:out.write_bytes(b'\0asm\x01\0\0\0owned module')
        return subprocess.CompletedProcess(args,0,b'',b'')
    def test_hit_whitespace_and_atomic_failure(self):
        with TemporaryDirectory() as tmp,patch('reloop.sourcecache.run_compiler',side_effect=self.compiler) as run:
            c,o,clang,ld=self.fixture(tmp);text=expression(4);a=build(text,c,o,clang,ld);self.assertFalse(a['cache_hit']);self.assertEqual(run.call_count,2)
            b=build(text,c,o,clang,ld);self.assertTrue(b['cache_hit']);self.assertEqual(run.call_count,2)
            w=build(text.replace('Color(', 'Color ('),c,o,clang,ld);self.assertTrue(w['cache_hit']);self.assertEqual(a['module_sha256'],w['module_sha256']);self.assertNotEqual(a['source_sha256'],w['source_sha256'])
            old=(o/'current.json').read_bytes()
            for text in ('Text("bad")',expression(8)):
                with self.assertRaises((ValueError,RuntimeError)):build(text,c,o,clang,ld,fault_before_commit=True)
                self.assertEqual((o/'current.json').read_bytes(),old)
            self.assertFalse(list(c.glob('.owned-build-*')));self.assertFalse(list(o.glob('.owned-publish-*')))
    def test_payload_manifest_and_index_corruption(self):
        with TemporaryDirectory() as tmp,patch('reloop.sourcecache.run_compiler',side_effect=self.compiler):
            c,o,clang,ld=self.fixture(tmp);a=build(expression(4),c,o,clang,ld);folder=c/'entries'/a['entry_sha256'];old=(o/'current.json').read_bytes()
            for name in ('view.wasm','manifest.json','view.ll'):
                p=folder/name;original=p.read_bytes();p.write_bytes(original+b'bad')
                with self.assertRaises(ValueError):build(expression(4),c,o,clang,ld)
                self.assertEqual((o/'current.json').read_bytes(),old);p.write_bytes(original)
            idx=c/'keys'/(a['cache_key']+'.json');atomic(idx,{'version':1,'entry_sha256':'../escape'})
            with self.assertRaises(ValueError):build(expression(4),c,o,clang,ld)
    def test_named_linker_alias_preserves_driver_flavor(self):
        with TemporaryDirectory() as tmp,patch('reloop.sourcecache.run_compiler',side_effect=self.compiler) as run:
            c,o,clang,ld=self.fixture(tmp);alias=Path(tmp)/'wasm-ld';alias.symlink_to(ld)
            result=build(expression(4),c,o,clang,alias)
            command=run.call_args_list[1].args[0]
            self.assertIn('-fuse-ld='+str(alias),command)
            self.assertEqual(load(o/'versions'/result['entry_sha256']/'manifest.json')['identity']['wasm_ld_invocation'],str(alias))
            self.assertFalse(build(expression(4),c,o,clang,ld)['cache_hit'])

    def test_tool_identity_timeout_symlinks_and_lock(self):
        with TemporaryDirectory() as tmp,patch('reloop.sourcecache.run_compiler',side_effect=self.compiler):
            c,o,clang,ld=self.fixture(tmp);a=build(expression(4),c,o,clang,ld);old=(o/'current.json').read_bytes();clang.write_bytes(b'changed compiler')
            with patch('reloop.sourcecache.run_compiler',side_effect=subprocess.TimeoutExpired(['owned'],30)):
                with self.assertRaises(subprocess.TimeoutExpired):build(expression(4),c,o,clang,ld)
            self.assertEqual((o/'current.json').read_bytes(),old);self.assertFalse(list(c.glob('.owned-build-*')))
            with lock(c,'.build.lock'):
                with self.assertRaises(RuntimeError):build(expression(4),c,o,clang,ld)
            clang.write_bytes(b'owned compiler');folder=c/'entries'/a['entry_sha256'];p=folder/'view.wasm';raw=p.read_bytes();p.unlink();outside=Path(tmp)/'outside';outside.write_bytes(raw);p.symlink_to(outside)
            with self.assertRaises(ValueError):build(expression(4),c,o,clang,ld)
            self.assertEqual((o/'current.json').read_bytes(),old)
