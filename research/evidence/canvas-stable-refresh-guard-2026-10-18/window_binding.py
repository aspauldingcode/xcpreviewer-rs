"""Bind trusted CUA workspace/source observations to an exact broker tab.

This verifies a documented observation record, not authenticity of arbitrary AX
text or freshness of later UI indices. It never delivers input.
"""
import re
from pathlib import Path
from urllib.parse import urlsplit,unquote
from bindings import owned_tab

def bind(ax,windows,project,source):
 if type(ax) is not str or len(ax)>262144:raise ValueError('AX shape')
 roots=re.findall(r'^0 standard window .+, ID: Xcode\.WorkspaceWindow, Secondary Actions: Raise, URL: (\S+)$',ax,re.M)
 if len(roots)!=1:raise ValueError('workspace root')
 url=urlsplit(roots[0]);path=Path(unquote(url.path))
 if url.scheme!='file' or url.netloc or url.query or url.fragment or not path.is_absolute() or path.resolve()!=Path(source).resolve():raise ValueError('source URL')
 projects=re.findall(r'^\t1 split group PreviewLab\.xcodeproj, ID: Workspace window tab content, Description: (.+)$',ax,re.M)
 if len(projects)!=1 or Path(projects[0]).resolve()!=Path(project).resolve():raise ValueError('workspace description')
 closes=re.findall(r'^\t(\d+) close button$',ax,re.M)
 if len(closes)!=1:raise ValueError('close binding')
 return {'tab':owned_tab(windows,project),'close_index':int(closes[0]),'source':str(path.resolve()),'project':str(Path(project).resolve())}
