from pathlib import Path
import ast,json,hashlib
w=Path(__file__).parent;manifest=json.loads((w/'sources.json').read_text())
for row in manifest['files']:
 p=w/row['path'];assert p.stat().st_size==row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
tree=ast.parse((w/'tools/xcodeproj2xtool.py').read_text());platforms=None;selector=None
for node in ast.walk(tree):
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PLATFORMS' for t in node.targets):platforms=ast.literal_eval(node.value)
 if isinstance(node,ast.FunctionDef) and node.name=='platform_of':selector=ast.unparse(node)
assert set(platforms)=={'ios','macos'} and selector and "else 'ios'" in selector
result={'repository':manifest['repository'],'revision':manifest['revision'],'source_files_hashed':len(manifest['files']),'reviewed_importer_platform_table':sorted(platforms),'platform_selection_scope':'Static source: macOS when only macosx is selected, otherwise iOS. No additional Apple platform support inferred.','simview_native_parity_disclaimer_present':"not real SwiftUI layout, fonts, animation, or Metal" in (w/'simview/README.md').read_text(),'license':'MIT; retain upstream notices in any future copied/adapted portions','upstream_code_executed':False,'upstream_code_copied_into_product':False,'upstream_toolchain_installed':False,'scope':'Source/document review only; no independent build, device, preview or host compatibility verification.'}
assert result['simview_native_parity_disclaimer_present'];(w/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
