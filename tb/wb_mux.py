import cocotb
from cocotb.triggers import Timer

def reset(dut):
    dut.slave_select.value = 0

    dut.master.cyc.value = 0
    dut.master.stb.value = 0
    dut.master.write_enable.value = 0
    dut.master.addr.value = 0
    dut.master.write_data.value = 0
    dut.master.select.value = 0
    dut.master.lock.value = 0

    dut.slaves[0].ack.value = 0
    dut.slaves[0].stall.value = 0
    dut.slaves[0].rty.value = 0
    dut.slaves[0].err.value = 0
    dut.slaves[0].read_data.value = 0

    dut.slaves[1].ack.value = 0
    dut.slaves[1].stall.value = 0
    dut.slaves[1].rty.value = 0
    dut.slaves[1].err.value = 0
    dut.slaves[1].read_data.value = 0

@cocotb.test()
async def test_wishbone_demux_basic(dut):
    """Test WishboneMux with two slaves and one master."""

    await Timer(1, unit='ns')

    reset(dut)
    await Timer(1, unit='ns')

    # Test slave_select = 0
    dut.slave_select.value = 0

    dut.master.cyc.value = 1
    dut.master.stb.value = 1
    dut.master.write_enable.value = 1
    dut.master.addr.value = 0xA5
    dut.master.write_data.value = 0xDEADBEEF
    dut.master.select.value = 0xF
    dut.master.lock.value = 0

    dut.slaves[0].ack.value = 1
    dut.slaves[0].stall.value = 1
    dut.slaves[0].rty.value = 1
    dut.slaves[0].err.value = 1
    dut.slaves[0].read_data.value = 0xCACABEBE

    await Timer(1, unit='ns')

    assert dut.slaves[0].cyc.value == 1
    assert dut.slaves[0].stb.value == 1
    assert dut.slaves[0].write_enable.value == 1
    assert dut.slaves[0].addr.value == 0xA5
    assert dut.slaves[0].write_data.value == 0xDEADBEEF
    assert dut.slaves[0].select.value == 0xF

    # At the very least, STB and CYC should be 0 on slave 1
    assert dut.slaves[1].cyc.value == 0
    assert dut.slaves[1].stb.value == 0

    assert dut.master.ack.value == 1
    assert dut.master.stall.value == 1
    assert dut.master.rty.value == 1
    assert dut.master.err.value == 1
    assert dut.master.read_data.value == 0xCACABEBE

    await Timer(1, unit = "ns")

    # Test slave_select = 1
    dut.slave_select.value = 1

    dut.master.cyc.value = 1
    dut.master.stb.value = 1
    dut.master.write_enable.value = 1
    dut.master.addr.value = 0x5A
    dut.master.write_data.value = 0xFEEDFACE
    dut.master.select.value = 0xA
    dut.master.lock.value = 1

    dut.slaves[1].ack.value = 1
    dut.slaves[1].stall.value = 1
    dut.slaves[1].rty.value = 1
    dut.slaves[1].err.value = 1
    dut.slaves[1].read_data.value = 0xB1AB2

    await Timer(1, unit='ns')

    assert dut.slaves[1].cyc.value == 1
    assert dut.slaves[1].stb.value == 1
    assert dut.slaves[1].write_enable.value == 1
    assert dut.slaves[1].addr.value == 0x5A
    assert dut.slaves[1].write_data.value == 0xFEEDFACE
    assert dut.slaves[1].select.value == 0xA

    # At the very least, STB and CYC should be 0 on slave 0
    assert dut.slaves[0].cyc.value == 0
    assert dut.slaves[0].stb.value == 0

    assert dut.master.ack.value == 1
    assert dut.master.stall.value == 1
    assert dut.master.rty.value == 1
    assert dut.master.err.value == 1
    assert dut.master.read_data.value == 0xB1AB2