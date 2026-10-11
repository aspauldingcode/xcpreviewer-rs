"""Actual owned subprocess output cap and pre-aborted admission checks."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parents[3]

class OwnedCompilerTests(unittest.TestCase):
    def test_bounded_output_and_pre_aborted_admission(self):
        node=shutil.which('node')
        if not node:self.skipTest('Existing Node required')
        code="""const assert=require('node:assert/strict');
const {runOwned}=require(process.argv[1]);
(async()=>{
 const a=new AbortController();a.abort();
 await assert.rejects(runOwned(process.argv[2],['-c','print("must not run")'],{signal:a.signal}),/before spawn/);
 await assert.rejects(runOwned(process.argv[2],['-c','print("x"*4096)'],{limit:64}),/output limit/);
 const r=await runOwned(process.argv[2],['-c','print("owned")']);assert.equal(r.stdout,'owned\\n');assert.equal(r.code,0);
 console.log(JSON.stringify({controls:3}));
})().catch(e=>{console.error(e);process.exitCode=1;});"""
        result=subprocess.run([node,'-e',code,str(ROOT/'tools/re/reloop/owned_compiler.js'),sys.executable],
                              check=True,timeout=10,capture_output=True,text=True)
        self.assertEqual(json.loads(result.stdout)['controls'],3)
