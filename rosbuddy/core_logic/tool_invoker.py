# rosbuddy/core_logic/tool_invoker.py
import subprocess
import os
import pathlib
import shutil
from typing import Tuple, Optional, List, Dict, Callable
import shlex
import tempfile
import select 

ROS2_DISTRO_SETUP_BASH = "/opt/ros/humble/setup.bash" 

class ToolInvoker:
    def __init__(self, workspace_manager: 'WorkspaceManager'):
        self.workspace_manager = workspace_manager
        self.bash_executable = shutil.which("bash")
        if not self.bash_executable:
            print("WARNING: 'bash' executable not found.")

    # Modified to return (success, full_stdout, full_stderr, process_obj)
    def _execute_bash_c_script(self, 
                               script_content: str, 
                               cwd: Optional[str] = None,
                               realtime_output_callback: Optional[Callable[[str], None]] = None,
                               process_started_callback: Optional[Callable[[subprocess.Popen], None]] = None
                               ) -> Tuple[bool, str, str, Optional[subprocess.Popen]]: # Return process object
        if not self.bash_executable:
            return False, "", "Bash executable not found", None

        cmd_list_for_popen = [self.bash_executable, "-c", script_content]
        
        full_stdout_capture = []
        full_stderr_capture = []
        process = None
        try:
            effective_env = os.environ.copy()
            print(f"Executing script via bash -c:\n------ SCRIPT BEGIN ------\n{script_content}\n------ SCRIPT END ------")
            if cwd: print(f"In CWD: {cwd}")

            process = subprocess.Popen(
                cmd_list_for_popen, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                bufsize=1, 
                cwd=cwd, 
                env=effective_env
            )

            if process and process_started_callback:
                try:
                    process_started_callback(process)
                except Exception as e_cb:
                    print(f"[TOOL_INVOKER_ERROR] Error in process_started_callback: {e_cb}")

            if realtime_output_callback:
                try:
                    stdout_fd = process.stdout.fileno()
                    stderr_fd = process.stderr.fileno()
                    os.set_blocking(stdout_fd, False)
                    os.set_blocking(stderr_fd, False)
                    
                    while True: 
                        if process.poll() is not None: break
                        ready_to_read, _, _ = select.select([process.stdout, process.stderr], [], [], 0.1)
                        if not ready_to_read and process.poll() is not None: break
                        for pipe_obj in ready_to_read: 
                            try:
                                data = os.read(pipe_obj.fileno(), 4096)
                                if data:
                                    text_data = data.decode('utf-8', errors='replace')
                                    for line in text_data.splitlines():
                                        stripped_line = line.strip()
                                        if stripped_line:
                                            if pipe_obj == process.stdout:
                                                full_stdout_capture.append(stripped_line)
                                                realtime_output_callback(f"[OUT] {stripped_line}")
                                            elif pipe_obj == process.stderr:
                                                full_stderr_capture.append(stripped_line)
                                                realtime_output_callback(f"[ERR] {stripped_line}")
                                elif process.poll() is not None: break 
                            except BlockingIOError: pass 
                            except Exception as e_read: print(f"Error reading pipe: {e_read}"); break 
                        if process.poll() is not None: break 
                except (AttributeError, ValueError, OSError) as e_select: 
                     print(f"Warning: Could not use select for real-time output (Error: {e_select}). Falling back to communicate().")
                     if process and process.poll() is None: stdout_fb, stderr_fb = process.communicate() 
                     else: stdout_fb, stderr_fb = (process.stdout.read() if process and process.stdout else ""), (process.stderr.read() if process and process.stderr else "")
                     if stdout_fb: 
                         for line in (stdout_fb if isinstance(stdout_fb, str) else stdout_fb.decode('utf-8', errors='replace')).strip().split('\n'): 
                            if line.strip(): full_stdout_capture.append(line.strip()); realtime_output_callback(f"[OUT] {line.strip()}")
                     if stderr_fb: 
                         for line in (stderr_fb if isinstance(stderr_fb, str) else stderr_fb.decode('utf-8', errors='replace')).strip().split('\n'): 
                            if line.strip(): full_stderr_capture.append(line.strip()); realtime_output_callback(f"[ERR] {line.strip()}")
                
                if process.stdout: 
                    for line in process.stdout.readlines(): 
                        stripped_line = line.strip(); 
                        if stripped_line and stripped_line not in full_stdout_capture : full_stdout_capture.append(stripped_line); realtime_output_callback(f"[OUT] {stripped_line}")
                if process.stderr: 
                    for line in process.stderr.readlines():
                        stripped_line = line.strip(); 
                        if stripped_line and stripped_line not in full_stderr_capture : full_stderr_capture.append(stripped_line); realtime_output_callback(f"[ERR] {stripped_line}")
            else: 
                stdout_full_block, stderr_full_block = process.communicate()
                if stdout_full_block: full_stdout_capture.extend(filter(None,stdout_full_block.strip().split('\n')))
                if stderr_full_block: full_stderr_capture.extend(filter(None,stderr_full_block.strip().split('\n')))

            if process.returncode is None: process.wait()
            retcode = process.returncode

            if retcode == 0: 
                print("Command executed successfully.")
                return True, "\n".join(full_stdout_capture), "\n".join(full_stderr_capture), process
            else: 
                print(f"Command failed with exit code {retcode}.")
                return False, "\n".join(full_stdout_capture), "\n".join(full_stderr_capture), process

        except FileNotFoundError:
             err_msg = f"Error: Bash executable not found: {self.bash_executable}"; print(err_msg); return False, "", err_msg, None
        except Exception as e: 
            err_msg = f"Error in _execute_bash_c_script: {e}"; print(err_msg); import traceback; traceback.print_exc()
            return False, "", "\n".join(full_stderr_capture) + f"\nException: {str(e)}", None 
        finally:
            # We don't terminate/kill here if 'process' is the main process we want to return.
            # The caller of this method (Worker) will be responsible for handling process termination.
            pass


    # _construct_simple_sourced_script is the same as before
    def _construct_simple_sourced_script(self, command_to_execute: str, include_pre_command_debug: bool = False) -> str:
        script_lines = ["set -e"]
        if os.path.exists(ROS2_DISTRO_SETUP_BASH):
            script_lines.append(f"source {shlex.quote(ROS2_DISTRO_SETUP_BASH)}")
        else:
            print(f"WARNING (build/clean): ROS 2 distro setup file not found: {ROS2_DISTRO_SETUP_BASH}")
        
        if include_pre_command_debug:
            script_lines.append("echo '[INFO] Current directory (colcon build): $(pwd)'")
            script_lines.append("echo '[INFO] colcon list before build:'")
            script_lines.append("colcon list --paths src/* || echo '[INFO] colcon list pre-build failed or no packages'")
        
        script_lines.append(f"exec {command_to_execute}") 
        return "\n".join(script_lines)

    # Modified to return (success, full_stdout, full_stderr, process_obj)
    def _run_command_via_wrapper_script(self, 
                                       command_parts_to_exec: List[str], 
                                       cwd: Optional[str] = None,
                                       realtime_output_callback: Optional[Callable[[str], None]] = None,
                                       process_started_callback: Optional[Callable[[subprocess.Popen], None]] = None
                                       ) -> Tuple[bool, str, str, Optional[subprocess.Popen]]: # Return process object
        if not self.bash_executable:
            return False, "", "Bash executable not found.", None

        script_lines = [
            "#!/usr/bin/env bash", 
            "echo '[WRAPPER_INFO] Script started.'", 
            "set -e"
        ]
        script_lines.append("echo '[WRAPPER_INFO] Initial AMENT_PREFIX_PATH (before any sourcing): $AMENT_PREFIX_PATH'")

        if os.path.exists(ROS2_DISTRO_SETUP_BASH):
            script_lines.append(f"echo '[WRAPPER_INFO] Sourcing ROS_DISTRO: {ROS2_DISTRO_SETUP_BASH}'")
            script_lines.append(f"source {shlex.quote(ROS2_DISTRO_SETUP_BASH)}")
            script_lines.append("echo '[WRAPPER_INFO] After ROS_DISTRO source, AMENT_PREFIX_PATH: $AMENT_PREFIX_PATH'")
        else: 
            script_lines.append(f"echo '[WRAPPER_INFO] WARNING: ROS 2 distro setup file not found: {ROS2_DISTRO_SETUP_BASH}'")
        
        active_ws_path = self.workspace_manager.get_active_workspace_path()
        if active_ws_path:
            ws_install_script = active_ws_path / "install" / "setup.sh"
            if not ws_install_script.exists(): ws_install_script = active_ws_path / "install" / "setup.bash" # Fallback
            if ws_install_script.exists():
                script_lines.extend([f"echo '[WRAPPER_INFO] Sourcing WORKSPACE: {str(ws_install_script)}'", f"source {shlex.quote(str(ws_install_script))}", "echo '[WRAPPER_INFO] After WORKSPACE source, AMENT_PREFIX_PATH: $AMENT_PREFIX_PATH'"])
            else: script_lines.append(f"echo '[WRAPPER_INFO] WARNING: Workspace install script not found in {active_ws_path / 'install'}'")
        else: script_lines.append("echo '[WRAPPER_INFO] WARNING: No active ROSBuddy workspace for sourcing install setup.'")
        
        script_lines.extend(["echo '[WRAPPER_INFO] Environment variables just before exec:'", "echo \"[WRAPPER_ENV_INFO] AMENT_PREFIX_PATH=$AMENT_PREFIX_PATH\""])
        exec_command_str = shlex.join(command_parts_to_exec) 
        script_lines.extend([f"echo '[WRAPPER_INFO] Executing: {exec_command_str}'", f"exec {exec_command_str}"])
        full_script_content = "\n".join(script_lines)
        
        full_stdout_capture = []
        full_stderr_capture = []
        process = None
        script_path_obj = None

        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sh", prefix="rosbuddy_wrapper_") as tmp_script:
                tmp_script.write(full_script_content)
                script_path_obj = pathlib.Path(tmp_script.name)
            script_path_obj.chmod(0o755) 

            print(f"Executing wrapper script: {script_path_obj}")
            if cwd: print(f"In CWD: {cwd}")

            process = subprocess.Popen(
                [str(script_path_obj)], 
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, cwd=cwd, env=os.environ.copy()
            )

            if process and process_started_callback:
                try:
                    process_started_callback(process)
                except Exception as e_cb:
                    print(f"[TOOL_INVOKER_ERROR] Error in process_started_callback: {e_cb}")

            if realtime_output_callback:
                try:
                    stdout_fd = process.stdout.fileno()
                    stderr_fd = process.stderr.fileno()
                    os.set_blocking(stdout_fd, False)
                    os.set_blocking(stderr_fd, False)
                    while True: 
                        if process.poll() is not None: break
                        ready_to_read, _, _ = select.select([process.stdout, process.stderr], [], [], 0.1)
                        if not ready_to_read and process.poll() is not None: break
                        for pipe_obj in ready_to_read: 
                            try:
                                data = os.read(pipe_obj.fileno(), 4096)
                                if data:
                                    text_data = data.decode('utf-8', errors='replace')
                                    for line in text_data.splitlines(): 
                                        stripped_line = line.strip()
                                        if stripped_line:
                                            if pipe_obj == process.stdout: full_stdout_capture.append(stripped_line); realtime_output_callback(f"[OUT] {stripped_line}")
                                            elif pipe_obj == process.stderr: full_stderr_capture.append(stripped_line); realtime_output_callback(f"[ERR] {stripped_line}")
                                elif process.poll() is not None: break 
                            except BlockingIOError: pass
                            except Exception as e_read: print(f"Error reading pipe: {e_read}"); break 
                        if process.poll() is not None: break 
                except (AttributeError, ValueError, OSError) as e_sel: 
                    print(f"Warning: Select loop issue (wrapper): {e_sel}. Falling back to communicate().")
                    if process and process.poll() is None: stdout_fb, stderr_fb = process.communicate()
                    else: stdout_fb, stderr_fb = (process.stdout.read() if process and process.stdout else ""), (process.stderr.read() if process and process.stderr else "")
                    if stdout_fb: 
                        for line in (stdout_fb if isinstance(stdout_fb, str) else stdout_fb.decode('utf-8', errors='replace')).strip().split('\n'): 
                            if line.strip(): full_stdout_capture.append(line.strip()); realtime_output_callback(f"[OUT] {line.strip()}")
                    if stderr_fb: 
                        for line in (stderr_fb if isinstance(stderr_fb, str) else stderr_fb.decode('utf-8', errors='replace')).strip().split('\n'): 
                            if line.strip(): full_stderr_capture.append(line.strip()); realtime_output_callback(f"[ERR] {line.strip()}")
                
                if process.stdout: 
                    for line in process.stdout.readlines(): 
                        stripped_line = line.strip(); 
                        if stripped_line and stripped_line not in full_stdout_capture : full_stdout_capture.append(stripped_line); realtime_output_callback(f"[OUT] {stripped_line}")
                if process.stderr: 
                    for line in process.stderr.readlines():
                        stripped_line = line.strip(); 
                        if stripped_line and stripped_line not in full_stderr_capture : full_stderr_capture.append(stripped_line); realtime_output_callback(f"[ERR] {stripped_line}")
            else: 
                stdout_full_block, stderr_full_block = process.communicate()
                if stdout_full_block: full_stdout_capture.extend(filter(None, stdout_full_block.strip().split('\n')))
                if stderr_full_block: full_stderr_capture.extend(filter(None, stderr_full_block.strip().split('\n')))
            
            if process.returncode is None: process.wait()
            retcode = process.returncode
            if retcode == 0: 
                print(f"Command ({command_parts_to_exec[0]}) executed successfully via wrapper.")
                return True, "\n".join(full_stdout_capture), "\n".join(full_stderr_capture), process # Return process object
            else: 
                print(f"Command ({command_parts_to_exec[0]}) failed (via wrapper) with exit code {retcode}.")
                return False, "\n".join(full_stdout_capture), "\n".join(full_stderr_capture), process # Return process object
        except Exception as e:
            err_msg = f"An error occurred with wrapper script for {command_parts_to_exec[0]}: {e}"; print(err_msg)
            import traceback; traceback.print_exc()
            return False, "\n".join(full_stdout_capture), "\n".join(full_stderr_capture) + f"\nException: {e}", None # Return None for process on exception
        finally:
            # We do NOT terminate/kill here. The caller (Worker) will be responsible for this process.
            if script_path_obj and script_path_obj.exists():
                try: script_path_obj.unlink() # Clean up temp script
                except Exception as e_unlink: print(f"Error unlinking temp script {script_path_obj}: {e_unlink}")

    # Public Methods
    def colcon_build(self, package_name: Optional[str] = None, realtime_output_callback: Optional[Callable[[str], None]] = None, process_started_callback: Optional[Callable[[subprocess.Popen], None]] = None) -> Tuple[bool, str, str]:
        active_ws_path = self.workspace_manager.get_active_workspace_path()
        if not active_ws_path: return False, "", "No active workspace."
        if not self.bash_executable: return False, "", "Bash not found."
        
        script_lines = ["set -e"]
        if os.path.exists(ROS2_DISTRO_SETUP_BASH):
            script_lines.append(f"source {shlex.quote(ROS2_DISTRO_SETUP_BASH)}")
        
        # Pre-build debug
        script_lines.append("echo '[INFO] Current directory (colcon build): $(pwd)'")
        script_lines.append("echo '[INFO] colcon list before build:'")
        script_lines.append("colcon list --paths src/* || echo '[INFO] colcon list pre-build failed or no packages'")

        actual_cmd = "colcon build --event-handlers \"console_direct+\""
        script_lines.append(f"exec {actual_cmd}")
        full_script_content = "\n".join(script_lines)
        
        print(f"DEBUG: Full script for colcon build:\n{full_script_content}")
        success, stdout, stderr, _ = self._execute_bash_c_script(full_script_content, cwd=str(active_ws_path), realtime_output_callback=realtime_output_callback, process_started_callback=process_started_callback)
        return success, stdout, stderr

    def colcon_clean(self, realtime_output_callback: Optional[Callable[[str], None]] = None, process_started_callback: Optional[Callable[[subprocess.Popen], None]] = None) -> Tuple[bool, str, str]:
        active_ws_path = self.workspace_manager.get_active_workspace_path()
        if not active_ws_path: return False, "", "No active workspace."
        # This will now use the manual clean method directly, not colcon clean via script
        # The logic is implemented directly in this method below
        
        print(f"Executing manual workspace clean...")
        
        dirs_to_remove_names = ["build", "install", "log"]
        all_removed_successfully = True
        stdout_log_lines = []
        stderr_log_lines = []

        if realtime_output_callback: realtime_output_callback("[INFO] Starting manual workspace clean...")
        stdout_log_lines.append("Starting manual workspace clean...")

        for dir_name in dirs_to_remove_names:
            dir_to_remove = active_ws_path / dir_name
            if dir_to_remove.exists():
                msg_info = f"Attempting to remove directory: {dir_to_remove}"
                if realtime_output_callback: realtime_output_callback(f"[INFO] {msg_info}")
                stdout_log_lines.append(msg_info)
                try:
                    shutil.rmtree(dir_to_remove)
                    msg_success = f"Successfully removed: {dir_to_remove}"
                    if realtime_output_callback: realtime_output_callback(f"[OUT] {msg_success}")
                    stdout_log_lines.append(msg_success)
                except OSError as e:
                    msg_err = f"Error removing directory {dir_to_remove}: {e}"
                    if realtime_output_callback: realtime_output_callback(f"[ERR] {msg_err}")
                    stderr_log_lines.append(msg_err)
                    all_removed_successfully = False
            else:
                msg_skip = f"Directory not found, skipping: {dir_to_remove}"
                if realtime_output_callback: realtime_output_callback(f"[INFO] {msg_skip}")
                stdout_log_lines.append(msg_skip)
        
        final_message = "Manual workspace clean completed."
        if not all_removed_successfully:
            final_message = "Manual workspace clean completed with errors."
        
        if realtime_output_callback: realtime_output_callback(f"[INFO] {final_message}")
        stdout_log_lines.append(final_message)
        
        return all_removed_successfully, "\n".join(stdout_log_lines), "\n".join(stderr_log_lines)

    def ros2_run(self, package_name: str, executable_name: str, args: Optional[List[str]] = None, 
                 cwd: Optional[str] = None, realtime_output_callback: Optional[Callable[[str], None]] = None,
                 process_started_callback: Optional[Callable[[subprocess.Popen], None]] = None
                 ) -> Tuple[bool, str, str, Optional[subprocess.Popen]]: # Return process object
        cmd_parts = ["ros2", "run", package_name, executable_name]
        if args: cmd_parts.extend(args)
        return self._run_command_via_wrapper_script(cmd_parts, cwd=cwd, 
                                                    realtime_output_callback=realtime_output_callback,
                                                    process_started_callback=process_started_callback)

    def ros2_launch(self, package_name: str, launch_file_name: str, args: Optional[List[str]] = None, 
                    cwd: Optional[str] = None, realtime_output_callback: Optional[Callable[[str], None]] = None,
                    process_started_callback: Optional[Callable[[subprocess.Popen], None]] = None
                    ) -> Tuple[bool, str, str, Optional[subprocess.Popen]]: # Return process object
        cmd_parts = ["ros2", "launch", package_name, launch_file_name]
        if args: cmd_parts.extend(args) 
        return self._run_command_via_wrapper_script(cmd_parts, cwd=cwd, 
                                                    realtime_output_callback=realtime_output_callback,
                                                    process_started_callback=process_started_callback)