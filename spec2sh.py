#!/usr/bin/env python3
"""Simple SPEC speccmds.cmd to bash script converter"""
"""
# To run specmds
python3 speccmds.cmd run.sh
./run.sh
"""

import os
import sys

VTUNE_CMD = (
    'export HAWKEYE=/opt/intel/oneapi/vtune/2025.4/bin64/vtune\n'
    '$HAWKEYE -collect uarch-exploration -knob sampling-interval=2ms --finalization-mode=full --result-dir="runname" '
)

def convert_speccmds_to_bash(input_file, output_file, vtune=False):
    """Convert speccmds.cmd to bash script"""
    with open(input_file, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    bash_lines = [
        "#!/bin/bash",
        f"# Generated from {input_file}",
        "",
        "# Set default SPECCOPYNUM if not set", 
        "export SPECCOPYNUM=${SPECCOPYNUM:-0}",
        ""
    ]
    
    current_output = None
    current_error = None
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("-E "):
            parts = line[3:].split(' ', 1)
            if len(parts) >= 2:
                var_name, var_value = parts[0], parts[1]
                if "BASH_FUNC_" in var_name:
                    bash_lines.append(f"# Skipped bash function: {var_name}")
                else:
                    bash_lines.append(f'export {var_name}="{var_value}"')
        elif line.startswith("-C "):
            directory = line[3:].strip()
            bash_lines.extend(["", f"cd '{directory}'"])
        elif line.startswith("-o "):
            parts = line[3:].split()
            current_output = parts[0] if parts else None
            rest_of_line = ' '.join(parts[1:]) if len(parts) > 1 else ""
            if rest_of_line:
                if rest_of_line.startswith("-e "):
                    e_parts = rest_of_line[3:].split()
                    current_error = e_parts[0] if e_parts else None
                    command_parts = e_parts[1:] if len(e_parts) > 1 else []
                    full_command = ' '.join(command_parts)
                else:
                    full_command = rest_of_line
                # Always emit command, not just for specific keywords
                if full_command:
                    bash_lines.extend(["", "# Execute command"])
                    if vtune:
                        bash_lines.append(VTUNE_CMD)
                    cmd = full_command
                    if current_output:
                        cmd += f" > '{current_output}'"
                    if current_error:
                        cmd += f" 2> '{current_error}'"
                    bash_lines.append(cmd)
                    current_output = current_error = None
        elif line.startswith("-e "):
            current_error = line[3:].split()[0]
        elif line and not line.startswith("-"):
            # If previous -o/-e, treat this as the command
            if current_output or current_error:
                bash_lines.extend(["", "# Execute command"])
                if vtune:
                    bash_lines.append(VTUNE_CMD)
                cmd = line
                if current_output:
                    cmd += f" > '{current_output}'"
                if current_error:
                    cmd += f" 2> '{current_error}'"
                bash_lines.append(cmd)
                current_output = current_error = None
        elif line.startswith("-N "):
            bash_lines.append(f"# {line[3:].strip()}")
        elif line.startswith("-"):
            option = line.split()[0] if line.split() else line
            bash_lines.extend([
                f"# WARNING: Unhandled option '{option}' - may need implementation",
                f"# Original line: {line}"
            ])
        i += 1
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(bash_lines))
    
    os.chmod(output_file, 0o755)
    print(f"Converted {input_file} -> {output_file}")
    print(f"Generated {len(bash_lines)} lines")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 spec2sh.py <input_file> [output_file] [-vtune]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = None
    vtune = False
    for arg in sys.argv[2:]:
        if arg == "-vtune":
            vtune = True
        elif output_file is None:
            output_file = arg
    if output_file is None:
        output_file = input_file.replace('.cmd', '.sh').replace('speccmds', 'run')
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    try:
        convert_speccmds_to_bash(input_file, output_file, vtune=vtune)
        print(f"Success! Run with: ./{output_file}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
