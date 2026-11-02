"""Refresh aggregate milestone counts; never export issue bodies or credentials."""
import argparse, datetime, json, os, subprocess, urllib.request
from pathlib import Path
REPO='aspauldingcode/xcpreviewer-rs'
def fetch(path):
 token=os.environ.get('GITHUB_TOKEN')
 if token:
  req=urllib.request.Request('https://api.github.com/'+path,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
  with urllib.request.urlopen(req,timeout=20) as response:return json.load(response)
 return json.loads(subprocess.run(['gh','api',path],capture_output=True,text=True,check=True,timeout=25).stdout)
def main():
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=Path(__file__).with_name('status.json'));p.add_argument('--output',type=Path);a=p.parse_args();d=json.loads(a.input.read_text());issues=[]
 for page in range(1,101):
  rows=fetch(f'repos/{REPO}/issues?state=all&per_page=100&page={page}')
  issues.extend(x for x in rows if 'pull_request' not in x)
  if len(rows)<100:break
 else:raise RuntimeError('Issue pagination exceeded bound')
 for milestone in d['milestones']:
  rows=[x for x in issues if (x.get('milestone') or {}).get('number')==milestone['number']]
  if not rows:raise RuntimeError('Milestone has no tracked issues')
  milestone['total_issues']=len(rows);milestone['closed_issues']=sum(x['state']=='closed' for x in rows)
 d['issue_counts_updated_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 (a.output or a.input).write_text(json.dumps(d,indent=2)+'\n')
 print(json.dumps({'milestones':[{'number':x['number'],'closed':x['closed_issues'],'total':x['total_issues']} for x in d['milestones']]}))
if __name__=='__main__':main()
