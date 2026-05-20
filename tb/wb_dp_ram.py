import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

def assert_ack(wb):
    assert wb.ack.value == 1
    assert wb.err.value == 0

def assert_read(wb, address, expected):
    assert_ack(wb)
    assert wb.read_data.value == expected, f"Error at address {address}: expected {hex(expected)}, got {hex(wb.read_data.value)}"

def start_read_txn(wb, address, byte_select):
    wb.cyc.value = 1
    wb.stb.value = 1
    wb.write_enable.value = 0
    wb.select.value = byte_select
    wb.addr.value = address

def start_write_txn(wb, address, data, byte_select):
    wb.cyc.value = 1
    wb.stb.value = 1
    wb.write_enable.value = 1
    wb.select.value = byte_select
    wb.addr.value = address
    wb.write_data.value = data

def finish_txn(wb):
    wb.cyc.value = 0
    wb.stb.value = 0

async def reset(dut):
    dut.rst.value = 1
    # Manually clear RAM for test repeatability
    dut.ram.ram.mem.value = [0] * len(dut.ram.ram.mem.value)
    await RisingEdge(dut.clk)
    for wb in [dut.wb_a, dut.wb_b]:
        wb.cyc.value = 0
        wb.stb.value = 0
        wb.select.value = 0
        wb.write_enable.value = 0
        wb.addr.value = 0
        wb.write_data.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    print("reset done !")

@cocotb.test()
async def dual_port_wishbone_ram_test(dut):
    """Test dual-ported Wishbone RAM backed by dual-port RAM."""
    cocotb.start_soon(Clock(dut.clk, 1, unit="ns").start())
    await reset(dut)

    test_data = [
        (0, 0xDEADBEEF),
        (4, 0xCAFEBABE),
        (8, 0x12345678),
        (12, 0xA5A5A5A5)
    ]

    # BASIC WORD WRITE TEST: wb_a writes, wb_b reads
    for address, data in test_data:
        start_write_txn(dut.wb_a, address, data, 0b1111)

        await RisingEdge(dut.clk)

        # Immediately
        # send a read request (pipeline mode)
        finish_txn(dut.wb_a)

        start_read_txn(dut.wb_a, address, 0b1111)
        start_read_txn(dut.wb_b, address, 0b1111)

        # Verify by reading back
        await RisingEdge(dut.clk)

        # Write request has been acknowledged
        assert_ack(dut.wb_a)

        await RisingEdge(dut.clk)

        assert_read(dut.wb_a, address, data)
        finish_txn(dut.wb_a)

        assert_read(dut.wb_b, address, data)
        finish_txn(dut.wb_b)

        await RisingEdge(dut.clk)


    # WRITE TEST #2: wb_b writes, wb_a reads
    for i in range(0, 40, 4):
        address = i
        data = i
        start_write_txn(dut.wb_b, address, data, 0b1111)

        await RisingEdge(dut.clk)

        finish_txn(dut.wb_b)

        # Immediately start read and
        # check that setting write_data doesn't affect RAM state
        start_read_txn(dut.wb_a, address, 0b1111)
        start_read_txn(dut.wb_b, address, 0b1111)
        dut.wb_a.write_data = 0xFAFABEBE
        await RisingEdge(dut.clk)

        # Verify by reading back
        await RisingEdge(dut.clk)

        # Write request has been acknowledged
        assert_ack(dut.wb_b)
        assert_read(dut.wb_a, i, i)
        
        # Read back a second time, now on both ports
        await RisingEdge(dut.clk)

        assert_read(dut.wb_a, address, data)
        finish_txn(dut.wb_a)

        assert_read(dut.wb_b, address, data)
        finish_txn(dut.wb_b)

        await RisingEdge(dut.clk)

    # NO WRITE TEST: wb_a reads, wb_b sets write_data but no write
    for i in range(0, 40, 4):
        start_read_txn(dut.wb_a, i, 0b1111)
        # Check that setting write_data doesn't affect RAM state
        dut.wb_a.write_data.value = 0xBEBECACA
        dut.wb_b.write_data.value = 0xCACABEBE

        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)

        assert_read(dut.wb_a, i, i)
        finish_txn(dut.wb_a)

        await RisingEdge(dut.clk)

    # BYTE WRITE TEST: wb_a writes with byte enables, wb_b reads
    for byte_enable in range(16):
        # We reset memory...
        await reset(dut)
        # Generate mask from byte_enable
        mask = 0

        for j in range(4):
            if (byte_enable >> j) & 1:
                mask |= (0xFF << (j * 8))

        print(f"mask: {mask}")

        for address, data in test_data:
            start_write_txn(dut.wb_a, address, data, byte_enable)

            # Write
            await RisingEdge(dut.clk)

            finish_txn(dut.wb_a)
            # Read all bytes in word for good measure
            start_read_txn(dut.wb_b, address, 0b1111)

            await RisingEdge(dut.clk)

            # Verify by reading back
            await RisingEdge(dut.clk)

            read_val = dut.wb_b.read_data.value
            mem_val = dut.ram.ram.mem.value[int(address/4)]
            assert (read_val & mask) == (data & mask)
            assert (read_val & ~mask) == (mem_val & ~mask)

            finish_txn(dut.wb_b)
            await RisingEdge(dut.clk)

    # SIMULTANEOUS WRITE TEST: both ports write to different addresses
    start_write_txn(dut.wb_a, 0, 0xB1AB2, 0b1111)
    start_write_txn(dut.wb_b, 4, 0x7777, 0b1111)

    await RisingEdge(dut.clk)

    finish_txn(dut.wb_a)
    finish_txn(dut.wb_b)

    start_read_txn(dut.wb_a, 0, 0b1111)
    start_read_txn(dut.wb_b, 4, 0b1111)

    await RisingEdge(dut.clk)

    assert_ack(dut.wb_a)
    assert_ack(dut.wb_b)

    await RisingEdge(dut.clk)
    assert_read(dut.wb_a, 0, 0xB1AB2)
    assert_read(dut.wb_b, 4, 0x7777)
    finish_txn(dut.wb_a)
    finish_txn(dut.wb_b)

    await RisingEdge(dut.clk)

    # ERROR TEST: misaligned accesses

    # Write some data and wait for write to happen
    start_write_txn(dut.wb_a, 0x0, 0xb1abc001, 0b1111)

    await RisingEdge(dut.clk)
    finish_txn(dut.wb_a)

    await RisingEdge(dut.clk)
    assert_ack(dut.wb_a)

    start_write_txn(dut.wb_a, 0x1, 0x00000000, 0b1111)

    await RisingEdge(dut.clk)

    finish_txn(dut.wb_a)

    await RisingEdge(dut.clk)

    assert dut.wb_a.ack.value == 0
    assert dut.wb_a.err.value == 1

    # Re-read to confirm data is unchanged
    start_read_txn(dut.wb_a, 0x0, 0b1111)
    
    await RisingEdge(dut.clk)
    finish_txn(dut.wb_a)

    await RisingEdge(dut.clk)

    assert_read(dut.wb_a, 0x0, 0xb1abc001)
