"""Replay frozen existing tests with explicitly selected frozen reader modules."""
from pathlib import Path
import importlib.util,unittest,json,sys,types,ast
p=Path(__file__).resolve().parent;r=Path('/Users/8amps/xcpreviewer-rs');source=sys.argv[1];catalog=json.loads((p/'selection.json').read_text())['catalog']
class Result(unittest.TestResult):
 def __init__(self):super().__init__();self.records=[]
 def addSubTest(self,test,subtest,err):
  self.records.append({'kind':'subtest','id':subtest.id(),'accepted_fault':err is not None,'exception':err[0].__name__ if err else None,'message':str(err[1]) if err else None});super().addSubTest(test,subtest,err)
 def addError(self,test,err):self.records.append({'kind':'error','id':test.id(),'exception':err[0].__name__});super().addError(test,err)
 def addFailure(self,test,err):self.records.append({'kind':'failure','id':test.id(),'exception':err[0].__name__});super().addFailure(test,err)
 def addSuccess(self,test):self.records.append({'kind':'success','id':test.id()});super().addSuccess(test)
results=[]
for row in catalog:
 spec=importlib.util.spec_from_file_location('selected_reader',p/source/row['reader']);reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
 # Only the frozen stdlib test text executes. Its logical file location preserves
 # original ROOT/source comparisons. Replace its reader before any test runs.
 m=types.ModuleType('frozen_'+row['name']);m.__file__=str(r/'tools/re/tests'/row['test']);code=(p/'tests'/row['test']).read_text();exec(compile(code,m.__file__,'exec'),m.__dict__);m.reader=reader
 result=Result();unittest.defaultTestLoader.loadTestsFromModule(m).run(result)
 results.append({'reader':row['reader'],'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'records':result.records,'positive_result':reader.verify(r/row['evidence'])})
print(json.dumps({'source':source,'optimized':not __debug__,'results':results,'native_execution':False}))
