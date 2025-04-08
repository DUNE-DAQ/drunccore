# Using the Unified Shell

## Jumpstart a run
To start the unified shell, you can use:
```bash
drunc-unified-shell ssh-standalone config/daqsystemtest/example-configs.data.xml local-1x1-config your-choice-of-session-name
```
Where:
 - `ssh-standalone` denotes the process manager configuration.
 - `config/daqsystemtest/example-configs.data.xml` is the name of the file on which the configuration is stored
 - `local-1x1-config` is the name of the `Session` object in the `xml` file above that you would like to use
 - `your-choice-of-session-name` is the name of the session you want to use (it's the name that will appear in operational monitoring for example).

After that you can, you are presented with a shell in which you can:
```bash
boot
```

That will start all the processes of the DAQ.

If everything goes well, you will get
```log
  Looking for root-controller on the connectivity service... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:00 0:00:06
⠋ Trying to talk to the controller...                                          -:--:-- 0:00:00
[2025/04/08 17:50:38] INFO       commands.py:79                 unified_shell.boot:                           Booted successfully
```

This means you are able to send command to the top controller, it doesn't mean that the system is full connected though, so you should issue a `status`:

```bash
drunc-unified-shell > status
                                       your-choice-of-session-name status
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name                   ┃ Info      ┃ State   ┃ Substate ┃ In error ┃ Included ┃ Endpoint                  ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ root-controller        │           │ initial │ initial  │ No       │ Yes      │ grpc://10.73.136.38:43493 │
│   df-controller        │           │ initial │ initial  │ No       │ Yes      │ grpc://10.73.136.38:34661 │
│     df-01              │           │ initial │ idle     │ No       │ Yes      │ rest://10.73.136.38:50703 │
│     dfo-01             │           │ initial │ idle     │ No       │ Yes      │ rest://10.73.136.38:36819 │
│     tp-stream-writer   │           │ initial │ idle     │ No       │ Yes      │ rest://10.73.136.38:58985 │
│   hsi-fake-controller  │           │ initial │ initial  │ No       │ Yes      │ grpc://10.73.136.38:36509 │
│     hsi-fake-01        │           │ initial │ idle     │ No       │ Yes      │ rest://10.73.136.38:46847 │
│     hsi-fake-to-tc-app │           │ initial │ idle     │ No       │ Yes      │ rest://10.73.136.38:44491 │
│   ru-controller        │           │ initial │ initial  │ No       │ Yes      │ grpc://10.73.136.38:38695 │
│     ru-01              │ conn apa1 │ initial │ idle     │ No       │ Yes      │ rest://10.73.136.38:46305 │
│   trg-controller       │           │ initial │ initial  │ No       │ Yes      │ grpc://10.73.136.38:35241 │
│     mlt                │           │ initial │ idle     │ No       │ Yes      │ rest://10.73.136.38:53607 │
│     tc-maker-1         │           │ initial │ idle     │ No       │ Yes      │ rest://10.73.136.38:40777 │
└────────────────────────┴───────────┴─────────┴──────────┴──────────┴──────────┴───────────────────────────┘
[2025/04/08 17:59:01] INFO       shell_utils.py:344             utils.ShellContext:                           Current FSM status is initial. Available transitions are conf.
```

As you can advertised, you can now issue `conf`, and if that works well, `start --run-number 1`, `enable-triggers`.

_Congratulation!_ You are writing data.

To stop the run, simply issue the following commands:
```bash
disable-triggers
drain-dataflow
stop-trigger-sources
stop
```


And, if you want to quit:
```bash
scrap
terminate
exit
```

That should bring you back to your shell.

## Unified Shell Reference
All the commands that are issued in the shell take a `--help` flag, you can also use tab completion.

### boot
#### Description
This command spawns the processes that are used by the DAQ. In most cases, it SSHes on the host where the process is supposed to run, and execute the `daq_application` or `drunc-controller` binary.

The `boot` command will check if there are processes running in the process manager with the same session name and ask for confirmation if it detects other process running under the same session name.

The `boot` command can take the following option:
 - `--override-logs/--no-override-logs` (optional), this flags adds a timestamp to the log files of the application, effectively making them non-overriding. Note this happens only in the case where the `log_path` is _not_ set in your configuration's `Session` or `Application` objects. If the configuration's `log_path` is not `./` in either of these, the run control will use that, and the log will not be overriding (in this case, _this flag is ignored_).

#### Example
```bash
boot --override-logs
```

#### Related commands
 - `kill`
 - `ps`

### change-rate
#### Description
**NOTE**: This command depends on your FSM configuration. If you don't use the standard FSM from the DAQ, you may not have it!

**NOTE**: This command requires you to have booted the system and to be connected to a controller.

This command allows you to change the trigger rate of the system, when it is `running` or `ready`, this command does not change the state of the system.

The `change-rate` command can take the following options:
 - `--trigger-rate` (mandatory), is a float to specify the trigger rate in Hz you want the system to be running at.
 - `--target` (optional), allows you to specify a target application/segment for the command. The command will only be run on that application or segment and children if you specify it. By default, the target is the top segment for the whole session.

#### Examples
To send `change-rate` to the whole of the DAQ:
```bash
change-rate --trigger-rate 0.01
```
To send `change-rate` to the whole trigger segment:
```bash
change-rate --trigger-rate 0.01 --target root-controller/trg-controller
```
To send `change-rate` to the MLT only:
```bash
change-rate --trigger-rate 0.01 --target root-controller/trg-controller/mlt
```

#### Related commands
 - `start`
 - `enable-triggers`
 - `disable-triggers`
 - `drain-dataflow`

### conf
#### Description
**NOTE**: This command depends on your FSM configuration. If you don't use the standard FSM from the DAQ, you may not have it!

**NOTE**: This command requires you to have booted the system and to be connected to a controller.

This command allows you to configure the system, when it is `initialised`, and thus to reach the `configured` state.

The `conf` command can take the following option:
 - `--target` (optional), allows you to specify a target application/segment for the command. The command will only be run on that application or segment and children if you specify it. By default, the target is the top segment for the whole session.

#### Examples
To send `conf` to the whole of the DAQ:
```bash
conf
```
To send `conf` to the whole trigger segment:
```bash
conf --target root-controller/trg-controller
```
To send `conf` to the MLT only:
```bash
conf --target root-controller/trg-controller/mlt
```

#### Related commands
 - `scrap`
 - `start`

### connect
#### Description
This command is used to connect the shell to a controller.

The `connect` command takes the control address of the controller as argument

If you are already connected to a controller, you will be asked to confirm that you want to connect to another controller.

The `connect` command take the following options:
 - `-f/--force`, which can be used to skip the confirmation step in case you are already connected to another controller.

#### Example
```bash
connect grpc://np04-srv-019:56582
```

#### Related command
 - `disconnect`

### disable-triggers
#### Description
**NOTE**: This command depends on your FSM configuration. If you don't use the standard FSM from the DAQ, you may not have it!

**NOTE**: This command requires you to have booted the system and to be connected to a controller.

This command allows you to disable the triggers of the system, when it is `running`, and thus to reach the `ready` state.

The `disable-triggers` command can take the following option:
 - `--target` (optional), allows you to specify a target application/segment for the command. The command will only be run on that application or segment and children if you specify it. By default, the target is the top segment for the whole session.

#### Examples
To send `disable-triggers` to the whole of the DAQ:
```bash
disable-triggers
```
To send `disable-triggers` to the whole trigger segment:
```bash
disable-triggers --target root-controller/trg-controller
```
To send `disable-triggers` to the MLT only:
```bash
disable-triggers --target root-controller/trg-controller/mlt
```

#### Related commands
 - `enable-triggers`
 - `change-rate`

### disconnect
#### Description
This command is used to disconnect the shell to a controller.

The `disconnect` command takes the control address of the controller as argument

If you are connected to a controller, you will be asked to confirm that you want to disconnect.

The `disconnect` command take the following options:
 - `-f/--force`, which can be used to skip the confirmation step in case you are already connected to another controller.

#### Example
```bash
disconnect
```

#### Related command
 - `connect`

### drain-dataflow
#### Description
**NOTE**: This command depends on your FSM configuration. If you don't use the standard FSM from the DAQ, you may not have it!

**NOTE**: This command requires you to have booted the system and to be connected to a controller.

This command allows you to drain the dataflow of the system, when it is `ready`, and thus to reach the `dataflow-drained` state.

The `drain-dataflow` command can take the following options, depending on your FSM configuration:
 - `--target` (optional), allows you to specify a target application/segment for the command. The command will only be run on that application or segment and children if you specify it. By default, the target is the top segment for the whole session.
 - `--elisa-post` (optional), allows you to add a message on the ELisA logbook post that gets created when the run finishes.
 - `--file-logbook-post` (optional), allows you to add a message on the file logbook post that gets create when the run finishes.
#### Examples
To send `drain-dataflow` to the whole of the DAQ:
```bash
drain-dataflow
```
To send `drain-dataflow` to the whole trigger segment:
```bash
drain-dataflow --target root-controller/trg-controller
```
To send `drain-dataflow` to the MLT only:
```bash
drain-dataflow --target root-controller/trg-controller/mlt
```

#### Related commands
 - `start`
 - `disable-triggers`
 - `stop-trigger-sources`

### enable-triggers
#### Description
**NOTE**: This command depends on your FSM configuration. If you don't use the standard FSM from the DAQ, you may not have it!

**NOTE**: This command requires you to have booted the system and to be connected to a controller.

This command allows you to enable the trigger of the system, when it is `ready`, and thus to reach the `running` state.

The `enable-triggers` command can take the following options:
 - `--target` (optional), allows you to specify a target application/segment for the command. The command will only be run on that application or segment and children if you specify it. By default, the target is the top segment for the whole session.

#### Examples
To send `enable-triggers` to the whole of the DAQ:
```bash
enable-triggers
```
To send `enable-triggers` to the whole trigger segment:
```bash
enable-triggers --target root-controller/trg-controller
```
To send `enable-triggers` to the MLT only:
```bash
enable-triggers --target root-controller/trg-controller/mlt
```

#### Related commands
 - `start`
 - `disable-triggers`

### exclude
#### Description
**NOTE**: This command requires you to have booted the system and to be connected to a controller.

Allows you to exclude a segment or an application from the DAQ system. All commands to the excluded part of the system are then ignored, and the next time `recompute-status` is issued, excluded nodes states are ignored.

The `exclude` command can take the following options:
 - `--target` (optional), allows you to specify a target application/segment for the command. The command will only be run on that application or segment if you specify it. By default, the target is the top segment for the whole session.

#### Examples
To `exclude` to the whole trigger segment:
```bash
exclude --target root-controller/trg-controller
```
To `exclude` to the MLT only:
```bash
exclude --target root-controller/trg-controller/mlt
```

#### Related commands
 - `include`
 - `status`
 - `recompute-status`


### flush
#### Description
This command removes the dead processes from the `ps` list, after issuing `flush`, you will not be able to send `restart` to that process.

The `flush` command can take the following options:
 - `--uuid`, to select a process to flush based on its UUID.
 - `-u/--user`, to select the processes to flush based on its user.
 - `-n/--name`, to select a process to flush based on its "friendly name".
 - `-s/--session`, to select the processes to flush based on a session name.

By default, `flush` will flush all the dead processes from all sessions, users and names.

All the processes metadata can be which can be found by issuing `ps`.

#### Examples
To `flush` all the dead processes:
```bash
flush
```
To `flush` the MLT:
```bash
flush --name mlt
```
To `flush` the whole session:
```bash
flush -s your-session-name
```

#### Related commands
 - `kill`
 - `ps`

### include
#### Description
**NOTE**: This command requires you to have booted the system and to be connected to a controller.

Allows you to include a segment or an application (that was previously excluded) from the DAQ system.

The `include` command can take the following options:
 - `--target` (optional), allows you to specify a target application/segment for the command. The command will only be run on that application or segment if you specify it. By default, the target is the top segment for the whole session.

#### Examples
To `include` to the whole trigger segment:
```bash
include --target root-controller/trg-controller
```
To `include` to the MLT only:
```bash
include --target root-controller/trg-controller/mlt
```

#### Related commands
 - `exclude`
 - `status`
 - `recompute-status`

### kill
#### Description
This command kills running processes.

The `kill` command must take at least one the following options:
 - `--uuid`, to select a process to flush based on its UUID.
 - `-u/--user`, to select the processes to flush based on its user.
 - `-n/--name`, to select a process to flush based on its "friendly name".
 - `-s/--session`, to select the processes to flush based on a session name.

By default, `kill` does nothing, you need to supply one of the options.

All the processes metadata can be which can be found by issuing `ps`.

#### Examples
To `kill` the MLT:
```bash
kill --name mlt
```
To `kill` the whole session:
```bash
kill -s your-session-name
```

#### Related commands
 - `terminate`
 - `ps`
 - `boot`
 - `restart`


### logs
#### Description
This command prints the log of a processes.

The `logs` command must take at least one the following options:
 - `--uuid`, to select a process to flush based on its UUID.
 - `-u/--user`, to select the processes to flush based on its user.
 - `-n/--name`, to select a process to flush based on its "friendly name".
 - `-s/--session`, to select the processes to flush based on a session name.
 - `--how-far`, how many lines to print, by default it `logs` print the last 100 lines of log.
 - `--grep`, to select a particular string in the logs. Works with regex too.

By default, `logs` does nothing, you need to supply one or more of the options `--uuid`, `-u/--user`, `-n/--name`, `-s/-session`, and the logical _AND_ of this options must correspond to exactly one process.

All the processes metadata can be which can be found by issuing `ps`.

#### Example
To get the `logs` of the MLT:
```bash
logs --name mlt
```
To get the errors in `logs` of the MLT:
```bash
logs --name mlt --grep ERROR
```

#### Related command
 - `ps`


### ps
#### Description
This command list running processes.

The `ps` command must take at least one the following options:
 - `--uuid`, to select a process to flush based on its UUID.
 - `-u/--user`, to select the processes to flush based on its user.
 - `-n/--name`, to select a process to flush based on its "friendly name".
 - `-s/--session`, to select the processes to flush based on a session name.

By default, `ps` list all the processes.

#### Examples
To check the state the MLT process:
```bash
ps --name mlt
```
To check the state of the whole session:
```bash
ps -s your-session-name
```
To check the state of all the processes:
```bash
ps
```

#### Related commands
 - `kill`
 - `logs`
 - `restart`
 - `boot`

### recompute-status
#### Description
**NOTE**: This command requires you to have booted the system and to be connected to a controller.

Figure out the status the status of the controller, from the state of its _included_ children.

The `recompute-status` command takes the following options:
 - `--target` (optional), allows you to specify a target application/segment for the command. The command will only be run on that application or segment and children if you specify it. By default, the target is the top segment for the whole session.
 - `--execute-along-path/--dont-execute-along-path` (optional), the command gets executed along the path of the target, starting with the top controller, etc. By default, execute along path is true.
 - `--execute-on-all-subsequent-children-in-path/--dont-execute-on-all-subsequent-children-in-path` (optional), the command gets executed on all the children (applications and controllers) that are controlled by target (similar to `-r/--recursive` for `rm` or `grep`). By default, execute on all subsequent children in path.

By default, the `recompute-status` recomputes the status of all the system.

#### Example
To recompute the status of the whole system:
```bash
recompute-status
```
To recompute the status of the trg-controller, and the root-controller:
```bash
recompute-status --target root-controller/trg-controller
```
To recompute the status of the trg-controller _only_:
```bash
recompute-status --target root-controller/trg-controller --dont-execute-along-path
```

#### Related commands
 - `status`
 - `exclude`
 - `include`


### restart
#### Description
**NOTE**: This command isn't typically used right now, most likely this will not work as intended.

Restart a process that was booted.

The `restart` command must take at least one the following options:
 - `--uuid`, to select a process to flush based on its UUID.
 - `-u/--user`, to select the processes to flush based on its user.
 - `-n/--name`, to select a process to flush based on its "friendly name".
 - `-s/--session`, to select the processes to flush based on a session name.

By default, `restart` does nothing, you need to supply one or more of the options `--uuid`, `-u/--user`, `-n/--name`, `-s/-session`, and the logical _AND_ of this options must correspond to exactly one process.

#### Example
To `restart` the MLT process:
```bash
restart --name mlt
```

#### Related commands
 - `boot`
 - `kill`
 - `ps`


### scrap
#### Description
**NOTE**: This command depends on your FSM configuration. If you don't use the standard FSM from the DAQ, you may not have it!

**NOTE**: This command requires you to have booted the system and to be connected to a controller.

This command allows you to "unconfigure" the system, when it is `configured`, and thus to reach the `initial` state.

The `scrap` command can take the following option:
 - `--target` (optional), allows you to specify a target application/segment for the command. The command will only be run on that application or segment and children if you specify it. By default, the target is the top segment for the whole session.

#### Examples
To send `scrap` to the whole of the DAQ:
```bash
scrap
```
To send `scrap` to the whole trigger segment:
```bash
scrap --target root-controller/trg-controller
```
To send `scrap` to the MLT only:
```bash
scrap --target root-controller/trg-controller/mlt
```

#### Related commands
 - `conf`
 - `stop`

### start
#### Description
**NOTE**: This command depends on your FSM configuration. If you don't use the standard FSM from the DAQ, you may not have it!

**NOTE**: This command requires you to have booted the system and to be connected to a controller.

This command allows you to "start" the run on system, when it is `configured`, and thus to reach the `ready` state.

The `start` command can take the following options:
 - `--target` (optional), allows you to specify a target application/segment for the command. The command will only be run on that application or segment and children if you specify it. By default, the target is the top segment for the whole session.
 - `--elisa-post` (optional), allows you to add a message on the ELisA logbook post that gets created when the run ends. By default, nothing is added on the post.
 - `--file-logbook-post` (optional), allows you to add a message on the file logbook post that gets create when the run ends. By default, nothing is added on the post.
 - `--run-type` (optional), either _PROD_ or _TEST_, depending on how you think the data will be used. By default, _TEST_ is used.
 - `--trigger-rate` (optional), the trigger rate you want to set. By default it's 0 Hz, but the system will use the trigger rate from the configuration.
 - `--disable-data-storage` (optional), wether to disable the writing of the data and have a "dry run" of the DAQ. By default, write data.
 - `--run-number` (required, in some cases), which run number to use.

#### Examples
To send `start`:
```bash
start --run-number 1
```
To send `start` and add a message to the ELisa logbook, and run in PROD mode:
```bash
start --elisa-post "A run with the TDE and PDS" --run-type PROD
```

#### Related commands
 - `conf`
 - `enable-triggers`
 - `drain-dataflow`

### status
#### Description
**NOTE**: This command requires you to have booted the system and to be connected to a controller.

Prints the status the status of the controller.

The `status` command takes the following options:
 - `--target` (optional), allows you to specify a target application/segment for the command. The command will only be run on that application or segment and children if you specify it. By default, the target is the top segment for the whole session.
 - `--execute-along-path/--dont-execute-along-path` (optional), the command gets executed along the path of the target, starting with the top controller, etc. By default, execute along path is true.
 - `--execute-on-all-subsequent-children-in-path/--dont-execute-on-all-subsequent-children-in-path` (optional), the command gets executed on all the children (applications and controllers) that are controlled by target (similar to `-r/--recursive` for `rm` or `grep`). By default, execute on all subsequent children in path.

By default, the `status` prints the status of all the system.

#### Example
To get the status of the whole system:
```bash
status
```
To get the status of the trg-controller, and the root-controller:
```bash
status --target root-controller/trg-controller
```
To get the status of the trg-controller _only_:
```bash
status --target root-controller/trg-controller --dont-execute-along-path
```

#### Related commands
 - `recompute-status`
 - `exclude`
 - `include`

### stop
#### Description
**NOTE**: This command depends on your FSM configuration. If you don't use the standard FSM from the DAQ, you may not have it!

**NOTE**: This command requires you to have booted the system and to be connected to a controller.

This command allows you to stop the system, when it is in the `trigger-sources-stopped` state, and thus to reach the `configured` state.

The `stop` command can take the following option:
 - `--target` (optional), allows you to specify a target application/segment for the command. The command will only be run on that application or segment and children if you specify it. By default, the target is the top segment for the whole session.

#### Examples
To send `stop` to the whole of the DAQ:
```bash
stop
```
To send `stop` to the whole trigger segment:
```bash
stop --target root-controller/trg-controller
```
To send `stop` to the MLT only:
```bash
stop --target root-controller/trg-controller/mlt
```

#### Related commands
 - `scrap`
 - `start`
 - `stop-trigger-sources`

### stop-trigger-sources
#### Description
**NOTE**: This command depends on your FSM configuration. If you don't use the standard FSM from the DAQ, you may not have it!

**NOTE**: This command requires you to have booted the system and to be connected to a controller.

This command allows you to stop the trigger sources of the system, when it is in the `dataflow-drained` state, and thus to reach the `trigger-sources-stopped` state.

The `stop-trigger-sources` command can take the following option:
 - `--target` (optional), allows you to specify a target application/segment for the command. The command will only be run on that application or segment and children if you specify it. By default, the target is the top segment for the whole session.

#### Examples
To send `stop-trigger-sources` to the whole of the DAQ:
```bash
stop-trigger-sources
```
To send `stop-trigger-sources` to the whole trigger segment:
```bash
stop-trigger-sources --target root-controller/trg-controller
```
To send `stop-trigger-sources` to the MLT only:
```bash
stop-trigger-sources --target root-controller/trg-controller/mlt
```

#### Related commands
 - `stop`
 - `drain-dataflow`

### surrender-control
#### Description
**NOTE**: This command requires you to have booted the system and to be connected to a controller.

**NOTE**: This command isn't typically used right now.

This commands allows you to give up the control of a controller and its children. Note the user must be in control to be able to send commands to the controller

The `surrender-control` command takes the following options:
 - `--target` (optional), allows you to specify a target application/segment for the command. The command will only be run on that application or segment and children if you specify it. By default, the target is the top segment for the whole session.
 - `--execute-along-path/--dont-execute-along-path` (optional), the command gets executed along the path of the target, starting with the top controller, etc. By default, execute along path is true.
 - `--execute-on-all-subsequent-children-in-path/--dont-execute-on-all-subsequent-children-in-path` (optional), the command gets executed on all the children (applications and controllers) that are controlled by target (similar to `-r/--recursive` for `rm` or `grep`). By default, execute on all subsequent children in path.

By default, `surrender-control` surrenders the control on the whole system.

#### Example
To give up the control of the whole session:
```bash
surrender-control
```
To give up the control of the trg-controller and its children:
```bash
surrender-control --target root-controller/trg-controller
```

#### Related command
 - `take-control`
 - `who-is-in-charge`
 - `whoami`

### take-control
#### Description
**NOTE**: This command requires you to have booted the system and to be connected to a controller.

**NOTE**: This command isn't typically used right now.

This commands allows you to take the control of a controller and its children. Note the user must be in control to be able to send commands to the controller

The `take-control` command takes the following options:
 - `--target` (optional), allows you to specify a target application/segment for the command. The command will only be run on that application or segment and children if you specify it. By default, the target is the top segment for the whole session.
 - `--execute-along-path/--dont-execute-along-path` (optional), the command gets executed along the path of the target, starting with the top controller, etc. By default, execute along path is true.
 - `--execute-on-all-subsequent-children-in-path/--dont-execute-on-all-subsequent-children-in-path` (optional), the command gets executed on all the children (applications and controllers) that are controlled by target (similar to `-r/--recursive` for `rm` or `grep`). By default, execute on all subsequent children in path.

By default, `take-control` surrenders the control on the whole system.

#### Example
To take control of the whole session:
```bash
take-control
```
To take control of the trg-controller and its children:
```bash
take-control --target root-controller/trg-controller
```

#### Related command
 - `surrender-control`
 - `who-is-in-charge`
 - `whoami`

### terminate
#### Description
This command kills all the running processes in your instance of the process manager.

The `terminate` takes no option.

#### Example
To `terminate` all the processes:
```bash
terminate
```

#### Related commands
 - `kill`
 - `ps`
 - `boot`
 - `restart`

### wait
#### Description
This command make the run control wait.

The `wait` takes one argument, the number of second to wait

#### Example
To `wait` 10 seconds:
```bash
wait 10
```

### who-is-in-charge
#### Description
**NOTE**: This command requires you to have booted the system and to be connected to a controller.

**NOTE**: This command isn't typically used right now.

**NOTE**: This command does not render correctly right now who is in charge for the children.

This commands displays who is has the control of a controller and its children. Note the user must be in control to be able to send commands to the controller

The `who-is-in-charge` command takes the following options:
 - `--target` (optional), allows you to specify a target application/segment for the command. The command will only be run on that application or segment and children if you specify it. By default, the target is the top segment for the whole session.
 - `--execute-along-path/--dont-execute-along-path` (optional), the command gets executed along the path of the target, starting with the top controller, etc. By default, execute along path is true.
 - `--execute-on-all-subsequent-children-in-path/--dont-execute-on-all-subsequent-children-in-path` (optional), the command gets executed on all the children (applications and controllers) that are controlled by target (similar to `-r/--recursive` for `rm` or `grep`). By default, execute on all subsequent children in path.

By default, `who-is-in-charge` surrenders the control on the whole system.

#### Example
To see who is in charge of the whole session:
```bash
who-is-in-charge
```
To see who is in charge of the trg-controller and its children:
```bash
who-is-in-charge --target root-controller/trg-controller
```

#### Related commands
 - `take-control`
 - `surrender-control`
 - `whoami`

### whoami
#### Description
**NOTE**: This command isn't typically used right now.

This command prints your name.

#### Example
To print your name:
```bash
whoami
> jcvandamme