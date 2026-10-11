// Decompile explicitly selected addresses; output remains local research data.
//@category PreviewResearch
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import java.nio.file.Files;
import java.nio.file.Paths;

public class DumpPreviewFunctions extends GhidraScript {
    @Override public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) throw new IllegalArgumentException("output-file address [address ...]");
        DecompInterface decompiler = new DecompInterface();
        StringBuilder output = new StringBuilder("Program: " + currentProgram.getName() + "\nLanguage: " + currentProgram.getLanguageID() + "\n");
        try {
            if (!decompiler.openProgram(currentProgram)) throw new IllegalStateException(decompiler.getLastMessage());
            for (int i = 1; i < args.length; ++i) {
                Address address = toAddr(args[i]);
                Function function = getFunctionAt(address);
                if (function == null) function = createFunction(address, null);
                output.append("\nAddress: ").append(address).append("\n");
                if (function == null) { output.append("NO FUNCTION\n"); continue; }
                output.append("Symbol: ").append(function.getName()).append("\n");
                DecompileResults result = decompiler.decompileFunction(function, 60, monitor);
                output.append(result.decompileCompleted() ? result.getDecompiledFunction().getC() : "FAILED: " + result.getErrorMessage());
            }
            Files.writeString(Paths.get(args[0]), output.toString());
        } finally { decompiler.dispose(); }
    }
}
