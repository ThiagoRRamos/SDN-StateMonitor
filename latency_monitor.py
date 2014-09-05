from ryu.lib.packet import packet_base
import struct
from ryu.lib import addrconv
import time

class LatencyMonitorPacket(packet_base.PacketBase):

	ETH_TYPE = 0x0888
	PKT_STRUCT = '!6s6sHid'

	def __init__(self, dp=0, t=0):
		self.time = t
		self.dp = dp

	@classmethod
	def parser(cls, buf):
		dst, src, ethertype, dp, ti = struct.unpack_from(cls.PKT_STRUCT, buf)
		#print dst, src, ethertype, dp, ti
		return cls(dp, ti)

	def serialize(self, payload, prev):
		return struct.pack(self.PKT_STRUCT,
                addrconv.mac.text_to_bin("11:11:11:11:11:11"),
                addrconv.mac.text_to_bin("22:22:22:22:22:22"),
                self.ETH_TYPE,
                self.dp,
                self.time)
