# MEMORY TESTBENCH
#
# BRH 10/24
#
# NOT USED IN FPGA EDITION !


import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

async def reset(dut):
    dut.rst.value = 0
    # Asserting RESET does not set the memory to 0, just like in real hardware.
    # We do it manually for testing purposes
    dut.ram.mem.value = [0] * len(dut.ram.mem.value)
    await RisingEdge(dut.clk)
    dut.port.enable.value = 0
    dut.port.byte_write_enable.value = 0
    dut.port.address.value = 0
    dut.port.write_data.value = 0
    await RisingEdge(dut.clk)

    dut.rst.value = 1
    await RisingEdge(dut.clk)

    print("reset done !")

def assert_read(dut, address, expected):
    assert dut.port.read_data.value == expected, f"Error at address {address}: expected {hex(expected)}, got {hex(dut.port.read_data.value)}"


@cocotb.test()
async def memory_data_test(dut):
    # INIT MEMORY
    cocotb.start_soon(Clock(dut.clk, 1, unit="ns").start())
    await reset(dut)

    dut.port.enable.value = 1
        
    # Test: Write and read back data
    test_data = [
        (0, 0xDEADBEEF),
        (4, 0xCAFEBABE),
        (8, 0x12345678),
        (12, 0xA5A5A5A5)
    ]

    # ======================
    # BASIC WORD WRITE TEST
    # ======================
    for address, data in test_data:
        dut.port.address.value = address
        dut.port.write_data.value = data

        # write
        # For the first tests, we deal with word operations
        dut.port.byte_write_enable.value = 0b1111
        await RisingEdge(dut.clk)
        dut.port.byte_write_enable.value = 0
        await RisingEdge(dut.clk)

        # Verify by reading back
        await RisingEdge(dut.clk)
        assert_read(dut, address, data)

    # ==============
    # WRITE TEST #2
    # ==============
    for i in range(0,40,4):
        dut.port.address.value = i
        dut.port.write_data.value = i
        dut.port.byte_write_enable.value = 0b1111
        await RisingEdge(dut.clk)
        # Check that setting write_data doesn't affect RAM state
        dut.port.write_data.value = 0xFAFABEBE
        dut.port.byte_write_enable.value = 0
        await RisingEdge(dut.clk)

        # Verify by reading back
        await RisingEdge(dut.clk)
        assert dut.port.read_data.value == i

        # Read back a second time for fun
        await RisingEdge(dut.clk)
        assert_read(dut, i, i)

    # ==============
    # NO WRITE TEST
    # ==============
    dut.port.byte_write_enable.value = 0
    for i in range(0,40,4):
        dut.port.address.value = i
        # Check that setting write_data doesn't affect RAM state
        dut.port.write_data.value = 0xBEBECACA
        await RisingEdge(dut.clk)

        # Verify by reading back
        await RisingEdge(dut.clk)
        assert_read(dut, i, i)

    # ===============
    # BYTE WRITE TEST
    # ===============
    for byte_enable in range(16):
        await reset(dut) # we reset memory..
        dut.port.enable.value = 1
        
        # generate mask from byte_enable
        mask = 0
        for j in range(4):
            if (byte_enable >> j) & 1:
                mask |= (0xFF << (j * 8))

        print(f"mask: {mask}")

        for address, data in test_data:
            dut.port.byte_write_enable.value = byte_enable
            dut.port.address.value = address
            dut.port.write_data.value = data

            # write
            await RisingEdge(dut.clk)
            dut.port.byte_write_enable.value = 0
            await RisingEdge(dut.clk)

            # Verify by reading back
            await RisingEdge(dut.clk)

            # Check that we're only touching the concerned bytes
            assert dut.port.read_data.value.to_unsigned() & mask == data & mask
            assert dut.port.read_data.value.to_unsigned() & ~mask == dut.ram.mem.value[int(address/4)].to_unsigned() & ~mask
