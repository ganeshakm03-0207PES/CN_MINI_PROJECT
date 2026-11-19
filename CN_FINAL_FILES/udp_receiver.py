import socket
import time

HOST = "0.0.0.0"
PORT = 5000

TOTAL_PACKETS = 100

def main():

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    sock.bind((HOST, PORT))
    sock.settimeout(20)

    received = set()
    first_received = set()
    recovered = set()

    start_time = time.perf_counter()

    print(
        "UDP Receiver Started on port 5000",
        flush=True
    )

    end_received = False
    end_deadline = None

    while True:

        if end_received:
            remaining = (
                end_deadline - time.monotonic()
            )

            if remaining <= 0:
                break

            sock.settimeout(remaining)

        try:
            data, addr = sock.recvfrom(1024)

        except socket.timeout:
            if end_received:
                break

            print(
                "Receiver timed out waiting for packets",
                flush=True
            )
            break

        message = data.decode()

        if message == "END":

            sock.sendto(b"END_ACK", addr)

            if not end_received:
                end_received = True
                end_deadline = (
                    time.monotonic() + 1.5
                )

            continue

        parts = message.split("|")

        if len(parts) != 3:
            continue

        if parts[0] != "DATA":
            continue

        try:
            seq = int(parts[1])
        except ValueError:
            continue

        packet_type = parts[2]

        if not 1 <= seq <= TOTAL_PACKETS:
            continue

        if packet_type not in ("NEW", "RETX"):
            continue

        if seq not in received:

            received.add(seq)

            if packet_type == "NEW":
                first_received.add(seq)

            elif packet_type == "RETX":
                recovered.add(seq)

            print(
                f"Received packet {seq} ({packet_type})",
                flush=True
            )

        # Always acknowledge, even for duplicates
        acknowledgement = f"ACK|{seq}"

        sock.sendto(
            acknowledgement.encode(),
            addr
        )

    elapsed = time.perf_counter() - start_time

    missing = (
        set(range(1, TOTAL_PACKETS + 1))
        - received
    )

    loss_percentage = (
        len(missing) / TOTAL_PACKETS
    ) * 100

    print("\n========== RECEIVER SUMMARY ==========")
    print("Expected packets:", TOTAL_PACKETS)
    print("Unique packets received:", len(received))
    print(
        "Received on first transmission:",
        len(first_received)
    )
    print(
        "Recovered by retransmission:",
        len(recovered)
    )
    print("Final missing packets:", len(missing))
    print(
        f"Final packet loss: {loss_percentage:.2f}%"
    )
    print(
        f"Receiver elapsed time: {elapsed:.3f} seconds"
    )
    print("======================================")

    sock.close()


if __name__ == "__main__":
    main()

