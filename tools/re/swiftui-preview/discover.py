#!/usr/bin/env python3
"""List actual compiler-generated #Preview registries from one owned Swift source.

Mac-only discovery; invokes registry constructors, not stored view-body closures.
"""
from pathlib import Path
import argparse,hashlib,json,os,platform,re,signal,subprocess,sys,tempfile


def run(arguments, timeout, environment):
    process=subprocess.Popen(arguments,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                             env=environment,start_new_session=True)
    try:
        stdout,stderr=process.communicate(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
        try: os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError: pass
        process.communicate()
        if isinstance(error, KeyboardInterrupt): raise
        raise RuntimeError(f"Owned process exceeded {timeout:g} seconds") from None
    if len(stdout)>8*1024*1024 or len(stderr)>8*1024*1024:
        raise ValueError("Compiler/runtime output exceeds 8 MiB")
    if process.returncode:
        raise RuntimeError(stderr[-65536:].decode(errors="replace") or
                           f"Owned process exited {process.returncode}")
    return stdout,stderr


def discover(source, runtime_seconds=8):
    if platform.system()!='Darwin' or platform.machine() not in ('arm64','x86_64'):
        raise ValueError('Preview discovery requires a supported Mac')
    if not 0.1<=runtime_seconds<=8:
        raise ValueError('Runtime deadline must be between 0.1 and 8 seconds')
    path=Path(source).resolve(strict=True)
    if not path.is_file() or path.stat().st_size>1024*1024:
        raise ValueError('Source must be a file of at most 1 MiB')
    with path.open('rb') as stream: data=stream.read(1024*1024+1)
    if len(data)>1024*1024: raise ValueError('Source exceeds 1 MiB')
    environment={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')}
    compiler=run(['xcrun','--find','swiftc'],5,environment)[0].decode().strip()
    sdk=run(['xcrun','--show-sdk-path'],5,environment)[0].decode().strip()
    version=run([compiler,'--version'],5,environment)[0].decode().strip()
    target=platform.machine()+'-apple-macos14.0'
    with tempfile.TemporaryDirectory(prefix='swiftui-discover-') as directory:
        work=Path(directory);owned=work/'Source.swift';owned.write_bytes(data)
        common=[compiler,'-parse-as-library','-module-name','PreviewDiscovery','-target',target,
                '-sdk',sdk,'-module-cache-path',str(work/'module-cache')]
        expansion=run(common+['-typecheck','-Xfrontend','-dump-macro-expansions',str(owned)],30,environment)[1]
        names=re.findall(rb'^struct (\$s[A-Za-z0-9_$]{1,511}): DeveloperToolsSupport\.PreviewRegistry \{$',expansion,re.M)
        names=list(dict.fromkeys(name.decode('ascii') for name in names))
        if b'DeveloperToolsSupport.PreviewRegistry' in expansion and not names:
            raise ValueError('Unsupported compiler registry expansion format')
        if len(names)>64: raise ValueError('More than 64 preview registries')
        rows=[]
        if names:
            calls='\n'.join(f'  try record(`{name}`.self, "{name}")' for name in names)
            wrapper='''import SwiftUI
import DeveloperToolsSupport
import Foundation
@main struct Discovery {
 @MainActor static func main() throws {
  var rows=[[String:Any]]()
  func record<P: PreviewRegistry>(_ type: P.Type,_ identity:String) throws {
   let preview=try P.makePreview()
   let fields=Mirror(reflecting:preview).children
   guard let displayName=fields.first(where:{$0.label=="displayName"}) else {throw Failure.unsupportedPreviewShape}
   guard displayName.value is String? else {throw Failure.unsupportedPreviewShape}
   let name=(displayName.value as? String) as Any?
   rows.append(["registry":identity,"file_id":P.fileID,"line":P.line,"column":P.column,"display_name":name ?? NSNull()])
  }
__CALLS__
  print(String(data:try JSONSerialization.data(withJSONObject:rows,options:[.sortedKeys]),encoding:.utf8)!)
 }
 enum Failure:Error {case unsupportedPreviewShape}
}
'''.replace('__CALLS__',calls)
            (work/'Discovery.swift').write_text(wrapper)
            run(common+[str(owned),str(work/'Discovery.swift'),'-o',str(work/'discover')],30,environment)
            result=run([str(work/'discover')],runtime_seconds,environment)[0]
            rows=json.loads(result)
            if not isinstance(rows,list) or len(rows)!=len(names): raise ValueError('Unexpected registry result count')
            for name,row in zip(names,rows):
                if row.get('registry')!=name or not isinstance(row.get('file_id'),str) or type(row.get('line')) is not int or row['line']<1 or type(row.get('column')) is not int or row['column']<1 or (row.get('display_name') is not None and not isinstance(row['display_name'],str)):
                    raise ValueError('Unexpected registry metadata')
    rows.sort(key=lambda row:(row['line'],row['column'],row['registry']))
    return {'source':str(path),'source_sha256':hashlib.sha256(data).hexdigest(),
            'compiler':compiler,'compiler_version':version,'deployment_target':target,
            'expansion_sha256':hashlib.sha256(expansion).hexdigest(),'previews':rows,
            'scope':'Actual generated registry constructors; stored view-body closures are not invoked. File IDs refer to the temporary compile module and Source.swift; line/column refer to the supplied source.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source');parser.add_argument('--runtime-seconds',type=float,default=8)
    args=parser.parse_args()
    try: print(json.dumps(discover(args.source,args.runtime_seconds),sort_keys=True))
    except (OSError,ValueError,RuntimeError,KeyError,TypeError) as error:
        print(str(error),file=sys.stderr);return 1
    return 0

if __name__=='__main__': sys.exit(main())
