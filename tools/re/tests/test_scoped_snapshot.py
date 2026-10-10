import subprocess
import unittest
from unittest.mock import patch
from reloop.processes import snapshot

START=('Sat','Oct','10','12:00:00','2026')
class ScopedSnapshotTests(unittest.TestCase):
    def test_only_owned_ancestry_and_matching_detached_start_queried(self):
        inventory='100 1 100 S Sat Oct 10 12:00:00 2026\n101 100 101 S Sat Oct 10 12:00:00 2026\n102 1 102 S Sat Oct 10 12:00:00 2026\n103 1 103 S Sat Oct 10 12:01:00 2026\n999 1 999 S Sat Oct 10 12:00:00 2026\n'
        commands='100 Sat Oct 10 12:00:00 2026 owned root\n101 Sat Oct 10 12:00:00 2026 owned child\n102 Sat Oct 10 12:00:00 2026 detached child\n'
        results=[subprocess.CompletedProcess([],0,inventory,''),subprocess.CompletedProcess([],0,commands,'')]
        with patch('reloop.processes.subprocess.run',side_effect=results) as run:
            rows=snapshot({100},{102:START+('detached child',),103:START+('old PID',)})
        self.assertEqual(set(rows),{100,101,102})
        self.assertEqual(run.call_args_list[1].args[0][2],'100,101,102')
        self.assertEqual(rows[102]['identity'],START+('detached child',))
        self.assertNotIn('command=',run.call_args_list[0].args[0][-1])
        self.assertTrue(all(c.kwargs['timeout']==2 for c in run.call_args_list))
    def test_changed_start_between_reads_and_vanished_pid_rejected(self):
        inventory='100 1 100 S Sat Oct 10 12:00:00 2026\n101 100 101 S Sat Oct 10 12:00:00 2026\n'
        commands='100 Sat Oct 10 12:01:00 2026 replacement\n'
        with patch('reloop.processes.subprocess.run',side_effect=[subprocess.CompletedProcess([],0,inventory,''),subprocess.CompletedProcess([],1,commands,'')]):
            self.assertEqual(snapshot({100}),{})
