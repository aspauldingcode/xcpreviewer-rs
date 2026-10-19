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
 # Rebind only the three original module-loader bootstrap statements. Test
 # methods/assertions remain unchanged, and no installed reader is imported.
 m=types.ModuleType('frozen_'+row['name']);m.__file__=str(r/'tools/re/tests'/row['test']);m.reader=reader
 tree=ast.parse((p/'tests'/row['test']).read_text());kept=[];removed=[]
 for node in tree.body:
  loader_assign=isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['s','reader'] for t in node.targets)
  loader_exec=isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and ast.unparse(node.value.func)=='s.loader.exec_module'
  (removed if loader_assign or loader_exec else kept).append(node)
 if len(removed)!=3:raise ValueError('Unexpected test bootstrap')
 exec(compile(ast.Module(body=kept,type_ignores=[]),m.__file__,'exec'),m.__dict__)
 result=Result();unittest.defaultTestLoader.loadTestsFromModule(m).run(result)
 results.append({'reader':row['reader'],'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'records':result.records,'positive_result':reader.verify(r/row['evidence'])})
print(json.dumps({'source':source,'optimized':not __debug__,'results':results,'native_execution':False}))
