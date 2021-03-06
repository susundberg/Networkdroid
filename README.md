Networkdroid
============

Software for network diagnostic 

It consists of components:
* Single server running in linux box
 * It runs python with zeromq
 * Handles starting and stopping of modules
 * Fixed endpoints for clients and modules
 
* Zero or more running modules
 * Each connect with PUB to server SUB ( modules )
 * Example: Ping module that sends 'connection to 8.8.8.8 ok' every 0.5s
 * Example: HTTP GET module that sends 'http get ok' every 1s
 
* Zero or more running clients
* May connect with REQ to server REP ( clients )
 * Example: 'Start module PING' -- "OK"
* May connect with SUB to server PUB ( clients )
 * Example 'From module SSH: connection open'
 * Example 'From module TCPDUMP: traffic XXXX'


## Connections


### REP/REQ to Clients <-> Server

Bind on server side to known port. Clients connect. Accept commands:
 * ```LAUNCH <module name> ```
  * Start module with given name if found
  * Returns 'OK' if module launched without error
  * Returns 'FAIL' otherwise
 * ``` KILL <module name> ```
  * Kills module with given name if running
   * Returns 'OK' if module killed
   * Returns 'FAIL' if module is not running 
 * ``` LIST ```
  * Returns list of all known modules
 * ``` PING ```
  * Returns 'PONG' and all arguments joined with ',' 

### Modules PUB to Clients SUB
Server acts as Forwarder SUB->PUB for Modules to talk Clients
* Module PUB -> SUB (bind) server PUB (bind) -> SUB client

Forwards all messages from all modules to all clients. Needed as gateway so that clients dont need to know anything about the running modules. Messages in format of:
```<module name> <message type> <message data>```

Examples:
* 'SSH : HB OK' -- Module SSH sends heartbeat, all ok
* 'SSH : TERM' -- Module SSH sends heartbeat, bail out, last heartbeat.
* 'SSH INFO Connection ok' -- Module SSH sends INFO string to all clients
* 'TCPDUMP INFO 11:47:45.178938 IP arn06s02-in-f5.1e100.net.http > sundberg-MS-7680.local.51050:' -- Module TCPDUMP sends INFO string to all clients 



## Modules
* SSH module
 * Open SSH-pipe to pre-defined host allowing user to access the server machine (that might be inside NAT)
 * 'HB OK/FAIL' when connection to server state
 * 'INFO remote shell access ok/lost' -- When state changes

* PING module
 * Checks that connection to pre-defined host is ok, that is we have internet connection. Works in the order that state changes from ifup->internetok->dnsok, and returns on step down on error.
 * 'HB OK/FAIL' when connection to 8.8.8.8 (PingServer) is ok
 * 'INFO interface up/down' -- interface state chages up->down or down->up
 * 'INFO internet ok/failed' -- connection to PingServer changes 
 * 'INFO dns ok/failed' -- connection to google.com changes
 
* HTTP GET
 * Checks that client can do normal HTTP get from server known
 * 'HB OK/FAIL' connection is up and running
 * 'INFO http ok/failed' connection state changed

* TCPDUMP
 * Dumps the captured trafic on the INFO stream
 * 'INFO <data>'


## Clients
* Android via Bluetooth
 * Android application to be connected via Bluetooth

* Speaker
 * Read out aloud info messages

* Console
 * Use STDIN for launching and STDOUT for messages


