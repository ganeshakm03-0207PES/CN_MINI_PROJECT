# Computer Networks Mini Project: Packet Loss Detection and Recovery

This project demonstrates UDP packet acknowledgements and retransmissions alongside SDN path failover in a Mininet network controlled by OS-Ken.

## Project layout

- `CN_FINAL_FILES/controller.py` — OS-Ken controller. Installs OpenFlow 1.3 forwarding rules and switches between the primary and backup routes when the primary link changes state.
- `CN_FINAL_FILES/topology.py` — Mininet topology with hosts `h1` and `h2`, four Open vSwitches, and two routes.
- `CN_FINAL_FILES/udp_sender.py` — Sends 100 numbered UDP packets, waits for acknowledgements, and retries unacknowledged packets.
- `CN_FINAL_FILES/udp_receiver.py` — Receives and acknowledges packets, tracks unique deliveries, and prints a summary.

## Network paths

- Primary: `h1 — s1 — s2 — s4 — h2`
- Backup: `h1 — s1 — s3 — s4 — h2`

The hosts use `10.0.0.1` and `10.0.0.2`. The controller connects at `127.0.0.1:6653`; the switches use OpenFlow 1.3.

## Requirements

Run this project in a Linux environment with Mininet, Open vSwitch, OS-Ken, and Python 3 installed. The Mininet topology creates network namespaces and may require administrator privileges.

## Run the project

1. Start the controller in one terminal from the repository root:

   ```sh
   osken-manager CN_FINAL_FILES/controller.py
   ```

2. Start the topology in another terminal:

   ```sh
   sudo python3 CN_FINAL_FILES/topology.py
   ```

3. In the Mininet CLI, check connectivity:

   ```text
   mininet> pingall
   ```

4. From the Mininet CLI, start the receiver and sender. The Mininet hosts share the host filesystem; run these commands from the repository root:

   ```text
   mininet> h2 python3 CN_FINAL_FILES/udp_receiver.py &
   mininet> h1 python3 CN_FINAL_FILES/udp_sender.py
   ```

The sender and receiver print summaries of acknowledged packets, retransmissions, recovered packets, and any packets still missing.

## Try primary-link failover

While the Mininet CLI is running, take down and restore the primary link:

```text
mininet> link s1 s2 down
mininet> pingall
mininet> link s1 s2 up
```

The controller monitors the primary link and installs forwarding rules for the alternate route when it reports a failure.

## Notes

- The UDP sender and receiver use port `5000`.
- The source files are provided as uploaded. Validate the setup in your own Mininet/OS-Ken environment before relying on specific runtime results.
