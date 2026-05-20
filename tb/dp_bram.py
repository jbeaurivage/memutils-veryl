import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

def assert_read_port(port, address, expected):
    assert port.read_data.value == expected, \
        f"Error at {port} address {address}: expected {hex(expected)}, got {hex(port.read_data.value)}"

async def reset(dut):
    dut.rst.value = 0
    dut.ram.mem.value = [0] * len(dut.ram.mem.value)
    await RisingEdge(dut.clk)
    for port in ['port_a', 'port_b']:
        getattr(dut, port).enable.value = 0
        getattr(dut, port).byte_write_enable.value = 0
        getattr(dut, port).address.value = 0
        getattr(dut, port).write_data.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    print("reset done !")

@cocotb.test()
async def memory_data_test(dut):
    cocotb.start_soon(Clock(dut.clk, 1, unit="ns").start())
    await reset(dut)

    dut.port_a.enable.value = 1
    dut.port_b.enable.value = 1

    test_data = [
        (0, 0xDEADBEEF),
        (4, 0xCAFEBABE),
        (8, 0x12345678),
        (12, 0xA5A5A5A5)
    ]

    # BASIC WORD WRITE TEST: port_a writes, port_b reads
    for address, data in test_data:
        dut.port_a.address.value = address
        dut.port_b.address.value = address

        dut.port_a.write_data.value = data
        dut.port_a.byte_write_enable.value = 0b1111
        await RisingEdge(dut.clk)
        dut.port_a.byte_write_enable.value = 0
        await RisingEdge(dut.clk)
        
        await RisingEdge(dut.clk)
        # port_b reads
        assert_read_port(dut.port_b, address, data)

    # WRITE TEST #2: port_b writes, port_a reads
    for i in range(0, 40, 4):
        dut.port_b.address.value = i
        dut.port_a.address.value = i

        dut.port_b.write_data.value = i
        dut.port_b.byte_write_enable.value = 0b1111
        await RisingEdge(dut.clk)
        dut.port_b.write_data.value = 0xFAFABEBE
        dut.port_b.byte_write_enable.value = 0
        await RisingEdge(dut.clk)

        await RisingEdge(dut.clk)

        # port_a reads
        assert_read_port(dut.port_a, i, i)

        await RisingEdge(dut.clk)

        # Check that both ports read the same data
        assert_read_port(dut.port_a, i, i)
        assert_read_port(dut.port_b, i, i)

    # NO WRITE TEST: port_a reads, port_b sets write_data but no write
    dut.port_b.byte_write_enable.value = 0
    for i in range(0, 40, 4):
        dut.port_a.address.value = i
        dut.port_b.write_data.value = 0xBEBECACA
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        assert_read_port(dut.port_a, i, i)

    # BYTE WRITE TEST: port_a writes with byte enables, port_b reads
    for byte_enable in range(16):
        await reset(dut)
        dut.port_a.enable.value = 1
        dut.port_b.enable.value = 1
        mask = 0
        for j in range(4):
            if (byte_enable >> j) & 1:
                mask |= (0xFF << (j * 8))
        print(f"mask: {mask}")
        for address, data in test_data:
            dut.port_a.address.value = address
            dut.port_b.address.value = address

            dut.port_a.byte_write_enable.value = byte_enable
            dut.port_a.write_data.value = data

            await RisingEdge(dut.clk)
            dut.port_a.byte_write_enable.value = 0

            await RisingEdge(dut.clk)
            await RisingEdge(dut.clk)
            
            read_val = dut.port_b.read_data.value
            mem_val = dut.ram.mem.value[int(address/4)]
            assert (read_val & mask) == (data & mask)
            assert (read_val & ~mask) == (mem_val & ~mask)

    # SIMULTANEOUS WRITE TEST: what happens if both ports
    # write to 2 different memory locations at the same time?
    dut.port_a.address.value = 0
    dut.port_a.byte_write_enable.value = 0b1111
    dut.port_a.write_data.value = 0xB1AB2

    dut.port_b.address.value = 1
    dut.port_b.byte_write_enable.value = 0b1111
    dut.port_b.write_data.value = 0x7777

    await RisingEdge(dut.clk)

    dut.port_a.byte_write_enable.value = 0
    dut.port_b.byte_write_enable.value = 0

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    assert dut.port_a.read_data.value == 0xB1AB2
    assert dut.port_b.read_data.value == 0x7777