"""Exact owned workspace and MCP success binding for research captures."""
import json,re
from pathlib import Path

def payload(value):
 if type(value) is not dict:raise ValueError('MCP response object required')
 if 'isError' in value and value['isError'] is not False:raise ValueError('MCP tool error')
 data=value.get('structuredContent')
 if data is None:
  content=value.get('content')
  if type(content) is not list or len(content)!=1 or content[0].get('type')!='text':raise ValueError('MCP text content')
  data=json.loads(content[0]['text'])
 if type(data) is not dict:raise ValueError('MCP payload object required')
 return data

def owned_tab(value,project):
 data=payload(value);message=data.get('message')
 if type(message) is not str or len(message)>262144:raise ValueError('window message')
 expected=Path(project).resolve();tabs=[]
 for line in message.splitlines():
  match=re.fullmatch(r'\* tabIdentifier: ([A-Za-z0-9_-]+), workspacePath: (.+)',line)
  if not match:continue
  tab,path=match.groups();path=Path(path)
  if path.is_absolute() and path.resolve()==expected:tabs.append(tab)
 if len(tabs)!=1:raise ValueError('owned workspace binding ambiguous or absent')
 return tabs[0]
