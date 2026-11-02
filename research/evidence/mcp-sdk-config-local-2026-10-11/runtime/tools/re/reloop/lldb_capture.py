"""Imported inside LLDB; collects owned tick stops without guessing Swift ABI."""
import json
import pathlib
import time
import lldb


def capture(debugger,command,result,internal_dict):
    out=pathlib.Path(command.strip());out.mkdir(parents=True,exist_ok=True)
    target=debugger.GetSelectedTarget()
    breakpoint=target.BreakpointCreateByName('preview_probe_tick')
    debugger.SetAsync(False)
    launch=lldb.SBLaunchInfo(None)
    launch.SetLaunchFlags(launch.GetLaunchFlags() & ~lldb.eLaunchFlagDisableASLR)
    launch.AddOpenFileAction(1,str(out/'target.stdout'),False,True)
    launch.AddOpenFileAction(2,str(out/'target.stderr'),False,True)
    error=lldb.SBError();process=target.Launch(launch,error)
    events=[]
    try:
        if not error.Success(): raise RuntimeError(error.GetCString())
        deadline=time.monotonic()+20
        while process.GetState() not in [lldb.eStateExited,lldb.eStateCrashed,lldb.eStateDetached] and time.monotonic()<deadline:
            if process.GetState()==lldb.eStateStopped:
                for thread in process:
                    if thread.GetStopReason()!=lldb.eStopReasonBreakpoint:continue
                    if thread.GetStopReasonDataAtIndex(0)!=breakpoint.GetID():continue
                    frame=thread.GetFrameAtIndex(0);address=frame.GetPCAddress();module=address.GetModule()
                    value=frame.FindVariable('value')
                    events.append({'function':frame.GetFunctionName(),'input':value.GetValueAsSigned() if value.IsValid() else None,
                                   'thread':thread.GetThreadID(),'file_address':address.GetFileAddress(),
                                   'module_uuid':module.GetUUIDString(),'module':str(module.GetFileSpec())})
                process.Continue()
            else: time.sleep(.01)
        output={'breakpoint_locations':breakpoint.GetNumLocations(),'events':events,'exit_status':process.GetExitStatus(),
                'completed':process.GetState()==lldb.eStateExited}
        (out/'capture.json').write_text(json.dumps(output,indent=2)+'\n')
        result.AppendMessage(json.dumps({'events':len(events),'completed':output['completed']}))
    except Exception as error: result.SetError(str(error))
    finally:
        if process.IsValid() and process.GetState() not in [lldb.eStateExited,lldb.eStateDetached]:process.Kill()


def __lldb_init_module(debugger,internal_dict):
    debugger.HandleCommand('command script add -f lldb_capture.capture re-capture')
