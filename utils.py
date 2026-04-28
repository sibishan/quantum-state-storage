from qiskit import QuantumCircuit

def cut_circuit(qc, idx):
    """Split a circuit into 2 at the barrier at position index (0 indexed)"""
    qc1 = QuantumCircuit(*qc.qregs, *qc.cregs)
    qc2 = QuantumCircuit(*qc.qregs, *qc.cregs)

    barrier_count = 0
    target = qc1

    for i, instr in enumerate(qc.data):
        print(i, instr.operation.name)

    for instr in qc.data:
        if instr.operation.name == "barrier":
            if barrier_count == idx:
                target = qc2
                barrier_count += 1
                continue
            barrier_count += 1
        target.append(instr.operation, instr.qubits, instr.clbits)
    
    if target is qc1:
        raise ValueError(f"QuantumCircuit has fewer than {idx +1} barriers")
    
    print(len(qc1.data), len(qc2.data))
    
    return qc1, qc2