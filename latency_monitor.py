import struct
import time

from ryu.lib import addrconv
from ryu.lib.packet import packet_base

class LatencyMonitorPacket(packet_base.PacketBase):

	ETH_TYPE = 0x0888
	PKT_STRUCT = '!6s6sHIId'

	def __init__(self, dp=0, t=0, port=0):
		self.time = t
		self.dp = dp
		self.port = port

	@classmethod
	def parser(cls, buf):
		dst, src, ethertype, dp, port, ti = struct.unpack_from(cls.PKT_STRUCT, buf)
		return cls(dp, ti, port)

	def serialize(self, payload, prev):
		return struct.pack(self.PKT_STRUCT,
                addrconv.mac.text_to_bin("11:11:11:11:11:11"),
                addrconv.mac.text_to_bin("22:22:22:22:22:22"),
                self.ETH_TYPE,
                self.dp,
                self.port,
                self.time)
