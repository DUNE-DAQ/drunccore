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

## Running on a production release

