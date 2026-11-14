"""Explicit local project source binding; never writes or runs the application's entry point."""
from pathlib import Path
import json,re


def code_mask(text):
    """Mask Swift comments/string literals while preserving offsets and line breaks."""
    chars=list(text);i=0;n=len(text)
    def hide(a,b):
        for k in range(a,b):
            if chars[k] not in '\r\n':chars[k]=' '
    while i<n:
        if text.startswith('//',i):
            end=text.find('\n',i);end=n if end<0 else end;hide(i,end);i=end
        elif text.startswith('/*',i):
            start=i;i+=2;depth=1
            while i<n and depth:
                if text.startswith('/*',i):depth+=1;i+=2
                elif text.startswith('*/',i):depth-=1;i+=2
                else:i+=1
            hide(start,i)
        else:
            start=i;hashes=0
            while i<n and text[i]=='#':hashes+=1;i+=1
            if i<n and text[i]=='"':
                quote='"""' if text.startswith('"""',i) else '"';end_token=quote+'#'*hashes;i+=len(quote)
                while i<n:
                    if text.startswith(end_token,i):i+=len(end_token);break
                    if text[i]=='\\' and hashes==0:i+=2
                    else:i+=1
                hide(start,min(i,n))
            else:i=max(start+1,i)
    return ''.join(chars)


def preview_snapshot(text):
    """Remove only real @main attributes from the owned compilation snapshot."""
    masked=code_mask(text);out=list(text);count=0
    for match in re.finditer(r'@main\b',masked):
        out[match.start():match.end()]=' '*len(match.group());count+=1
    return ''.join(out),count


def jsonc(text):
    # Xcode 27's supplied project.xcproj uses trailing commas. Preserve strings.
    out=[];i=0;quoted=False;escaped=False
    while i<len(text):
        c=text[i]
        if quoted:
            out.append(c)
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c=='"':quoted=False
        elif c=='"':quoted=True;out.append(c)
        elif c==',':
            j=i+1
            while j<len(text) and text[j].isspace():j+=1
            if j>=len(text) or text[j] not in ']}':out.append(c)
        else:out.append(c)
        i+=1
    return json.loads(''.join(out))


def resolve_source(path,factory,target=None):
    path=Path(path).resolve(strict=True)
    if path.is_file():return path,[],None
    manifest=path/'project.xcproj'
    if path.suffix!='.xcodeproj' or not manifest.is_file():
        raise ValueError('Choose a Swift source file or an Xcode 27 project.xcproj package; legacy project binding is not implemented')
    value=jsonc(manifest.read_text());targets=value.get('targets',[])
    candidates=[t for t in targets if target is None or t.get('name')==target]
    if len(candidates)!=1:raise ValueError('Choose one project target with --target')
    selected=candidates[0];root=path.parent;files=[]
    def walk(items):
        for item in items:
            if item.get('kind')=='group':walk(item.get('children',[]));continue
            if selected['name'] not in item.get('target-membership',[]):continue
            relative=item.get('path','');folder=(root/relative).resolve()
            if not folder.is_relative_to(root):raise ValueError('External project source roots require explicit integration')
            paths=folder.rglob('*.swift') if folder.is_dir() else [folder]
            for source in paths:
                if source.suffix=='.swift' and not any(part.startswith('.') for part in source.relative_to(root).parts):
                    real=source.resolve()
                    if not real.is_relative_to(root):raise ValueError('External source symlink rejected')
                    files.append(real)
    walk(value.get('files',[]));files=sorted(set(files))
    if not files or len(files)>128:raise ValueError('Project must contain 1–128 explicit local Swift source files')
    matches=[p for p in files if re.search(r'\bfunc\s+'+re.escape(factory)+r'\s*\(',code_mask(p.read_text()))]
    if len(matches)!=1:raise ValueError('Expected one factory '+factory+' in selected target sources')
    primary=matches[0];settings={**value.get('build-settings',{}),**selected.get('build-settings',{})}
    return primary,[p for p in files if p!=primary],{'name':path.stem,'target':selected['name'],'format':'project.xcproj',
        'manifest':str(manifest),'swift_version':str(settings.get('SWIFT_VERSION','5')).split('.')[0],
        'default_isolation':settings.get('SWIFT_DEFAULT_ACTOR_ISOLATION'),
        'scope':'Local target Swift sources and selected language/isolation settings. Package dependencies, assets, entitlements and non-Mac destination semantics remain pending.'}
