# https://www.kernel.org/doc/Documentation/ABI/testing/procfs-diskstats
# https://www.kernel.org/doc/Documentation/block/statca.txt

# 259       0 nvme0n1 107146 2852 19971336 23647 181355 11090 15833592 22852 0 66784 92500 13669 0 1758032920 52066
# 259       1 nvme1n1 109518 3015 19983994 23593 172156 11064 15588608 22670 0 73196 98604 13669 0 1757785272 52757
#   9     127 md127 222424 0 48560354 0 333649 0 37421048 0 0 0 0 13669 0 3515818192 0


# https://www.kernel.org/doc/Documentation/admin-guide/iostats.rst

# NFS stats: http://git.linux-nfs.org/?p=steved/nfs-utils.git;a=blob;f=tools/mountstats/mountstats.py;hb=HEAD
import logging
import os
import pprint
import time
import util

pp = pprint.PrettyPrinter(indent=4)

logger = logging.getLogger("monitoring")

# loop = loopback
# ram = ram
# nbd = network block device https://www.kernel.org/doc/html/latest/admin-guide/blockdev/nbd.html, we may want to monitor these
# fbdisk = ?
# fbsnap = ?
# zram = Compressed memory as block store https://www.kernel.org/doc/html/latest/admin-guide/blockdev/zram.html

IGNORE_PREFIXES = [
    "loop",
    "ram",
]
DISKSTAT_KEYS = (
    "major",
    "minor",
    #        "name",
    "read_ios",
    "read_merge",
    "read_sectors",
    "read_ticks",
    "write_ios",
    "write_merges",
    "write_sectors",
    "write_ticks",
    "in_flight",
    "total_io_ticks",
    "total_time_in_queue",
    "discard_ios",
    "discard_merges",
    "discard_sectors",
    "discard_ticks",
    "flush_ios",
    "flush_ticks",
)
# files in /sys/block/DEV/* we care about.
# inflight: gives read and write ops inflight. Maybe not really useful for monitoring, but diskstats only gives one value.
# queue/: https://www.kernel.org/doc/Documentation/block/queue-sysfs.txt
BLOCK_FILES = [
    "inflight",
    "size",
    "queue/discard_granularity",
    "queue/hw_sector_size",
    "queue/io_poll",
    "queue/io_poll_delay",
    "queue/io_timeout",
    "queue/iostats",
    "queue/logical_block_size",
    "queue/max_hw_sectors_kb",
    "queue/max_sectors_kb",
    "queue/minimum_io_size",
    "queue/nomerges",
    "queue/optimal_io_size",
    "queue/physical_block_size",
    "queue/read_ahead_kb",
    "queue/rotational",
    "queue/rq_affinity",
    "queue/scheduler",
    "queue/write_cache",
]
# For the purposes of these stats, we are focusing solely on block devices.
class Disk:
    # This seems universal?
    sys_block_path = "/sys/block/"
    # /sys/class/block was not present on my QNAP NAS running kernel 4.14
    sys_class_block_path = "/sys/class/block/"
    sys_dev_block_path = "/sys/dev/block/"
    # /proc/diskstats has a good chunk of what we need and I wonder if there's anything in /sys/block that wouldn't be in there, or named differently.
    proc_diskstats_path = "/proc/diskstats"

    blockdevices = {}

    def get_devices(self):
        diskstats = {}
        if util.caniread(self.proc_diskstats_path) is False:
            logger.error(f"Fatal: Can't open {self.proc_diskstats_path} for reading.")
            return None

        with open(self.proc_diskstats_path, "r") as reader:
            # 8       0 sda 6812071 23231120 460799263 43073497 9561353 55255999 547604986 81837974 0 93365790 124928542
            diskstats_line = str(reader.readline()).strip().split()
            while diskstats_line != []:
                if diskstats_line[2].startswith(tuple(IGNORE_PREFIXES)):
                    diskstats_line = str(reader.readline()).strip().split()
                    continue
                diskname = diskstats_line.pop(2)
                diskstats[diskname] = {
                    "iostats": dict(zip(DISKSTAT_KEYS, list(map(int, diskstats_line))))
                }
                diskstats[diskname]["_time"] = time.time()

                diskstats_line = str(reader.readline()).strip().split()
        return diskstats

    def get_sys_stats(self, devnum):
        path = os.path.join(self.sys_dev_block_path, devnum)
        path = os.scandir(os.path.realpath(path))
        # Time to figure out what type of directory we have. Options are:
        # bdi
        # device (root of block device)
        # partition
        # partition with a partition table maybe?
        # md
        # dm
        # nvmeX
        # nvmeXnY
        # nvmeXnYpZ

    def get_queue(self, queue):
        return 0

    def get_disks(self):
        # First let's do the easy thing and get the stats that exist in diskstats:
        devs = self.get_devices()
        for dev in devs:
            devnum = (
                str(devs[dev]["iostats"]["major"])
                + ":"
                + str(devs[dev]["iostats"]["minor"])
            )
            self.get_sys_stats(devnum)

    def __init__(self):
        self.get_disks()


if __name__ == "__main__":

    mydisk = Disk()
