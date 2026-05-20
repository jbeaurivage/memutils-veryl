import cocotb
from cocotb.triggers import Timer

def reset(dut):
    dut.master_select.value = 0
    
    dut.masters[0].cyc.value = 0
    dut.masters[1].cyc.value = 0

    dut.masters[0].stb.value = 0
    dut.masters[1].stb.value = 0

    dut.masters[0].write_enable.value = 0
    dut.masters[1].write_enable.value = 0

    dut.masters[0].addr.value = 0
    dut.masters[1].addr.value = 0

    dut.masters[0].write_data.value = 0
    dut.masters[1].write_data.value = 0

    dut.masters[0].select.value = 0
    dut.masters[1].select.value = 0

    dut.masters[0].lock.value = 0
    dut.masters[1].lock.value = 0

    dut.slave.ack.value = 0
    dut.slave.stall.value = 0
    dut.slave.rty.value = 0
    dut.slave.err.value = 0
    dut.slave.read_data.value = 0

@cocotb.test()
async def test_wishbone_demux_basic(dut):
    """Test WishboneDemux with two masters and one slave."""

    await Timer(1, unit='ns')

    reset(dut)
    await Timer(1, unit='ns')

    # Test master_select = 0
    dut.master_select.value = 0

    dut.masters[0].cyc.value = 1
    dut.masters[0].stb.value = 1
    dut.masters[0].write_enable.value = 1
    dut.masters[0].addr.value = 0xA5
    dut.masters[0].write_data.value = 0xDEADBEEF
    dut.masters[0].select.value = 0xF
    dut.masters[0].lock.value = 0
    dut.slave.ack.value = 1
    dut.slave.stall.value = 1
    dut.slave.rty.value = 1
    dut.slave.err.value = 1
    dut.slave.read_data.value = 0xCACABEBE

    await Timer(1, unit='ns')

    assert dut.slave.cyc.value == 1
    assert dut.slave.stb.value == 1
    assert dut.slave.write_enable.value == 1
    assert dut.slave.addr.value == 0xA5
    assert dut.slave.write_data.value
    assert dut.slave.select.value == 0xF

    assert dut.masters[0].ack.value == 1
    assert dut.masters[0].stall.value == 1
    assert dut.masters[0].rty.value == 1
    assert dut.masters[0].err.value == 1
    assert dut.masters[0].read_data.value == 0xCACABEBE

    # Also check that STALL is set for any inactive master
    assert dut.masters[1].stall.value == 1

    await Timer(1, unit = "ns")

    # Test master_select = 1
    dut.master_select.value = 1

    dut.masters[1].cyc.value = 1
    dut.masters[1].stb.value = 1
    dut.masters[1].write_enable.value = 1
    dut.masters[1].addr.value = 0x5A
    dut.masters[1].write_data.value = 0xFEEDFACE
    dut.masters[1].select.value = 0xA
    dut.masters[1].lock.value = 1

    dut.slave.ack.value = 1
    dut.slave.stall.value = 1
    dut.slave.rty.value = 1
    dut.slave.err.value = 1
    dut.slave.read_data.value = 0xB1AB2

    await Timer(1, unit='ns')

    assert dut.slave.cyc.value == 1
    assert dut.slave.stb.value == 1
    assert dut.slave.write_enable.value == 1
    assert dut.slave.addr.value == 0x5A
    assert dut.slave.write_data.value == 0xFEEDFACE
    assert dut.slave.select.value == 0xA

    assert dut.masters[1].ack.value == 1
    assert dut.masters[1].stall.value == 1
    assert dut.masters[1].rty.value == 1
    assert dut.masters[1].err.value == 1
    assert dut.masters[1].read_data.value == 0xB1AB2

    # Check that STALL is set for any inactive master
    assert dut.masters[0].stall.value == 1
    assert dut.masters[0].stall.value == 1

    # Also check that STALL is only set for the active
    # master when the slave sets it

    dut.slave.stall.value = 0

    await Timer(1, unit='ns')

    assert dut.masters[1].stall.value == 0
    assert dut.masters[0].stall.value == 1