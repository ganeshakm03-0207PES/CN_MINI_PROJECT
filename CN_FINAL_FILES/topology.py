from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info


def create_network():
    net = Mininet(
        controller=None,
        switch=OVSSwitch,
        link=TCLink,
        autoSetMacs=True
    )

    info("*** Adding OS-Ken remote controller\n")

    c0 = net.addController(
        "c0",
        controller=RemoteController,
        ip="127.0.0.1",
        port=6653
    )

    info("*** Creating hosts\n")

    h1 = net.addHost(
        "h1",
        ip="10.0.0.1/24"
    )

    h2 = net.addHost(
        "h2",
        ip="10.0.0.2/24"
    )

    info("*** Creating switches\n")

    s1 = net.addSwitch(
        "s1", dpid="0000000000000001",
        protocols="OpenFlow13"
    )

    s2 = net.addSwitch(
        "s2", dpid="0000000000000002",
        protocols="OpenFlow13"
    )

    s3 = net.addSwitch(
        "s3", dpid="0000000000000003",
        protocols="OpenFlow13"
    )

    s4 = net.addSwitch(
        "s4", dpid="0000000000000004",
        protocols="OpenFlow13"
    )

    info("*** Creating network links\n")

    # Host links
    net.addLink(h1, s1, port2=1)
    net.addLink(h2, s4, port2=1)

    # Primary path
    net.addLink(s1, s2, port1=2, port2=1)
    net.addLink(s2, s4, port1=2, port2=2)

    # Backup path
    net.addLink(s1, s3, port1=3, port2=1)
    net.addLink(s3, s4, port1=2, port2=3)

    info("*** Starting network\n")
    net.start()

    info("*** Network started\n")
    info("*** Primary: h1-s1-s2-s4-h2\n")
    info("*** Backup : h1-s1-s3-s4-h2\n")

    info("*** Opening Mininet CLI\n")
    try:
        CLI(net)
    finally:
        info("*** Stopping network\n")
        net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    create_network()

