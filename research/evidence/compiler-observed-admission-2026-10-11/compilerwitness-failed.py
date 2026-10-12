"""Read-only explicit compiler ancestry witness; not arbitrary process ownership."""
class CompilerWitness:
    def __init__(self, observer):
        if not callable(observer):raise ValueError('Compiler observer must be callable')
        self.observer=observer;self.known={};self.samples=0
    def sample(self, roots):
        self.samples+=1
        if self.samples>64:raise RuntimeError('Compiler observation budget exceeded')
        rows=self.observer(set(roots),dict(self.known))
        if type(rows) is not dict or len(rows)>1024:raise ValueError('Invalid compiler observation')
        for pid,row in rows.items():
            identity=row['identity']
            if (type(pid) is not int or not 0<pid<=2147483647 or len(identity)!=3
                or any(type(x) is not int or x<0 for x in identity[:2])
                or type(identity[2]) is not str or not identity[2].startswith('/')
                or any(type(row[k]) is not int or row[k]<0 for k in ['parent','group'])
                or row['state'] not in ['L','Z']):raise ValueError('Invalid compiler lifetime identity')
            if pid in self.known and tuple(identity)!=self.known[pid]:raise RuntimeError('Compiler observed lifetime identity changed')
        owned={pid for pid in roots if pid in rows}
        owned.update(pid for pid,identity in self.known.items() if pid in rows and tuple(rows[pid]['identity'])==identity)
        while True:
            children={pid for pid,row in rows.items() if row['parent'] in owned}
            if children<=owned:break
            owned.update(children)
        for pid in owned:self.known[pid]=tuple(rows[pid]['identity'])
        return rows
    def admit(self, root):
        rows=self.sample(set())
        if root not in self.known:raise RuntimeError('Compiler root lifetime was not observed')
        if any(pid!=root and pid in rows and tuple(rows[pid]['identity'])==identity and rows[pid]['state']!='Z' for pid,identity in self.known.items()):
            raise RuntimeError('Observed compiler descendants remain after successful root exit')
