import socket
import time

RECEIVER_IP = "10.0.0.2"
RECEIVER_PORT = 5000

TOTAL_PACKETS = 100
ACK_TIMEOUT = 0.3
MAX_RETRIES = 10

def main():

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    sock.settimeout(ACK_TIMEOUT)

    acknowledged = 0
    total_transmissions = 0
    retransmissions = 0

    start_time = time.perf_counter()

    print("UDP Sender Started", flush=True)
    print("Sending 100 packets...", flush=True)

    for seq in range(1, TOTAL_PACKETS + 1):

        success = False

        for attempt in range(MAX_RETRIES + 1):

            packet_type = (
                "NEW" if attempt == 0 else "RETX"
            )

            message = (
                f"DATA|{seq}|{packet_type}"
            )

            sock.sendto(
                message.encode(),
                (RECEIVER_IP, RECEIVER_PORT)
            )

            total_transmissions += 1

            if attempt > 0:
                retransmissions += 1

                print(
                    f"Retransmitting packet {seq}",
                    flush=True
                )

            deadline = (
                time.monotonic() + ACK_TIMEOUT
            )

            while time.monotonic() < deadline:

                remaining = (
                    deadline - time.monotonic()
                )

                sock.settimeout(max(remaining, 0.001))

                try:
                    data, addr = sock.recvfrom(1024)
                except socket.timeout:
                    break

                if addr[0] != RECEIVER_IP:
                    continue

                if data.decode() == f"ACK|{seq}":
                    success = True
                    break

            if success:
                acknowledged += 1
                break

        if not success:
            print(
                f"Packet {seq} NOT acknowledged",
                flush=True
            )

    # Notify receiver that transmission is complete
    sock.settimeout(ACK_TIMEOUT)

    end_confirmed = False

    for _ in range(10):

        sock.sendto(
            b"END",
            (RECEIVER_IP, RECEIVER_PORT)
        )

        try:
            data, addr = sock.recvfrom(1024)

            if (
                addr[0] == RECEIVER_IP
                and data == b"END_ACK"
            ):
                end_confirmed = True
                break

        except socket.timeout:
            pass

    elapsed = time.perf_counter() - start_time

    print("\n========== SENDER SUMMARY ==========")
    print("Original packets:", TOTAL_PACKETS)
    print("Total transmissions:", total_transmissions)
    print("Retransmissions:", retransmissions)
    print("Acknowledged packets:", acknowledged)
    print(
        "Unacknowledged packets:",
        TOTAL_PACKETS - acknowledged
    )
    print(f"Elapsed time: {elapsed:.3f} seconds")
    print("END confirmed:", end_confirmed)
    print("====================================")

    sock.close()


if __name__ == "__main__":
    main()

