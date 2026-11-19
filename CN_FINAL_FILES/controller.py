import time

from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import (
    CONFIG_DISPATCHER,
    MAIN_DISPATCHER,
    DEAD_DISPATCHER,
    set_ev_cls
)
from os_ken.ofproto import ofproto_v1_3


class PacketLossController(app_manager.OSKenApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.datapaths = {}
        self.primary_failed = False
        self.failed_ports = set()

        self.logger.info(
            "Packet Loss Detection and Recovery Controller"
        )

    def add_flow(self, dp, in_port, out_port, eth_type):

        parser = dp.ofproto_parser
        ofproto = dp.ofproto

        match = parser.OFPMatch(
            in_port=in_port,
            eth_type=eth_type
        )

        actions = [
            parser.OFPActionOutput(out_port)
        ]

        instructions = [
            parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS,
                actions
            )
        ]

        msg = parser.OFPFlowMod(
            datapath=dp,
            priority=100,
            match=match,
            instructions=instructions
        )

        dp.send_msg(msg)

    def clear_flows(self, dp):

        parser = dp.ofproto_parser
        ofproto = dp.ofproto

        msg = parser.OFPFlowMod(
            datapath=dp,
            command=ofproto.OFPFC_DELETE,
            out_port=ofproto.OFPP_ANY,
            out_group=ofproto.OFPG_ANY,
            match=parser.OFPMatch()
        )

        dp.send_msg(msg)

    def install_path(self):

        if len(self.datapaths) < 4:
            self.logger.info(
                "Waiting for switches: %d/4",
                len(self.datapaths)
            )
            return

        start = time.perf_counter()

        if self.primary_failed:

            # Backup: h1 -> s1 -> s3 -> s4 -> h2
            path = {
                1: [(1, 3), (3, 1)],
                3: [(1, 2), (2, 1)],
                4: [(3, 1), (1, 3)]
            }

            self.logger.warning(
                "Installing BACKUP path via s3"
            )

        else:

            # Primary: h1 -> s1 -> s2 -> s4 -> h2
            path = {
                1: [(1, 2), (2, 1)],
                2: [(1, 2), (2, 1)],
                4: [(2, 1), (1, 2)]
            }

            self.logger.info(
                "Installing PRIMARY path via s2"
            )

        # Remove previous forwarding rules
        for dp in self.datapaths.values():
            self.clear_flows(dp)

        # Install IPv4 and ARP rules
        for dpid, pairs in path.items():

            dp = self.datapaths.get(dpid)

            if dp is None:
                continue

            for in_port, out_port in pairs:

                # IPv4
                self.add_flow(
                    dp, in_port, out_port, 0x0800
                )

                # ARP
                self.add_flow(
                    dp, in_port, out_port, 0x0806
                )

        elapsed = time.perf_counter() - start

        self.logger.info(
            "CONTROLLER REROUTE PROGRAMMING TIME: %.6f seconds",
            elapsed
        )

    @set_ev_cls(
        ofp_event.EventOFPSwitchFeatures,
        CONFIG_DISPATCHER
    )
    def switch_features_handler(self, ev):

        dp = ev.msg.datapath
        dpid = dp.id

        self.datapaths[dpid] = dp

        self.logger.info(
            "Switch s%s connected",
            dpid
        )

        self.install_path()

    @set_ev_cls(
        ofp_event.EventOFPStateChange,
        [MAIN_DISPATCHER, DEAD_DISPATCHER]
    )
    def state_change_handler(self, ev):

        dp = ev.datapath

        if ev.state == MAIN_DISPATCHER:

            was_missing = dp.id not in self.datapaths
            self.datapaths[dp.id] = dp

            if was_missing:
                self.install_path()

        elif ev.state == DEAD_DISPATCHER:

            if self.datapaths.get(dp.id) is dp:
                self.datapaths.pop(dp.id, None)

            self.logger.warning(
                "Switch s%s disconnected",
                dp.id
            )

    @set_ev_cls(
        ofp_event.EventOFPPortStatus,
        MAIN_DISPATCHER
    )
    def port_status_handler(self, ev):

        msg = ev.msg
        dp = msg.datapath
        ofproto = dp.ofproto

        dpid = dp.id
        port = msg.desc.port_no

        # Primary link endpoints:
        # s1 port 2 and s2 port 1
        is_primary_link = (
            (dpid == 1 and port == 2) or
            (dpid == 2 and port == 1)
        )

        if not is_primary_link:
            return

        is_down = (
            bool(
                msg.desc.state &
                ofproto.OFPPS_LINK_DOWN
            )
            or bool(
                msg.desc.config &
                ofproto.OFPPC_PORT_DOWN
            )
            or msg.reason == ofproto.OFPPR_DELETE
        )

        key = (dpid, port)

        if is_down:
            self.failed_ports.add(key)
        else:
            self.failed_ports.discard(key)

        new_failed = bool(self.failed_ports)

        if new_failed == self.primary_failed:
            return

        self.primary_failed = new_failed

        if self.primary_failed:

            self.logger.warning(
                "LINK DOWN: switch s%s port %s",
                dpid, port
            )

            self.install_path()

            self.logger.info(
                "Traffic switched to BACKUP path"
            )

        else:

            self.logger.info(
                "PRIMARY LINK RESTORED"
            )

            self.install_path()

            self.logger.info(
                "Traffic switched to PRIMARY path"
            )

